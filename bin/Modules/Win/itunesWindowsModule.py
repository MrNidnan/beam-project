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
    if ApplicationRunning("iTunes.exe"):
        try:
            itunes = win32com.client.gencache.EnsureDispatch ("iTunes.Application")
        except:
            playbackStatus = 'PlayerNotRunning'
            return playlist, playbackStatus
    else:
        playbackStatus = 'PlayerNotRunning'
        return playlist, playbackStatus

    #
    # Playback Status
    #  
    if not itunes.PlayerState == 1:
        playbackStatus = 'Stopped'
        return playlist, playbackStatus
    #
    # Playback = Playing
    #
    else:
        playbackStatus = 'Playing'

        #Declare our position
        currentsong = itunes.CurrentTrack.PlayOrderIndex
        playlistlength  = currentsong+MaxTandaLength+2 # Not available for iTunes
        searchsong = currentsong

    #
    # Full-read
    #
    while searchsong < playlistlength and searchsong < currentsong+MaxTandaLength+2:
        try:
            playlist.append(getSongAt(itunes, searchsong))
        except:
            break
        searchsong = searchsong+1
    return playlist, playbackStatus

###############################################################
#
# Full read - Player specific
#
###############################################################

def getSongAt(itunes, songPosition):
    retSong = SongObject()
    Track = itunes.CurrentTrack.Playlist.Tracks.Item(songPosition)

    retSong.Artist      = (Track.Artist).encode('latin-1')
    retSong.Album       = (Track.Album).encode('latin-1')
    retSong.Title       = (Track.Name).encode('latin-1')
    retSong.Genre       = (Track.Genre).encode('latin-1')
    retSong.Comment     = (Track.Comment).encode('latin-1')
    retSong.Composer    = (Track.Composer).encode('latin-1')
    retSong.Year        = Track.Year
    #retSong._Singer     Defined by beam
    #retSong.AlbumArtist = (Track.AlbumArtist).encode('latin-1') # Does not exist for iTunes?
    #retSong.Performer   = (Track.Performer).encode('latin-1') # Does not exist for iTunes?
    #retSong.IsCortina   Defined by beam
    #retSong.fileUrl     Does not exist for iTunes
    #retSong.ModuleMessage = Not needed for iTunes
    
    return retSong

###############################################################
#
# Application running Windows-specific
#
###############################################################

def ApplicationRunning(AppName):
    from subprocess import Popen, PIPE
    cmd = 'WMIC PROCESS get Caption,Commandline,Processid'
    proc = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    for line in proc.stdout:
        if AppName in line:
            proc.kill()
            return True
    proc.kill()
    return False
