#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    Copyright (C) 2014 Mikael Holber http://http://www.beam-project.com
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
#       - Initial release
#
# This Python file uses the following encoding: utf-8

from bin.songclass import SongObject
import sys
from subprocess import Popen, PIPE

###############################################################
#
# Define operations
#
###############################################################

GetStatus   = '''tell application "Spotify"
                    set pstatus to player state
                 end tell
                 return pstatus'''

GetSongs    = '''tell application "Spotify"
                    set artistname to artist of current track
                    set trackname to name of current track
                    set albumname to album of current track
                    set albumartist to album artist of current track
                end tell
                return {artistname, trackname, albumname, albumartist}'''

GetTitle   = '''tell application "Spotify"
                   set var1 to name of current track
                end tell
                return var1'''

GetArtist   = '''tell application "Spotify"
                    set var1 to artist of current track
                end tell
                return var1'''

GetAlbum   = '''tell application "Spotify"
                    set var1 to album of current track
                end tell
                return var1'''

GetAlbumArtist   = '''tell application "Spotify"
                    set var1 to album artist of current track
                end tell
                return var1'''


CheckRunning = '''tell application "System Events"
    count (every process whose name is "Spotify")
    end tell'''

###############################################################
#
# MAIN FUNCTION
#
###############################################################

def run(MaxTandaLength):

    playlist = []
    
    #
    # Player Status
    #
    if int(AppleScript(CheckRunning, []).strip()) == 0:
        playbackStatus = 'PlayerNotRunning'
        return playlist, playbackStatus
    
    #
    # Playback Status
    #
    try:
        playbackStatus = AppleScript(GetStatus, []).rstrip('\n')
    except:
        playbackStatus = 'PlayerNotRunning'
        return playlist, playbackStatus

    #
    # Playback Status
    #
    if playbackStatus in 'paused':
        playbackStatus = 'Paused'
        return playlist, playbackStatus
    #
    # Playback = Playing
    #
    elif playbackStatus in 'playing':
        playbackStatus = 'Playing'

    playlist.append(getSongAt(1))
    return playlist, playbackStatus

###############################################################
#
# Full read - Player specific
#
###############################################################

def getSongAt(songPosition = 1):
    retSong = SongObject()
    try:
        # FASTER!
        # If there are no "," then this method works
        var = AppleScript(GetSongs, [str(1)]).rstrip('\n')
        retSong.Artist, retSong.Title, retSong.Album, retSong.AlbumArtist = var.split(', ')
    except:
        # SLOW!
        # If there are "," in the fields, then this method works
        retSong.Artist      = AppleScript(GetArtist, [str(songPosition)]).rstrip('\n')
        retSong.Album       = AppleScript(GetAlbum, [str(songPosition)]).rstrip('\n')
        retSong.Title       = AppleScript(GetTitle, [str(songPosition)]).rstrip('\n')
        #retSong.Genre      =
        #retSong.Comment    =
        #retSong.Composer   =
        #retSong.Year       =
        #retSong._Singer      
        retSong.AlbumArtist = AppleScript(GetAlbumArtist, [str(songPosition)]).rstrip('\n')
        #retSong.Performer  =
        #retSong.IsCortina  =
        #retSong.fileUrl     Does not exist for itunes
    
    return retSong

###############################################################
#
# AppleScript-function - MacOSX-specific
#
###############################################################

def AppleScript(scpt, args=[]):
     p = Popen(['osascript', '-'] + args, stdin=PIPE, stdout=PIPE, stderr=PIPE)
     stdout, stderr = p.communicate(scpt)
     return stdout