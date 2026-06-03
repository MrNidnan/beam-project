import threading
import logging
import socketserver

from bin.songclass import SongObject

# traktor_nowplaying (and its bundled bottle.py) can fail to import - e.g. on
# Python 3.13+ where the stdlib `cgi` module it depends on was removed (PEP 594,
# mitigated by the legacy-cgi backport in requirements.txt), or if the optional
# dependency is simply not installed. Catch it here so the import succeeds and
# gets cached: nowplayingdata re-imports this module every read cycle, and an
# uncaught failure would re-raise and spam the log each time.
#
# We use traktor_nowplaying's request-handler factory directly (instead of its
# Listener class) so Beam owns the TCPServer and can shut it down to rebind on a
# new port - Listener.start() hides its server in a local variable with no stop
# hook, which made port changes require an app restart.
try:
    from traktor_nowplaying.core import create_request_handler
    _LISTENER_IMPORT_ERROR = None
except Exception as _import_error:  # noqa: BLE001 - report any import-time failure
    create_request_handler = None
    _LISTENER_IMPORT_ERROR = _import_error


class _ReusableTCPServer(socketserver.TCPServer):
    # Allow immediate rebinding of the same port after a shutdown so a port
    # change (or restart on the same port) does not hit TIME_WAIT errors.
    allow_reuse_address = True


def apply_metadata_to_song(song, data):
    # Pure helper: map an Icecast/Traktor metadata dict onto a SongObject and
    # return it. Kept free of module globals so it can be unit tested directly.
    info = dict(data)

    if 'artist' in info or 'title' in info:
        # A broadcast started/changed; clear stale fields before repopulating.
        song.Artist = ""
        song.Title = ""

        if 'artist' in info:
            song.Artist = info.get('artist', '')
        if 'title' in info:
            song.Title = info.get('title', '')

    return song


def updateSong(data):
    # !!! callback currently only gets called when traktor broadcasting starts
    try:
        logging.debug("icecastmodule.updateSong() called with data")
        logging.debug(data)
        apply_metadata_to_song(run.currentSong, data)
    except Exception as e:
        logging.error(e, exc_info=True)

    return


def _start_listener(port):
    handler = create_request_handler(callbacks=[updateSong])
    server = _ReusableTCPServer(('', port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    run.icecastServer = server
    run.icecastThread = thread
    run.icecastPort = port
    logging.debug("icecastmodule: listening on port %s", port)


def _stop_listener():
    if run.icecastServer is not None:
        try:
            # shutdown() must be called from another thread than serve_forever;
            # run() executes on Beam's read thread, so this is safe.
            run.icecastServer.shutdown()
            run.icecastServer.server_close()
        except Exception as e:
            logging.error(e, exc_info=True)

    if run.icecastThread is not None:
        run.icecastThread.join(timeout=5)

    run.icecastServer = None
    run.icecastThread = None
    run.icecastPort = None


def run(maxtandalength, lastlplaylist, port=8000):
    if create_request_handler is None:
        # Dependency unavailable; log once instead of every read cycle.
        if not run.importErrorLogged:
            logging.error(
                "icecastmodule: traktor_nowplaying unavailable, Icecast disabled: %s",
                _LISTENER_IMPORT_ERROR,
            )
            run.importErrorLogged = True
        return [run.currentSong], 'Stopped'

    try:
        if run.icecastServer is None:
            _start_listener(port)
        elif run.icecastPort != port:
            logging.info(
                "icecastmodule: port changed %s -> %s, restarting listener",
                run.icecastPort,
                port,
            )
            _stop_listener()
            _start_listener(port)
    except Exception as e:
        logging.error(e, exc_info=True)
        # Leave a clean slate so the next run() can retry binding.
        _stop_listener()

    playback_status = 'Playing'
    playlist = [run.currentSong]
    return playlist, playback_status


run.icecastServer = None
run.icecastThread = None
run.icecastPort = None
run.importErrorLogged = False
run.currentSong = SongObject()
