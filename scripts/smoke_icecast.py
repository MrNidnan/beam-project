#!/usr/bin/env python

import sys
import types
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


CREATED_LISTENERS = []


class FakeListener:
    def __init__(self, port=8000, quiet=True, custom_callback=None):
        self.port = port
        self.quiet = quiet
        self.custom_callback = custom_callback
        self.started = False
        CREATED_LISTENERS.append(self)

    def start(self):
        # Listener normally blocks serving the socket; the smoke stub returns
        # immediately so the worker thread finishes without binding a port.
        self.started = True


def install_traktor_nowplaying_stub():
    traktor_module = types.ModuleType("traktor_nowplaying")
    traktor_module.Listener = FakeListener
    sys.modules["traktor_nowplaying"] = traktor_module


def test_apply_metadata_to_song():
    from bin.modules import icecastmodule
    from bin.songclass import SongObject

    # artist + title populate the song
    song = icecastmodule.apply_metadata_to_song(SongObject(), {'artist': 'Anibal Troilo', 'title': 'Sur'})
    assert song.Artist == 'Anibal Troilo', song.Artist
    assert song.Title == 'Sur', song.Title

    # a fresh broadcast clears stale fields before repopulating
    song = icecastmodule.apply_metadata_to_song(song, {'title': 'Cafe Dominguez'})
    assert song.Artist == '', song.Artist
    assert song.Title == 'Cafe Dominguez', song.Title

    # metadata without artist/title leaves the song untouched
    song.Artist = 'Osvaldo Pugliese'
    song.Title = 'La Yumba'
    song = icecastmodule.apply_metadata_to_song(song, {'bitrate': 320})
    assert song.Artist == 'Osvaldo Pugliese', song.Artist
    assert song.Title == 'La Yumba', song.Title


def test_update_song_callback_uses_global():
    from bin.modules import icecastmodule
    from bin.songclass import SongObject

    icecastmodule.run.currentSong = SongObject()
    icecastmodule.updateSong({'artist': 'Carlos Di Sarli', 'title': 'Bahia Blanca'})
    assert icecastmodule.run.currentSong.Artist == 'Carlos Di Sarli'
    assert icecastmodule.run.currentSong.Title == 'Bahia Blanca'


def test_run_wires_port_and_starts_listener():
    from bin.modules import icecastmodule

    # reset module-level listener state for a deterministic run
    CREATED_LISTENERS.clear()
    icecastmodule.run.icecastListener = None
    icecastmodule.run.icecastThread = None
    icecastmodule.run.icecastPort = None

    playlist, status = icecastmodule.run(4, [], port=9123)

    assert status == 'Playing', status
    assert len(playlist) == 1
    assert len(CREATED_LISTENERS) == 1, CREATED_LISTENERS
    assert CREATED_LISTENERS[0].port == 9123, CREATED_LISTENERS[0].port
    assert CREATED_LISTENERS[0].custom_callback is icecastmodule.updateSong

    if icecastmodule.run.icecastThread is not None:
        icecastmodule.run.icecastThread.join(timeout=2)

    # a second run with the same port reuses the listener (no new instance)
    icecastmodule.run(4, [], port=9123)
    assert len(CREATED_LISTENERS) == 1, CREATED_LISTENERS


def main():
    install_traktor_nowplaying_stub()

    test_apply_metadata_to_song()
    test_update_song_callback_uses_global()
    test_run_wires_port_and_starts_listener()

    print('Icecast smoke test passed')


if __name__ == '__main__':
    main()
