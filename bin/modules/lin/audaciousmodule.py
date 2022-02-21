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
import subprocess, sys

def run(MaxTandaLength):
    
    playlist = []
    
    try:
        check = subprocess.check_output(["audtool", "--current-song"]).rstrip('\n')
    except:
        playbackStatus = 'PlayerNotRunning'
        return playlist, playbackStatus
    
    playbackStatus  = subprocess.check_output(["audtool", "--playback-status"]).rstrip('\n')
    
    # Break and return empty if nothing is playing
    if check in 'No song playing.':
        playbackStatus = 'Stopped'
        return playlist, playbackStatus
    elif playbackStatus in 'stopped':
        playbackStatus = 'Stopped'
        return playlist, playbackStatus
    elif playbackStatus in 'paused':
        playbackStatus = 'Paused'
        return playlist, playbackStatus
    elif playbackStatus in 'playing':
        #   print "Lets get some info!"
        playbackStatus = 'Playing'

#Declare our position
    currentsong     = int(subprocess.check_output(["audtool", "--playlist-position"]).rstrip('\n'))
    playlistlength  = int(subprocess.check_output(["audtool", "--playlist-length"]).rstrip('\n'))
    searchsong = currentsong # Start on the current song
    
    while searchsong < playlistlength+1 and searchsong < currentsong+MaxTandaLength+2:
        playlist.append(getSongAt( searchsong))
        searchsong = searchsong+1
    return playlist, playbackStatus

def getSongAt(songPosition = 1):
    retSong = SongObject()
    retSong.Artist      = subprocess.check_output( ["audtool", "--playlist-tuple-data", "artist",   str(songPosition)]).rstrip('\n')
    retSong.Album       = subprocess.check_output( ["audtool", "--playlist-tuple-data", "album",    str(songPosition)]).rstrip('\n')
    retSong.Title       = subprocess.check_output( ["audtool", "--playlist-tuple-data", "title",    str(songPosition)]).rstrip('\n')
    retSong.Genre       = subprocess.check_output( ["audtool", "--playlist-tuple-data", "genre",    str(songPosition)]).rstrip('\n')
    retSong.Comment     = subprocess.check_output( ["audtool", "--playlist-tuple-data", "comment",  str(songPosition)]).rstrip('\n')
    retSong.Composer    = subprocess.check_output( ["audtool", "--playlist-tuple-data", "composer", str(songPosition)]).rstrip('\n')
    retSong.Year        = subprocess.check_output( ["audtool", "--playlist-tuple-data", "year",     str(songPosition)]).rstrip('\n')
    #retSong._Singer
    retSong.AlbumArtist = subprocess.check_output( ["audtool", "--playlist-tuple-data", "albumartist", str(songPosition)]).rstrip('\n')
    retSong.Performer   = subprocess.check_output( ["audtool", "--playlist-tuple-data", "performer",   str(songPosition)]).rstrip('\n')
    #retSong.IsCortina
    
    
    return retSong
