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
import Winamp

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
    try:
        winamp = Winamp.Winamp()
    except:
        playbackStatus = 'PlayerNotRunning'
        return playlist, playbackStatus

    #
    # Playback = Playing
    #
    if winamp.getPlaybackStatus() == 1:
        playbackStatus = 'Playing'

        #Declare our position
        currentsong	= winamp.getListPosition()
        listlength = winamp.getListLength()
        searchsong = currentsong
            
        #
        # Read from file
        #
        while searchsong < currentsong+MaxTandaLength+2 and searchsong < listlength:
            playlist.append(getSongFromUrl(winamp, searchsong))
            searchsong = searchsong+1
                            
        return playlist, playbackStatus

    #
    # Playback = Paused
    #
    else:
        playbackStatus = 'Stopped'
        return playlist, playbackStatus

###############################################################
#
# Full read from file - Player specific
#
###############################################################

def getSongFromUrl(winamp, songPosition = 1):
    retSong = SongObject()
    
    try:
        retSong.fileUrl = winamp.getPlaylistFile(songPosition)
    except:
        retSong.ModuleMessage = "Error from Winamp"
        return retSong
    
    try:
        retSong.buildFromUrl(retSong.fileUrl)
    except:
        retSong.ModuleMessage = "Error reading file, check your ID3-tags"
    
    return retSong
