#!/usr/bin/env python

# Smoke test for the Linux MPRIS "Now Playing" backend (bin.modules.lin.mprismodule).
# Mirrors smoke_smtc.py: stubs the D-Bus binding so the module's logic is testable
# off a real session bus. Forces the synchronous dbus-python path (the always-present
# fallback) for the integration tests; the pure helpers are backend-independent.

import os
import sys
import tempfile
import types
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# --- fake dbus-python ---------------------------------------------------------

# Per-test state: the bus names published and a {bus_name: FakePlayer} map.
_STATE = {'names': [], 'players': {}}


class FakePlayer:
    def __init__(self, status, metadata=None):
        self.status = status
        self.metadata = metadata or {}


class FakeSessionBus:
    def list_names(self):
        return list(_STATE['names'])

    def get_object(self, bus_name, object_path):
        return _STATE['players'][bus_name]


class FakeInterface:
    def __init__(self, obj, iface):
        self._obj = obj

    def Get(self, iface, prop, timeout=None):
        if prop == 'PlaybackStatus':
            return self._obj.status
        if prop == 'Metadata':
            return self._obj.metadata
        raise KeyError(prop)


def install_dbus_stub():
    dbus_module = types.ModuleType("dbus")
    dbus_module.SessionBus = FakeSessionBus
    dbus_module.Interface = FakeInterface
    sys.modules["dbus"] = dbus_module


def set_players(players, names=None):
    # players: dict bus_name -> FakePlayer. names defaults to the players' keys
    # plus a couple of non-MPRIS names to prove filtering.
    _STATE['players'] = players
    _STATE['names'] = (names if names is not None else list(players)) + [
        'org.freedesktop.DBus', 'org.gnome.Shell',
    ]


def _mpris(name):
    return 'org.mpris.MediaPlayer2.' + name


# --- tests --------------------------------------------------------------------

def test_status_mapping():
    from bin.modules.lin import mprismodule
    assert mprismodule._status_to_beam('Playing') == 'Playing'
    assert mprismodule._status_to_beam('Paused') == 'Paused'
    assert mprismodule._status_to_beam('Stopped') == 'PlayerNotRunning'
    assert mprismodule._status_to_beam('') == 'PlayerNotRunning'
    assert mprismodule._status_to_beam(None) == 'PlayerNotRunning'


def test_friendly_name():
    from bin.modules.lin import mprismodule
    assert mprismodule.aumid_friendly_name(_mpris('spotify')) == 'Spotify'
    assert mprismodule.aumid_friendly_name(_mpris('chromium.instance1234')) == 'Chromium'
    assert mprismodule.aumid_friendly_name(_mpris('firefox.instance99')) == 'Firefox'
    assert mprismodule.aumid_friendly_name('') == ''
    # unknown -> raw bus name preserved
    assert mprismodule.aumid_friendly_name(_mpris('some.unknown')) == _mpris('some.unknown')


def test_metadata_to_song():
    from bin.modules.lin import mprismodule
    # values like dbus-python returns: arrays for artist/genre, plain strings else
    song = mprismodule._metadata_to_song({
        'xesam:title': 'Sur',
        'xesam:artist': ['Anibal Troilo', 'Edmundo Rivero'],
        'xesam:album': 'Suburbio',
        'xesam:albumArtist': ['Troilo Orquesta'],
        'xesam:genre': ['Tango'],
    })
    assert song.Title == 'Sur'
    assert song.Artist == 'Anibal Troilo'      # first of the array
    assert song.Album == 'Suburbio'
    assert song.AlbumArtist == 'Troilo Orquesta'
    assert song.Genre == 'Tango'

    # missing/empty fields stay blank, no crash
    song = mprismodule._metadata_to_song({'xesam:title': 'X', 'xesam:artist': []})
    assert song.Title == 'X'
    assert song.Artist == ''
    assert song.Genre == ''


