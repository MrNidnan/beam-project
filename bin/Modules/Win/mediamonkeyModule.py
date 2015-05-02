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

from bin.songclass import SongObject
import subprocess
try:
	import win32com.client
except ImportError:
	pass
from copy import deepcopy

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
    if ApplicationRunning("MediaMonkey.exe"):
        try:
            MediaMonkey = win32com.client.Dispatch("SongsDB.SDBApplication")
        except:
            playbackStatus = 'PlayerNotRunning'
            return playlist, playbackStatus
    else:
        playbackStatus = 'PlayerNotRunning'
        return playlist, playbackStatus

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

    #
    # Quick-read
    #
    if quickRead(MediaMonkey, currentsong, MaxTandaLength, LastPlaylist):
        print "Quick-read"
        playlist = deepcopy(LastPlaylist)
        return playlist, playbackStatus
    #
    # Full-read
    #
    print "Full-read"
    while searchsong < playlistlength and searchsong < currentsong+MaxTandaLength+2:
        try:
            playlist.append(getSongAt(MediaMonkey, searchsong))
        except:
            break
        searchsong = searchsong+1
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
            Track = MediaMonkey.Player.CurrentPlaylist.Item(songPosition+i)
            Current.append(Track.Path.encode('latin-1'))
        except:
            pass
        try:
            Song = LastRead[i]
            Last.append(Song.fileUrl)
        except:
            pass
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
    Track = MediaMonkey.Player.CurrentPlaylist.Item(songPosition)

    retSong.Artist      = Track.ArtistName.encode('latin-1')
    retSong.Album       = Track.AlbumName.encode('latin-1')
    retSong.Title       = Track.Title.encode('latin-1')
    retSong.Genre       = Track.Genre.encode('latin-1')
    retSong.Comment     = Track.Comment.encode('latin-1')
    retSong.Composer    = Track.Author.encode('latin-1')
    retSong.Year        = Track.Year
    #retSong._Singer     Defined by beam
    retSong.AlbumArtist = Track.AlbumArtistName.encode('latin-1')
    #retSong.Performer  = (Track.Performer).encode('latin-1') # Does not exist for iTunes?
    #retSong.IsCortina   Defined by beam
    retSong.fileUrl     = Track.Path.encode('latin-1')
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