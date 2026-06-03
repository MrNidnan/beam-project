#!/usr/bin/env python

import socket
import socketserver
import sys
import types
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


CAPTURED_CALLBACKS = []


class _NoopHandler(socketserver.BaseRequestHandler):
    def handle(self):
        # Smoke test never connects a client; the handler just needs to exist so
        # the TCPServer can bind and serve.
        pass


def fake_create_request_handler(callbacks):
    CAPTURED_CALLBACKS.append(callbacks)
    return _NoopHandler


def install_traktor_nowplaying_stub():
    traktor_module = types.ModuleType("traktor_nowplaying")
    core_module = types.ModuleType("traktor_nowplaying.core")
    core_module.create_request_handler = fake_create_request_handler
    traktor_module.core = core_module
    sys.modules["traktor_nowplaying"] = traktor_module
    sys.modules["traktor_nowplaying.core"] = core_module


def _free_port():
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    probe.bind(('127.0.0.1', 0))
    port = probe.getsockname()[1]
    probe.close()
    return port


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


def test_run_starts_hot_restarts_and_reuses():
    from bin.modules import icecastmodule

    # deterministic starting state
    icecastmodule._stop_listener()
    CAPTURED_CALLBACKS.clear()

    port_one = _free_port()
    playlist, status = icecastmodule.run(4, [], port=port_one)

    assert status == 'Playing', status
    assert len(playlist) == 1
    assert icecastmodule.run.icecastServer is not None
    assert icecastmodule.run.icecastPort == port_one, icecastmodule.run.icecastPort
    assert icecastmodule.run.icecastThread.is_alive()
    # the handler factory received our updateSong callback
    assert CAPTURED_CALLBACKS[-1] == [icecastmodule.updateSong], CAPTURED_CALLBACKS
    first_server = icecastmodule.run.icecastServer

    # changing the port hot-restarts: old server closed, new one on the new port
    port_two = _free_port()
    while port_two == port_one:
        port_two = _free_port()
    icecastmodule.run(4, [], port=port_two)

    assert icecastmodule.run.icecastServer is not first_server
    assert icecastmodule.run.icecastPort == port_two, icecastmodule.run.icecastPort
    assert first_server.socket.fileno() == -1, 'old server socket should be closed'
    second_server = icecastmodule.run.icecastServer

    # same port again reuses the running server (no restart)
    icecastmodule.run(4, [], port=port_two)
    assert icecastmodule.run.icecastServer is second_server

    icecastmodule._stop_listener()
    assert icecastmodule.run.icecastServer is None
    assert icecastmodule.run.icecastPort is None


def main():
    install_traktor_nowplaying_stub()

    test_apply_metadata_to_song()
    test_update_song_callback_uses_global()
    test_run_starts_hot_restarts_and_reuses()

    print('Icecast smoke test passed')


if __name__ == '__main__':
    main()