def test_image_extension():
    from bin.modules.lin import mprismodule
    assert mprismodule._image_extension(b'\xff\xd8\xff\xe0rest') == '.jpg'
    assert mprismodule._image_extension(b'\x89PNG\r\n\x1a\nrest') == '.png'
    assert mprismodule._image_extension(b'BMrest') == '.bmp'
    assert mprismodule._image_extension(b'GIF89arest') == '.gif'
    assert mprismodule._image_extension(b'not an image') == ''


def test_pick_name():
    from bin.modules.lin import mprismodule
    names = [_mpris('vlc'), _mpris('spotify')]
    status = {_mpris('vlc'): 'Paused', _mpris('spotify'): 'Playing'}

    def status_of(name):
        return status[name]

    # preferred present -> preferred
    assert mprismodule._pick_name(names, _mpris('vlc'), status_of) == _mpris('vlc')
    # preferred absent -> first Playing
    assert mprismodule._pick_name(names, _mpris('nope'), status_of) == _mpris('spotify')
    # none playing -> first published
    assert mprismodule._pick_name(names, '', lambda n: 'Paused') == names[0]
    # nothing published -> None
    assert mprismodule._pick_name([], '', status_of) is None


def test_resolve_art_file_uri():
    from bin.modules.lin import mprismodule
    fd, path = tempfile.mkstemp(suffix='.png')
    os.write(fd, b'\x89PNG\r\n\x1a\nfake')
    os.close(fd)
    try:
        # file:// URI -> the local path is returned directly (no copy)
        uri = Path(path).as_uri()
        assert mprismodule._resolve_art(uri, 'key') == path
        # empty / unsupported -> ''
        assert mprismodule._resolve_art('', 'key') == ''
        assert mprismodule._resolve_art('file:///does/not/exist.png', 'key') == ''
    finally:
        os.remove(path)


def _force_dbus_python(mprismodule):
    # Drive the synchronous dbus-python path deterministically regardless of
    # whether dbus-next happens to be installed in the CI image.
    mprismodule._HAS_DBUS_NEXT = False
    mprismodule._HAS_DBUS_PYTHON = True


def test_run_with_details_playing():
    from bin.modules.lin import mprismodule
    _force_dbus_python(mprismodule)

    set_players({
        _mpris('spotify'): FakePlayer('Playing', {
            'xesam:title': 'La Yumba',
            'xesam:artist': ['Osvaldo Pugliese'],
            'xesam:album': 'Ausencia',
        }),
    })
    playlist, status, details = mprismodule.run_with_details(4, _mpris('spotify'))
    assert status == 'Playing', status
    assert details['route'].startswith('mpris'), details['route']
    assert details['appName'] == 'Spotify'
    assert details['sessionCount'] == 1
    assert len(playlist) == 1
    assert playlist[0].Title == 'La Yumba'
    assert playlist[0].Artist == 'Osvaldo Pugliese'


def test_run_with_details_paused_returns_empty_playlist():
    from bin.modules.lin import mprismodule
    _force_dbus_python(mprismodule)

    set_players({_mpris('vlc'): FakePlayer('Paused', {'xesam:title': 'X'})})
    playlist, status, details = mprismodule.run_with_details(4, '')
    assert status == 'Paused', status
    assert playlist == []
    assert details['appName'] == 'VLC'


def test_list_sessions():
    from bin.modules.lin import mprismodule
    _force_dbus_python(mprismodule)

    set_players({
        _mpris('spotify'): FakePlayer('Playing'),
        _mpris('vlc'): FakePlayer('Paused'),
    })
    sessions = mprismodule.list_sessions()
    # non-MPRIS names filtered out; friendly names resolved
    assert sessions == [
        {'aumid': _mpris('spotify'), 'name': 'Spotify', 'status': 'Playing'},
        {'aumid': _mpris('vlc'), 'name': 'VLC', 'status': 'Paused'},
    ], sessions


def main():
    install_dbus_stub()

    test_status_mapping()
    test_friendly_name()
    test_metadata_to_song()
    test_image_extension()
    test_pick_name()
    test_resolve_art_file_uri()
    test_run_with_details_playing()
    test_run_with_details_paused_returns_empty_playlist()
    test_list_sessions()

    print('MPRIS smoke test passed')


if __name__ == '__main__':
    main()
