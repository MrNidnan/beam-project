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
#    18/10/2014 Version 1.0
#    	- Initial release
#

from bin.songclass import SongObject
import subprocess
try:
	import win32com.client
except ImportError:
	pass

###############################################################
#
# Define operations
#
###############################################################

def run(MaxTandaLength):

    playlist = []
    
    #
    # Player Status
    #
    if ApplicationRunning("Media Center"):
        try:
            JRMC = win32com.client.Dispatch ("MediaJukebox Application")
        except:
            playbackStatus = 'PlayerNotRunning'
            return playlist, playbackStatus
    else:
        playbackStatus = 'PlayerNotRunning'
        return playlist, playbackStatus
    #
    # Playback Status
    #
    if JRMC.GetPlayback().State == 1:
        playbackStatus = 'Paused'
        return playlist, playbackStatus
    elif JRMC.GetPlayback().State == 0:
        playbackStatus = 'Stopped'
        return playlist, playbackStatus

    #
    # Playback = Playing
    #
    elif JRMC.GetPlayback().State == 2:
        playbackStatus = 'Playing'

        #Declare our position
        currentsong = CurrentPlaylist.Position
        searchsong = currentsong

    #
    # Full-read
    #
        while searchsong < playlistlength and searchsong < currentsong+MaxTandaLength+2:
            try:
                playlist.append(getSongAt(JRMC, searchsong))
            except:
                break
            searchsong = searchsong+1
        return playlist, playbackStatus

###############################################################
#
# Full read - Player specific
#
###############################################################

def getSongAt(MediaMonkey, songPosition):
    
    retSong = SongObject()
    CurrentPlaylist = JRMC.GetCurPlaylist()
    Track = CurrentPlaylist.GetFile(searchsong)

    searchsong = searchsong+1
    retSong.Artist      = Track.Artist.encode('latin-1')
    retSong.Album       = Track.Album.encode('latin-1')
    retSong.Title       = Track.Name.encode('latin-1')
    retSong.Genre       = Track.Genre.encode('latin-1')
    retSong.Comment     = Track.Comment.encode('latin-1')
    #retSong.Composer    = Track.Author.encode('latin-1')
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