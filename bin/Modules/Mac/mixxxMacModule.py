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

# from bin.songclass import SongObject
# import sys
from subprocess import Popen, PIPE
import bin.Modules.mixxxSqlite


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


def run(MaxTandaLength, LastPlaylist):
    # print("mixxxModule.run()")
    playlist = []

    #
    # Player Status
    #
    if int(AppleScript(CheckRunning, []).strip()) == 0:
        playback_status = 'PlayerNotRunning'
        return playlist, playback_status

    #
    # Playback Status
    #
    try:
        playback_status = AppleScript(GetStatus, []).rstrip('\n')
    except:
        playback_status = 'PlayerNotRunning'
        return playlist, playback_status

    playlist, playback_status = bin.Modules.mixxxSqlite.run(MaxTandaLength, LastPlaylist)

    return playlist, playback_status


###############################################################
#
# AppleScript-function - MacOSX-specific
#
###############################################################

def AppleScript(scpt, args=[]):
     p = Popen(['osascript', '-'] + args, stdin=PIPE, stdout=PIPE, stderr=PIPE)
     stdout, stderr = p.communicate(scpt)
     return stdout