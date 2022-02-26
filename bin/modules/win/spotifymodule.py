# -*- encoding: utf-8 -*-
#    Copyright (C) 2014 Mikael Holber http://mywebsite.com
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#    or download it from http://www.gnu.org/licenses/gpl.txt
#
#
#    Revision History:
#
#    Version 1.0
#    	- Initial release
#

from bin.songclass import SongObject
import logging

try:
	import win32gui
except:
	pass
from bin.modules.win.winutils import applicationrunning

###############################################################
#
# Define operations
#
###############################################################

def run(MaxTandaLength):
    playlist = []
    
    # Player Status
    if applicationrunning("Spotify.exe"):
        try:
            windows = []

            spotifyWin = win32gui.FindWindow("SpotifyMainWindow", None)
            # https: // github.com / XanderMJ / spotilib / issues / 7
            # does no longer work
            track = win32gui.GetWindowText(spotifyWin)

            def find_spotify_uwp(hwnd, windows):
                text = win32gui.GetWindowText(hwnd)
                classname = win32gui.GetClassName(hwnd)
                if classname == "Chrome_WidgetWin_0" and len(text) > 0:
                    windows.append(text)

            if track:
                windows.append(track)
            else:
                win32gui.EnumWindows(find_spotify_uwp, windows)

            # If Spotify isn't running the list will be empty
            if len(windows) == 0:
                return playlist, 'PlayerNotRunning'

            # The window title is the default one when paused
            if windows[0].startswith('Spotify'):
                return playlist, 'Paused'

            # Local songs may only have a title field
            try:
                artist, track = windows[0].split(" - ", 1)
            except ValueError:
                artist = ''
                track = windows[0]

            retSong = SongObject()
            retSong.Artist = artist
            retSong.Title = track
            playlist.append(retSong)
            # !!! add to playlist
            # playlist.append(getSongAt(track, 1))

            return playlist, 'Playing'
        except Exception as e:
            logging.debug(e, exc_info=True)
            return playlist, 'PlayerNotRunning'
    else:
        return playlist, 'PlayerNotRunning'

    if track == "":
        return playlist, 'PlayerNotRunning'

    #
    # Playback
    #
    try:
        playlist.append(getSongAt(track, 1))
        playbackStatus = 'Playing'
    except:
        playbackStatus = 'Paused'

    return playlist, playbackStatus

###############################################################
#
# Full read - Player specific
#
###############################################################

def getSongAt(Track, songPosition):
    retSong = SongObject()
    trackinfo = Track.split(" - ")
    artist, title = trackinfo[1].split(" \x96 ")
    
    retSong.Artist      = artist
    #retSong.Album       = Track.AlbumName
    retSong.Title       = title
    #retSong.Genre       = Track.Genre
    #retSong.Comment     = Track.Comment
    #retSong.Composer    = Track.Author
    #retSong.Year        = Track.Year
    #retSong._Singer     Defined by beam
    #retSong.AlbumArtist = Track.AlbumArtistName
    #retSong.Performer  = (Track.Performer) # Does not exist for iTunes?
    #retSong.IsCortina   Defined by beam
    #retSong.fileUrl     = Track.Path
    #retSong.ModuleMessage = Not needed for iTunes
    
    return retSong

###############################################################
#
# Application running Windows-specific
#
###############################################################

def ApplicationRunning(AppName):
    import subprocess
    cmd = 'WMIC PROCESS get Caption,Commandline,Processid'
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    for line in proc.stdout:
        if AppName in line:
            proc.kill()
            return True
    proc.kill()
    return False
