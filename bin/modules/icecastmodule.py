import threading

from bin.songclass import SongObject
from traktor_nowplaying import Listener

def updateSong(data):
    info = dict(data)

    if 'artist' in info or 'title' in info:
        run.currentSong.Artist = ""
        run.currentSong.Title = ""

        if 'artist' in info:
            run.currentSong.Artist = info.get('artist', '')
        if 'title' in info:
            run.currentSong.Title = info.get('title', '')
    return



def run(maxtandalength, lastlplaylist):
    if not run.icecastListener:
        run.icecastListener = Listener(custom_callback=updateSong)

    if not run.icecastThread:
        run.icecastThread = threading.Thread(target=run.icecastListener.start)
        run.icecastThread.start()

    playback_status = 'Playing'
    playlist = [run.currentSong]
    return playlist, playback_status


run.icecastListener = None
run.icecastThread = None
run.currentSong = SongObject()



