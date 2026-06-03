import threading
import logging

from bin.songclass import SongObject

# traktor_nowplaying (and its bundled bottle.py) can fail to import - e.g. on
# Python 3.13+ where the stdlib `cgi` module it depends on was removed (PEP 594,
# mitigated by the legacy-cgi backport in requirements.txt), or if the optional
# dependency is simply not installed. Catch it here so the import succeeds and
# gets cached: nowplayingdata re-imports this module every read cycle, and an
# uncaught failure would re-raise and spam the log each time.
try:
    from traktor_nowplaying import Listener
    _LISTENER_IMPORT_ERROR = None
except Exception as _import_error:  # noqa: BLE001 - report any import-time failure
    Listener = None
    _LISTENER_IMPORT_ERROR = _import_error

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



def run(maxtandalength, lastlplaylist, port=8000):
    if Listener is None:
        # Dependency unavailable; warn once instead of every read cycle.
        if not run.importErrorLogged:
            logging.error(
                "icecastmodule: traktor_nowplaying unavailable, Icecast disabled: %s",
                _LISTENER_IMPORT_ERROR,
            )
            run.importErrorLogged = True
        return [run.currentSong], 'Stopped'

    try:
        if not run.icecastListener:
            run.icecastListener = Listener(port=port, quiet=True, custom_callback=updateSong)
            run.icecastPort = port

        # on first run
        if not run.icecastThread:
            run.icecastThread = threading.Thread(target=run.icecastListener.start)
            run.icecastThread.start()
            logging.debug("icecastmodule: start listener on port %s", port)
            # listener running in own thread
        elif run.icecastPort != port and run.warnedPortChange != port:
            # Port changed in settings but listener already running; the
            # traktor_nowplaying Listener exposes no stop hook, so the running
            # thread cannot be rebound to a new port without a clean shutdown.
            # Warn once per distinct new port instead of every read cycle.
            logging.warning(
                "icecastmodule: port changed to %s but listener still on %s; restart Beam to apply",
                port,
                run.icecastPort,
            )
            run.warnedPortChange = port
    except Exception as e:
        logging.error(e, exc_info=True)
        # threading.Thread cannot be force-terminated; reset state so a later
        # run() can retry starting the listener.
        run.icecastListener = None
        run.icecastThread = None

    # ???  thread save access?
    playback_status = 'Playing'
    playlist = [run.currentSong]
    return playlist, playback_status


run.icecastListener = None
run.icecastThread = None
run.icecastPort = None
run.importErrorLogged = False
run.warnedPortChange = None
run.currentSong = SongObject()



