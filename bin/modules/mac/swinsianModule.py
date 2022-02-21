#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    Copyright (C) 2015 Mikael Holber http://http://www.beam-project.com
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
from bin.Modules.Mac.macutils import AppleScript
from bin.songclass import SongObject
import sys, time

###############################################################
#
# Define operations
#
###############################################################

GetStatus   = '''tell application "Swinsian"
                 set playstatus to player state
                 end tell
                 return playstatus'''
GetTitle   = '''on run argv
                    tell application "Swinsian"
                       set var1 to name of track argv of playback queue
                    end tell
                    return var1
                end run'''
GetArtist   = '''on run argv
                    tell application "Swinsian"
                       set var1 to artist of track argv of playback queue
                    end tell
                    return var1
                end run'''
GetAlbum   = '''on run argv
                    tell application "Swinsian"
                       set var1 to album of track argv of playback queue
                    end tell
                    return var1
                end run'''
GetAlbumArtist   = '''on run argv
                    tell application "Swinsian"
                       set var1 to album artist of track argv of playback queue
                    end tell
                    return var1
                end run'''
GetGenre   = '''on run argv
                    tell application "Swinsian"
                       set var1 to genre of track argv of playback queue
                    end tell
                    return var1
                end run'''
GetYear   = '''on run argv
                    tell application "Swinsian"
                       set var1 to year of track argv of playback queue
                    end tell
                    return var1
                end run'''
GetComment   = '''on run argv
                    tell application "Swinsian"
                       set var1 to comment of track argv of playback queue
                    end tell
                    return var1
                end run'''
GetComposer   = '''on run argv
                    tell application "Swinsian"
                       set var1 to composer of track argv of playback queue
                    end tell
                    return var1
                end run'''
GetAllInfo    = '''on run argv
                    tell application "Swinsian"
                       set artistname to artist of track argv of playback queue
                       set trackname to name of track argv of playback queue
                       set albumname to album of track argv of playback queue
                       set albumartist to album artist of track argv of playback queue
                       set trackyear to year of track argv of playback queue
                       set comm to comment of track argv of playback queue
                       set trackgenre to genre of track argv of playback queue
                       set trackcomposer to composer of track argv of playback queue
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
                    
                    if comm is in "missing value"
                    set comm to ""
                    end if
                    
                    if trackgenre is in "missing value"
                    set trackgenre to ""
                    end if
                    
                    if trackcomposer is in "missing value"
                    set trackcomposer to ""
                    end if
                    
                    return {artistname, trackname, albumname, albumartist, trackyear, comm, trackgenre, trackcomposer}
                 end run'''

GetTrackURL     = '''on run argv
                      tell application "Swinsian"
                        try
                            set urlentry to path of track argv of playback queue
                        on error
                            set urlentry to ""
                        end try
                      end tell
                      return {urlentry}
                    end run'''

GetAllTrackURL     = '''on run {argv, argw}
                        set the urllist to {}
                        set startvalue to argv
                        set stopvalue to argw
                        tell application "Swinsian"
                            repeat with trackx from startvalue to stopvalue
                                try
                                    set the end of the urllist to path of track trackx of playback queue
                                on error
                                    set the end of the urllist to ""
                                end try
                            end repeat
                        end tell
                        return {urllist}
                     end run'''

CheckRunning    = '''tell application "System Events"
                        count (every process whose name is "Swinsian")
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

    if playbackStatus in 'stopped': 
        playbackStatus = 'Stopped'
        return playlist, playbackStatus
    elif playbackStatus in 'paused': 
        playbackStatus = 'Paused'
        return playlist, playbackStatus
    #
    # Playback = Playing
    #
    elif playbackStatus in 'playing':
        playbackStatus = 'Playing'

    # Declare our position
    currentsong     = 1 # Always use queue for Swinsian
    playlistlength  = currentsong+MaxTandaLength+2
    searchsong = currentsong

    #
    # Full-read primary from URL
    #
    while searchsong < playlistlength and searchsong < currentsong+MaxTandaLength+2:
        try:
            playlist.append(getSongFromUrl(searchsong))
        except:
            break
        searchsong = searchsong+1
    return playlist, playbackStatus


###############################################################
#
# Full read from file - Player specific
#
###############################################################

def getSongFromUrl(songPosition):
    retSong = SongObject()
    try:
        retSong.FilePath = AppleScript(GetTrackURL, [str(songPosition)]).rstrip('\n')
    except:
        retSong = getSongAt(songPosition)
    
    try:
        retSong.buildFromPath(retSong.FilePath)
    except:
        retSong = getSongAt(songPosition)
    
    return retSong

###############################################################
#
# Full read from player (Fallback) - Player specific
#
###############################################################

def getSongAt(songPosition = 1):
    retSong = SongObject()
    try:
        # FASTER!
        # If there are no "," then this method works
        var = AppleScript(GetAllInfo, [str(songPosition)]).rstrip('\n')
        retSong.Artist, retSong.Title, retSong.Album, retSong.AlbumArtist, retSong.Year, retSong.Comment, retSong.Genre, retSong.Composer = var.split(', ')
    except:
        # SLOW!
        # If there are "," in the fields, then this method works
        retSong.Artist      = AppleScript(GetArtist, [str(songPosition)]).rstrip('\n')
        retSong.Album       = AppleScript(GetAlbum, [str(songPosition)]).rstrip('\n')
        retSong.Title       = AppleScript(GetTitle, [str(songPosition)]).rstrip('\n')
        retSong.Genre       = AppleScript(GetGenre, [str(songPosition)]).rstrip('\n')
        retSong.Comment     = AppleScript(GetComment, [str(songPosition)]).rstrip('\n')
        retSong.Composer    = AppleScript(GetComposer, [str(songPosition)]).rstrip('\n')
        retSong.Year        = AppleScript(GetYear, [str(songPosition)]).rstrip('\n')
        #retSong._Singer
        retSong.AlbumArtist = AppleScript(GetAlbumArtist, [str(songPosition)]).rstrip('\n')
    #retSong.Performer
    #retSong.IsCortina
    retSong.ModuleMessage = "Error reading file, using fallback info from player"
    return retSong

