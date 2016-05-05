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
import time


###############################################################
#
# Define operations
#
###############################################################

EmbraceScript = '''
    on run {songCount}
    tell application "System Events"
        if (count of (every process whose name is "Embrace")) = 0 then
            return "PlayerNotRunning"
        end if
    end tell

    tell application "Embrace"
        set startvalue to current index
        if startvalue = 0 then
            return "Stopped"
        end if
        
        set stopvalue to (startvalue + songCount)
        if stopvalue > (count of tracks) then
            set stopvalue to (count of tracks)
        end if
        
        set AppleScript's text item delimiters to tab
        
        set theResult to {"Running"}
        
        repeat with trackx from startvalue to stopvalue
            set theAggregate to aggregate of track trackx
            set theYear to year of track trackx
            set theResult to theResult & ({theYear, theAggregate} as string)
        end repeat
        
        set AppleScript's text item delimiters to ASCII character 10
        return (theResult as string)
    end tell
    end run
    '''

###############################################################
#
# MAIN FUNCTION
#
###############################################################

def run(MaxTandaLength, LastPlaylist):
    start = time.time()

    # The first line is the playbackStatus.  Additional lines are tab-delimited song data
    lines = AppleScript(EmbraceScript, [str(MaxTandaLength+2)]).rstrip('\n').split("\n")

    # Show timing result in ms
    print "Embrace run() took", (time.time() - start) * 1000, "ms"

    playbackStatus = lines.pop(0)


    return map(makeSong, lines), playbackStatus

    
def makeSong(line):
    retSong = SongObject()

    try:
        retSong.Year, retSong.Title, retSong.Artist, retSong.Album, retSong.Genre, retSong.Comment, retSong.AlbumArtist, retSong.Composer = line.split('\t')[:8]
    except: 
        # Embrace guarantees that 'aggregate' will contain sanitized fields in the above order
        pass
    
    return retSong


def AppleScript(scpt, args=[]):
    p = Popen(['osascript', '-'] + args, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate(scpt)
    return stdout
