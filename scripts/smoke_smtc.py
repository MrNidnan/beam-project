#!/usr/bin/env python

import sys
import types
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# --- winsdk stub --------------------------------------------------------------

class FakeProps:
    def __init__(self, title='', artist='', album_title='', album_artist='', genres=None):
        self.title = title
        self.artist = artist
        self.album_title = album_title
        self.album_artist = album_artist
        self.genres = genres or []


class FakeSession:
    def __init__(self, aumid, status, props=None):
        self.source_app_user_model_id = aumid
        self._status = status
        self._props = props or FakeProps()

    def get_playback_info(self):
        return SimpleNamespace(playback_status=self._status)

    async def try_get_media_properties_async(self):
        return self._props


class FakeManager:
    def __init__(self, sessions, current):
        self._sessions = sessions
        self._current = current

    def get_sessions(self):
        return self._sessions

    def get_current_session(self):
        return self._current


class FakeSessionManager:
    instance = None

    @staticmethod
    async def request_async():
        return FakeSessionManager.instance


class FakePlaybackStatus:
    CLOSED = 0
    OPENED = 1
    CHANGING = 2
    STOPPED = 3
    PLAYING = 4
    PAUSED = 5


def install_winrt_stub():
    # Stub under the `winrt` namespace - the module's preferred import root.
    winrt_module = types.ModuleType("winrt")
    windows_module = types.ModuleType("winrt.windows")
    media_module = types.ModuleType("winrt.windows.media")
    control_module = types.ModuleType("winrt.windows.media.control")
    control_module.GlobalSystemMediaTransportControlsSessionManager = FakeSessionManager
    control_module.GlobalSystemMediaTransportControlsSessionPlaybackStatus = FakePlaybackStatus
    media_module.control = control_module
    windows_module.media = media_module
    winrt_module.windows = windows_module
    sys.modules["winrt"] = winrt_module
    sys.modules["winrt.windows"] = windows_module
    sys.modules["winrt.windows.media"] = media_module
    sys.modules["winrt.windows.media.control"] = control_module


# --- tests --------------------------------------------------------------------

def test_status_mapping():
    from bin.modules.win import smtcmodule

    assert smtcmodule._status_to_beam(4) == 'Playing'
    assert smtcmodule._status_to_beam(5) == 'Paused'
    assert smtcmodule._status_to_beam(2) == 'Paused'      # CHANGING
    assert smtcmodule._status_to_beam(3) == 'PlayerNotRunning'   # STOPPED
    assert smtcmodule._status_to_beam(0) == 'PlayerNotRunning'   # CLOSED
    assert smtcmodule._status_to_beam(None) == 'PlayerNotRunning'
    # enum-like with .value
    assert smtcmodule._status_to_beam(SimpleNamespace(value=4)) == 'Playing'


def test_friendly_name():
    from bin.modules.win import smtcmodule

    assert smtcmodule.aumid_friendly_name('Spotify.exe') == 'Spotify'
    assert smtcmodule.aumid_friendly_name('SpotifyAB.SpotifyMusic_zpdnekdrzrea0!Spotify') == 'Spotify (Store)'
    assert smtcmodule.aumid_friendly_name('AmazonMobileLLC.AmazonMusic_xxxx!App') == 'Amazon Music'
    assert smtcmodule.aumid_friendly_name('') == ''
    # unknown -> raw aumid preserved
    assert smtcmodule.aumid_friendly_name('Some.Unknown.App') == 'Some.Unknown.App'


def test_props_to_song():
    from bin.modules.win import smtcmodule

    song = smtcmodule._props_to_song(FakeProps(
        title='Sur', artist='Anibal Troilo', album_title='Suburbio',
        album_artist='Troilo Orquesta', genres=['Tango'],
    ))
    assert song.Title == 'Sur'
    assert song.Artist == 'Anibal Troilo'
    assert song.Album == 'Suburbio'
    assert song.AlbumArtist == 'Troilo Orquesta'
    assert song.Genre == 'Tango'

    # empty genres list leaves Genre blank, no crash
    song = smtcmodule._props_to_song(FakeProps(title='X', genres=[]))
    assert song.Genre == ''


def test_pick_session_prefers_then_falls_back():
    from bin.modules.win import smtcmodule

    spotify = FakeSession('Spotify.exe', FakePlaybackStatus.PLAYING)
    amazon = FakeSession('AmazonMusic', FakePlaybackStatus.PAUSED)
    manager = FakeManager([spotify, amazon], current=amazon)

    # preferred AUMID present -> that session
    assert smtcmodule._pick_session(manager, 'Spotify.exe') is spotify
    # preferred AUMID absent -> current session
    assert smtcmodule._pick_session(manager, 'Nope.exe') is amazon
    # no preference -> current session
    assert smtcmodule._pick_session(manager, '') is amazon
    # no manager -> None
    assert smtcmodule._pick_session(None, '') is None


def test_run_with_details_playing():
    from bin.modules.win import smtcmodule

    playing = FakeSession(
        'Spotify.exe', FakePlaybackStatus.PLAYING,
        FakeProps(title='La Yumba', artist='Osvaldo Pugliese', album_title='Ausencia', album_artist='Pugliese'),
    )
    FakeSessionManager.instance = FakeManager([playing], current=playing)

    playlist, status, details = smtcmodule.run_with_details(4, 'Spotify.exe')
    assert status == 'Playing', status
    assert details['route'] == 'smtc'
    assert details['appName'] == 'Spotify'
    assert details['sessionCount'] == 1
    assert len(playlist) == 1
    assert playlist[0].Title == 'La Yumba'
    assert playlist[0].Artist == 'Osvaldo Pugliese'
    assert playlist[0].AlbumArtist == 'Pugliese'


def test_run_with_details_paused_returns_empty_playlist():
    from bin.modules.win import smtcmodule

    paused = FakeSession('AmazonMusic', FakePlaybackStatus.PAUSED)
    FakeSessionManager.instance = FakeManager([paused], current=paused)

    playlist, status, details = smtcmodule.run_with_details(4, '')
    assert status == 'Paused', status
    assert playlist == []
    assert details['appName'] == 'Amazon Music'


def test_list_sessions():
    from bin.modules.win import smtcmodule

    spotify = FakeSession('Spotify.exe', FakePlaybackStatus.PLAYING)
    amazon = FakeSession('AmazonMusic', FakePlaybackStatus.PAUSED)
    FakeSessionManager.instance = FakeManager([spotify, amazon], current=spotify)

    sessions = smtcmodule.list_sessions()
    assert sessions == [
        {'aumid': 'Spotify.exe', 'name': 'Spotify', 'status': 'Playing'},
        {'aumid': 'AmazonMusic', 'name': 'Amazon Music', 'status': 'Paused'},
    ], sessions


def main():
    install_winrt_stub()

    test_status_mapping()
    test_friendly_name()
    test_props_to_song()
    test_pick_session_prefers_then_falls_back()
    test_run_with_details_playing()
    test_run_with_details_paused_returns_empty_playlist()
    test_list_sessions()

    print('SMTC smoke test passed')


if __name__ == '__main__':
    main()
