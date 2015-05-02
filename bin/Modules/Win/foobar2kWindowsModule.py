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
import subprocess
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
    if ApplicationRunning("foobar2000.exe"):
        try:
            Foobar = win32com.client.Dispatch("Foobar2000.Application.0.7")
        except:
            playbackStatus = 'PlayerNotRunning'
            return playlist, playbackStatus
    else:
        playbackStatus = 'PlayerNotRunning'
        return playlist, playbackStatus

    #
    # Playback Status
    #
    if not Foobar.Playback.IsPlaying:
        playbackStatus = 'Stopped'
        return playlist, playbackStatus
    elif Foobar.Playback.IsPlaying and Foobar.Playback.IsPaused:
        playbackStatus = 'Paused'
        return playlist, playbackStatus
    #
    # Playback = Playing
    #
    elif Foobar.Playback.IsPlaying and not Foobar.Playback.IsPaused:
        playbackStatus = 'Playing'
        try:
            playlist.append(getSongAt(Foobar, 1))
        except:
            pass

        return playlist, playbackStatus

###############################################################
#
# Full read - Player specific
#
###############################################################

def getSongAt(Foobar, songPosition):
    retSong = SongObject()

    retSong.Artist      = Foobar.Playback.FormatTitle("[%artist%]").encode('latin-1')
    retSong.Album       = Foobar.Playback.FormatTitle("[%album%]").encode('latin-1')
    retSong.Title       = Foobar.Playback.FormatTitle("[%title%]").encode('latin-1')
    retSong.Genre       = Foobar.Playback.FormatTitle("[%genre%]").encode('latin-1')
    retSong.Comment     = Foobar.Playback.FormatTitle("[%comment%]").encode('latin-1')
    retSong.Composer    = Foobar.Playback.FormatTitle("[%composer%]").encode('latin-1')
    retSong.Year        = Foobar.Playback.FormatTitle("[%date%]")
    #retSong._Singer     Defined by beam
    retSong.AlbumArtist = Foobar.Playback.FormatTitle("[%album artist%]").encode('latin-1')
    retSong.Performer   = Foobar.Playback.FormatTitle("[%performer%]").encode('latin-1')
    #retSong.IsCortina   Defined by beam
    retSong.fileUrl     = Foobar.Playback.FormatTitle("[%path%]").encode('latin-1')
    
    return retSong

###############################################################
#
# Application running Windows-specific
#
###############################################################

def ApplicationRunning(AppName):
    import subprocess
    cmd = 'WMIC PROCESS get Caption,Commandline,Processid'
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    for line in proc.stdout:
        if AppName in line:
            proc.kill()
            return True
    proc.kill()
    return False
