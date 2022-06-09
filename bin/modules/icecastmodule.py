import threading
import multiprocessing
import logging

from bin.songclass import SongObject
from traktor_nowplaying import Listener

def updateSong(data):
    # !!! callback currently only gets called when traktor broadcasting starts
    try:
        logging.debug("icecastmodule.updateSong() called with data")
        logging.debug(data)
        info = dict(data)

        if 'artist' in info or 'title' in info:
            logging.debug("icecastmodule.updateSong() has artist or title")
            run.currentSong.Artist = ""
            run.currentSong.Title = ""

            if 'artist' in info:
                run.currentSong.Artist = info.get('artist', '')
            if 'title' in info:
                run.currentSong.Title = info.get('title', '')
    except Exception as e:
        logging.error(e, exc_info=True)

    return



def run(maxtandalength, lastlplaylist):
    try:
        if not run.icecastListener:
            run.icecastListener = Listener(port=8000, quiet=True, custom_callback=updateSong)
            # default port 8000

        # on first run
        if not run.icecastThread:
            run.icecastThread = threading.Thread(target=run.icecastListener.start)
            run.icecastThread.start()
            logging.debug("icecastodule: start listener on port 8000")
            # listener running in own thread
    except Exception as e:
        logging.error(e, exc_info=True)
        # if run.icecastListener:
        #    run.icecastThread.destroy()
        if run.icecastThread:
            run.icecastThread.terminate()

    # ???  thread save access?
    playback_status = 'Playing'
    playlist = [run.currentSong]
    return playlist, playback_status


run.icecastListener = None
run.icecastThread = None
run.currentSong = SongObject()



