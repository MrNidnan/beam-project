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

GetPosition = '''tell application "Embrace" 
                 return current index
                 end tell'''
GetChangeIDPosition = '''tell application "Embrace" 
                 return current index
                 end tell'''
GetAllInfo    = '''on run argv
                    tell application "Embrace"
                       set theAggregate to aggregate of track argv
                       set theYear to year of track argv
                    end tell
                    set AppleScript's text item delimiters to tab
                    return {theYear, theAggregate} as string
                 end run'''
QuickRead     =  '''on run {argv, argw}
                        set the artistlist to {}
                        set the titlelist to {}
                        set startvalue to argv
                        set stopvalue to argw
                        tell application "Embrace"
                            repeat with trackx from startvalue to stopvalue
                                try
                                    set the end of the artistlist to artist of track trackx
                                    set the end of the titlelist to title of track trackx
                                on error
                                    set the end of the artistlist to ""
                                    set the end of the titlelist to ""
                                end try
                            end repeat
                        end tell
                        set AppleScript's text item delimiters to ASCII character 0
                        return {artistlist, titlelist} as string
                    end run'''


CheckRunning = '''tell application "System Events"
                    count (every process whose name is "Embrace")
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

    # Declare our position
    currentsong     = int(AppleScript(GetPosition, []))
    if currentsong == 0:
        playbackStatus = 'Stopped'
        return playlist, playbackStatus

    playbackStatus = 'Playing'
    playlistlength  = currentsong+MaxTandaLength+2
    searchsong = currentsong

    #
    # Quick-read
    #
    if quickRead(currentsong, LastPlaylist, MaxTandaLength):
        print "Quick-read"
        playlist = deepcopy(LastPlaylist)
        print currentsong

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
            var = AppleScript(QuickRead, [str(songPosition), str(songPosition+len(LastRead))]).rstrip('\n')
        else:
            var = AppleScript(QuickRead, [str(songPosition), str(songPosition+len(LastRead)-1)]).rstrip('\n')
        ArtistsAndTitles =  var.split(chr(0))
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
        var = AppleScript(GetAllInfo, [str(songPosition)]).rstrip('\n')
        retSong.Year, retSong.Title, retSong.Artist, retSong.Album, retSong.Genre, retSong.Comment, retSong.AlbumArtist, retSong.Composer = var.split('\t')[:8]
    except: 
        # Embrace guarantees that 'aggregate' will contain sanitized fields in the above order
        pass
    
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
