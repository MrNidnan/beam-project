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
from bin.Modules.Lin.dbusutils import getDbusSession, getDbusInterface
from bin.songclass import SongObject


def run(MaxTandaLength):

    playlist = []
    playbackStatus  = ''
    try:
        proxy = getDbusSession('org.gnome.Rhythmbox3', '/org/mpris/MediaPlayer2', 'org.gnome.Rhythmbox3')
        properties_manager = getDbusInterface(proxy, 'org.freedesktop.DBus.Properties')
        metadata = properties_manager.Get('org.mpris.MediaPlayer2.Player', 'Metadata')
        playbackStatus = properties_manager.Get('org.mpris.MediaPlayer2.Player', 'PlaybackStatus')
    except:
        playbackStatus  = 'PlayerNotRunning'
        return playlist, playbackStatus

    # Retrieve current song
    if playbackStatus == 'Playing':
        playlist.append( getSongObjectFromTrack(metadata) )
        
    return playlist, playbackStatus

def getSongObjectFromTrack(metadata):
    retSong = SongObject()

    try:
        retSong.Artist      = (metadata['xesam:artist'])[0]
    except:
        pass
        
    try:
        retSong.Album       = metadata['xesam:album']
    except:
        pass
    
    try:
        retSong.Title       = metadata['xesam:title']
    except:
        pass
        
    try:
        retSong.Genre       = (metadata['xesam:genre'])[0]
    except:
        pass
        
    try:
        retSong.Comment     = (metadata['xesam:comment'])[0]
    except:
        pass
        

    # try:
    # unresolved reference
    #     retSong.Composer    = (Track['composer'])
    # except:
    #     pass
        
    try:
        retSong.Year        = (metadata['xesam:contentCreated'])[:4]
    except:
        pass
        
    #retSong.Singer
    
    try:
        retSong.AlbumArtist = ""
    except:
        pass
        
    try:
        retSong.Performer   = ""
    except:
         pass
     #retSong.IsCortina
    
    return retSong

