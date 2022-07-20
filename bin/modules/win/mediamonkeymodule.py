# -*- encoding: utf-8 -*-
#    Copyright (C) 2014 Mikael Holber http://www.beam-project.com
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
import logging

from bin.songclass import SongObject

try:
    import pythoncom
    import win32com.client
except ImportError:
	pass
from copy import deepcopy
from bin.modules.win.winutils import applicationrunning

###############################################################
#
# Define operations
#
###############################################################

def run(MaxTandaLength, LastPlaylist):

    playlist = []
    
    #
    # Player Status
    #
    if not applicationrunning("MediaMonkey.exe"):
        playbackStatus = 'PlayerNotRunning'
        return playlist, playbackStatus

    pythoncom.CoInitialize()
    try:
        try:
            # First check for MM5
            MediaMonkey = win32com.client.Dispatch("SongsDB5.SDBApplication")
            # Tries to start MM5 when MM5 is not running!
            # raise
        except:
            # then check for MM4
            MediaMonkey = win32com.client.Dispatch("SongsDB.SDBApplication")

        #
        # Playback Status
        #
        if not MediaMonkey.Player.isPlaying:
            playbackStatus = 'Stopped'
            return playlist, playbackStatus
        elif MediaMonkey.Player.isPaused and MediaMonkey.Player.isPlaying:
            playbackStatus = 'Paused'
            return playlist, playbackStatus
        #
        # Playback = Playing
        #
        elif MediaMonkey.Player.isPlaying and not MediaMonkey.Player.isPaused:
            playbackStatus = 'Playing'

        #Declare our position
        currentsong = MediaMonkey.Player.CurrentSongIndex
        searchsong = currentsong
        playlistlength = searchsong + MaxTandaLength+2

        if MediaMonkey.VersionHi == 4:
            #
            # Quick-read
            #
            # Does not work with MM5
            if quickRead(MediaMonkey, currentsong, MaxTandaLength, LastPlaylist):
                logging.debug("Quick-read")
                playlist = deepcopy(LastPlaylist)
            else:
                # Full-read
                #
                # MM4 works current playlist
                logging.debug("Full-read")
                while searchsong < playlistlength and searchsong < currentsong+MaxTandaLength+2:
                    try:
                        playlist.append(getSongAt(MediaMonkey, searchsong))
                    except:
                        break
                    searchsong = searchsong+1
        else:
            if MediaMonkey.VersionHi == 5:
                # MM5 works only current song
                playlist.append(getSongAt(MediaMonkey, searchsong))
            else:
                # Unknown version
                raise
    finally:
        pythoncom.CoUninitialize()

    return playlist, playbackStatus
###############################################################
#
# Quick read - Player specific
#
###############################################################

def quickRead(MediaMonkey, songPosition = 1, MaxTandaLength = 1, LastRead = []):
    Last = []
    Current = []
    for i in range(0,MaxTandaLength+2):
        try:
            # does not work for MM5:
            Track = MediaMonkey.Player.CurrentPlaylist.Item(songPosition+i)
            Current.append(Track.Path)
        except:
            pass
        try:
            Song = LastRead[i]
            # if LastRead[i] exists
            Last.append(Song.FilePath)
        except:
            pass
# !!! auch wenn beide leer
    if Last == Current:
        return True


    return False
	
###############################################################
#
# Full read - Player specific
#
###############################################################

def getSongAt(MediaMonkey, songPosition):
    retSong = SongObject()

    if MediaMonkey.Player.CurrentSongIndex == songPosition:
        # Does work with MM5
        Track = MediaMonkey.Player.CurrentSong
    else:
        # Does not work with MM5
        Track = MediaMonkey.Player.CurrentPlaylist.Item(songPosition)

    # http://www.mediamonkey.com/wiki/SDBSongData
    retSong.Artist      = Track.ArtistName
    retSong.Album       = Track.AlbumName
    retSong.Title       = Track.Title
    retSong.Genre       = Track.Genre
    retSong.Comment     = Track.Comment
    retSong.Composer    = Track.Author
    # Only 0 in Track
    # retSong.Year        = Track.Year
    #retSong._Singer     Defined by beam
    retSong.AlbumArtist = Track.AlbumArtistName
    #retSong.Performer  = (Track.Performer) # Does not exist for iTunes?
    #retSong.IsCortina   Defined by beam
    retSong.FilePath     = Track.Path
    #retSong.ModuleMessage = Not needed for iTunes
    
    return retSong

###############################################################
#
# Application running Windows-specific
#
###############################################################

# def ApplicationRunning(AppName):
    #     import subprocess
    # cmd = 'WMIC PROCESS get Caption,Commandline,Processid'
    # proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    # for line in proc.stdout:
    #     if AppName in line:
    #         proc.kill()
    #         return True
    # proc.kill()
    # return False
