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
from bin.modules.win.winutils import applicationrunning

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
    if not applicationrunning("Media Center 29.exe"):
        playbackStatus = 'PlayerNotRunning'
        return playlist, playbackStatus

    pythoncom.CoInitialize()
    try:
        progID = "MediaJukebox Application"
        mjautomation = win32com.client.Dispatch(progID)

        mjplayback  = mjautomation.GetPlayback();
        mjstate = mjplayback.State;

        # Playback Status
        if mjstate == 0:
            playbackStatus = 'Stopped';
        else:
            if mjstate == 1:
                playbackStatus = 'Paused';
            else:
                if mjstate == 2:
                    playbackStatus = 'Playing';
                    mjplaylist = mjautomation.GetCurPlaylist();
                    minpos = int(mjplaylist.Position);
                    maxpos = int(mjplaylist.GetNumberFiles());
                    for songpos in range (minpos, maxpos):
                      playlist.append(getSongAt(mjplaylist, songpos))
                else:
                    playbackStatus = 'Unknown';
    finally:
        pythoncom.CoUninitialize()

    return playlist, playbackStatus

###############################################################
#
# Full read - Player specific
#
###############################################################

def getSongAt(mjplaylist, songpos):

    mjfile = mjplaylist.GetFile(songpos);

    retSong = SongObject()
    retSong.Artist      = mjfile.Artist;
    retSong.Album       = mjfile.Album;
    retSong.Title       = mjfile.Name;
    retSong.Genre       = mjfile.Genre;
    retSong.Comment     = mjfile.Comment;
    # retSong.Composer    = mjfile.Composer;
    retSong.Year        = mjfile.Year;
    #retSong._Singer     Defined by beam
    retSong.AlbumArtist = mjfile.AlbumArtist;
    # retSong.Performer   = mjfile.Performer;
    #retSong.IsCortina   Defined by beam
    retSong.FilePath     = mjfile.Filename;
    # 'C:\\Users\\DJ\\Music\\Angélique Kidjo\\Fifa\\Bitchifi - Angélique Kidjo.mp3'

    return retSong
