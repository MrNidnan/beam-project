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
import urllib

from bin.songclass import SongObject

try:
    import pythoncom
    import win32com.client
except ImportError:
    pass
from bin.Modules.Win.winutils import applicationrunning

###############################################################
#
# Define operations
#
###############################################################

def run(MaxTandaLength):

    playlist = []
    playbackStatus = ''
    
    #
    # Player Status
    #
    if not applicationrunning("foobar2000.exe"):
        playbackStatus = 'PlayerNotRunning'
        return playlist, playbackStatus

    pythoncom.CoInitialize()
    try:
        # shell = win32com.client.Dispatch("WScript.Shell")
        progID = "Foobar2000.Application.0.7"
        Foobar = win32com.client.Dispatch(progID)

        # Playback Status
        if not Foobar.Playback.IsPlaying:
            playbackStatus = 'Stopped'
        else:
            if Foobar.Playback.IsPaused:
                playbackStatus = 'Paused'
            else:
                playbackStatus = 'Playing'
                playlist.append(getSongAt(Foobar, 1))
    finally:
        pythoncom.CoUninitialize()

    return playlist, playbackStatus

###############################################################
#
# Full read - Player specific
#
###############################################################

def getSongAt(Foobar, songPosition):
    retSong = SongObject()

    retSong.Artist      = Foobar.Playback.FormatTitle("[%artist%]")
    retSong.Album       = Foobar.Playback.FormatTitle("[%album%]")
    retSong.Title       = Foobar.Playback.FormatTitle("[%title%]")
    retSong.Genre       = Foobar.Playback.FormatTitle("[%genre%]")
    retSong.Comment     = Foobar.Playback.FormatTitle("[%comment%]")
    retSong.Composer    = Foobar.Playback.FormatTitle("[%composer%]")
    retSong.Year        = Foobar.Playback.FormatTitle("[%date%]")
    #retSong._Singer     Defined by beam
    retSong.AlbumArtist = Foobar.Playback.FormatTitle("[%album artist%]")
    retSong.Performer   = Foobar.Playback.FormatTitle("[%performer%]")
    #retSong.IsCortina   Defined by beam

    retSong.FilePath     = Foobar.Playback.FormatTitle("[%path%]")
    # 'C:\\Users\\DJ\\Tango\\Todays Tango\\Cola \'e Paja - Orquesta Típica Porteña - 1928-04-28.mp3'
    
    return retSong
