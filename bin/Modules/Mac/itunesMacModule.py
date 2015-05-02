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

from bin.songclass import SongObject
import sys, time
from subprocess import Popen, PIPE
from copy import deepcopy

###############################################################
#
# Define operations
#
###############################################################

GetPosition = '''tell application "iTunes" 
                 set pos to index of current track
                 end tell
                 return pos'''
GetStatus   = '''tell application "iTunes"
                 set playstatus to player state
                 end tell
                 return playstatus'''
GetTitle   = '''on run argv
                    tell application "iTunes"
                       set var1 to name of track argv of current playlist
                    end tell
                    return var1
                end run'''
GetArtist   = '''on run argv
                    tell application "iTunes"
                       set var1 to artist of track argv of current playlist
                    end tell
                    return var1
                end run'''
GetAlbum   = '''on run argv
                    tell application "iTunes"
                       set var1 to album of track argv of current playlist
                    end tell
                    return var1
                end run'''
GetAlbumArtist   = '''on run argv
                    tell application "iTunes"
                       set var1 to album artist of track argv of current playlist
                    end tell
                    return var1
                end run'''
GetGenre   = '''on run argv
                    tell application "iTunes"
                       set var1 to genre of track argv of current playlist
                    end tell
                    return var1
                end run'''
GetYear   = '''on run argv
                    tell application "iTunes"
                       set var1 to year of track argv of current playlist
                    end tell
                    return var1
                end run'''
GetComment   = '''on run argv
                    tell application "iTunes"
                       set var1 to comment of track argv of current playlist
                    end tell
                    return var1
                end run'''
GetComposer   = '''on run argv
                    tell application "iTunes"
                       set var1 to composer of track argv of current playlist
                    end tell
                    return var1
                end run'''
GetAllInfo    = '''on run argv
                    tell application "iTunes"
                       set artistname to artist of track argv of current playlist
                       set trackname to name of track argv of current playlist
                       set albumname to album of track argv of current playlist
                       set albumartist to album artist of track argv of current playlist
                       set trackyear to year of track argv of current playlist
                       set comm to comment of track argv of current playlist
                       set trackgenre to genre of track argv of current playlist
                       set trackcomposer to composer of track argv of current playlist
                    end tell
                    return {artistname, trackname, albumname, albumartist, trackyear, comm, trackgenre, trackcomposer}
                 end run'''

QuickRead     =  '''on run {argv, argw}
                        set the artistlist to {}
                        set the titlelist to {}
                        set startvalue to argv
                        set stopvalue to argw
                        tell application "iTunes"
                            repeat with trackx from startvalue to stopvalue
                                try
                                    set the end of the artistlist to artist of track trackx of current playlist
                                    set the end of the titlelist to name of track trackx of current playlist
                                on error
                                    set the end of the artistlist to ""
                                    set the end of the titlelist to ""
                                end try
                            end repeat
                        end tell
                        return {artistlist, titlelist}
                    end run'''


CheckRunning = '''tell application "System Events"
                    count (every process whose name is "iTunes")
                  end tell'''

###############################################################
#
# MAIN FUNCTION
#
###############################################################

def run(MaxTandaLength, LastPlaylist):

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
    currentsong     = int(AppleScript(GetPosition, []))
    playlistlength  = currentsong+MaxTandaLength+2 # Not available for iTunes
    searchsong = currentsong

    #
    # Quick-read
    #
    if quickRead(currentsong, LastPlaylist, MaxTandaLength):
        print "Quick-read"
        playlist = deepcopy(LastPlaylist)
        return playlist, playbackStatus

    #
    # Full-read
    #
    print "Full-read"
    while searchsong < playlistlength and searchsong < currentsong+MaxTandaLength+2:
        try:
            playlist.append(getSongAt( searchsong))
        except:
            break
        searchsong = searchsong+1
    return playlist, playbackStatus

###############################################################
#
# Quick read - Player specific
#
###############################################################

def quickRead(songPosition = 1, LastRead = [], MaxTandaLength = 1):
    try:
        if len(LastRead) < MaxTandaLength + 2:
            var      = AppleScript(QuickRead, [str(songPosition), str(songPosition+len(LastRead))]).rstrip('\n')
        else:
            var      = AppleScript(QuickRead, [str(songPosition), str(songPosition+len(LastRead)-1)]).rstrip('\n')
        ArtistsAndTitles =  var.split(', ')
        #print "Quick:",ArtistsAndTitles
        Last = []
        try:
            for i in range(0,len(LastRead)):
                Song = LastRead[i]
                Last.append(str(Song.Artist))
            for i in range(0,len(LastRead)):
                Song = LastRead[i]
                Last.append(str(Song.Title))
        except:
            pass
        #print "Previous:",Last
        if Last == ArtistsAndTitles:
            return True
    except:
        pass

    #print "New!"
    return False

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
        #retSong._Singer     Defined by beam
        retSong.AlbumArtist = AppleScript(GetAlbumArtist, [str(songPosition)]).rstrip('\n')
        #retSong.Performer   Does not exist for itunes
        #retSong.IsCortina   Defined by beam
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
