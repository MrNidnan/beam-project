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
#    XX/XX/2014 Version 1.0
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

GetStatus   = '''tell application "Decibel"
                    set pstatus to playing
                 end tell
                 return pstatus'''

GetSongs    = '''tell application "Decibel"
                    set artistname to artist of nowPlaying
                    set trackname to title of nowPlaying
                    set albumname to album title of nowPlaying
                    set albumartist to album artist of nowPlaying
                    set trackyear to release date of nowPlaying
                    set trackgenre to genre of nowPlaying
                    set trackcomposer to composer of nowPlaying
                end tell

                if artistname is in "missing value"
                    set artistname to ""
                end if

                if trackname is in "missing value"
                    set trackname to ""
                end if

                if albumname is in "missing value"
                    set albumname to ""
                end if

                if albumartist is in "missing value"
                    set albumartist to ""
                end if

                if trackyear is in "missing value"
                    set trackyear to ""
                end if

                if trackgenre is in "missing value"
                    set trackgenre to ""
                end if

                if trackcomposer is in "missing value"
                    set trackcomposer to ""
                end if

                return {artistname, trackname, albumname, albumartist, trackyear, trackgenre, trackcomposer}'''

GetTitle   = '''tell application "Decibel"
                   set var1 to title of nowPlaying
                end tell
                if var1 is in "missing value"
                    set var1 to ""
                end if
                return var1'''

GetArtist   = '''tell application "Decibel"
                   set var1 to artist of nowPlaying
                 end tell
                if var1 is in "missing value"
                    set var1 to ""
                end if
                return var1'''

GetAlbum   = '''tell application "Decibel"
                   set var1 to album title of nowPlaying
                end tell
                if var1 is in "missing value"
                    set var1 to ""
                end if
                return var1'''

GetAlbumArtist   = '''tell application "Decibel"
                         set var1 to album artist of nowPlaying
                      end tell
                      if var1 is in "missing value"
                         set var1 to ""
                      end if
                      return var1'''

GetGenre   = '''tell application "Decibel"
                   set var1 to genre of nowPlaying
                end tell
                if var1 is in "missing value"
                    set var1 to ""
                end if
                return var1'''

GetYear    = '''tell application "Decibel"
                   set var1 to release date of nowPlaying
                end tell
                if var1 is in "missing value"
                    set var1 to ""
                end if
                return var1'''

GetComposer   = '''tell application "Decibel"
                       set var1 to to composer of nowPlaying
                    end tell
                    return var1
                end run'''

GetTrackURL     = '''tell application "Decibel"
                        set var1 to file of nowPlaying
                     end tell
                  return var1'''

CheckRunning = '''tell application "System Events"
                    count (every process whose name is "Decibel")
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

    if playbackStatus in 'false':
        playbackStatus = 'Paused'
        return playlist, playbackStatus
    #
    # Playback = Playing
    #
    elif playbackStatus in 'true':
        playbackStatus = 'Playing'

    #
    # Read from file
    #
    playlist.append(getSongFromUrl(1))
    return playlist, playbackStatus

###############################################################
#
# Full read from file - Player specific
#
###############################################################

def getSongFromUrl(songPosition = 1):
    retSong = SongObject()
    try:
        retSong.fileUrl = AppleScript(GetTrackURL, [str(songPosition)]).rstrip('\n').replace(':','/')
        retSong.fileUrl = "/Users"+retSong.fileUrl.split('/Users',1)[1]
    except:
        return retSong
    
    try:
        retSong.buildFromUrl(retSong.fileUrl)
    except:
        retSong = getSongAt(1)
    
    return retSong

###############################################################
#
# Full read from player - Player specific
#
###############################################################

def getSongAt(songPosition = 1):
    retSong = SongObject()
    try:
        # FASTER!
        # If there are no "," then this method works
        var = AppleScript(GetSongs, [str(1)]).rstrip('\n')
        retSong.Artist, retSong.Title, retSong.Album, retSong.AlbumArtist, retSong.Year, retSong.Comment, retSong.Genre, retSong.Composer = var.split(', ')
    except:
        # SLOW!
        # If there are "," in the fields, then this method works
        retSong.Artist      = AppleScript(GetArtist, [str(songPosition)]).rstrip('\n')
        retSong.Album       = AppleScript(GetAlbum, [str(songPosition)]).rstrip('\n')
        retSong.Title       = AppleScript(GetTitle, [str(songPosition)]).rstrip('\n')
        retSong.Genre       = AppleScript(GetGenre, [str(songPosition)]).rstrip('\n')
        #retSong.Comment
        retSong.Composer    = AppleScript(GetComposer, [str(songPosition)]).rstrip('\n')
        retSong.Year        = AppleScript(GetYear, [str(songPosition)]).rstrip('\n')
        #retSong._Singer      
        retSong.AlbumArtist = AppleScript(GetAlbumArtist, [str(songPosition)]).rstrip('\n')
        #retSong.Performer
        #retSong.IsCortina

    retSong.ModuleMessage = "Error reading file, using fallback info from player"
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