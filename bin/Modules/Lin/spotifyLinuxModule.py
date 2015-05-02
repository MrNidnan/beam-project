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

import imp
try:
    imp.find_module('dbus') #doesn't exist in Windows
    import dbus
except ImportError:
    found = False

def run(MaxTandaLength):

    playlist = []
    playbackStatus  = ''

    try:
        bus = dbus.SessionBus()
        spotify_bus = bus.get_object("org.mpris.MediaPlayer2.spotify", "/org/mpris/MediaPlayer2")
        spotify = dbus.Interface(spotify_bus,"org.mpris.MediaPlayer2.Player")
        properties_manager = dbus.Interface(spotify_bus, 'org.freedesktop.DBus.Properties')
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
        retSong.Artist      = (metadata[u'xesam:artist'])[0].encode('utf-8')
    except:
        pass
        
    try:
        retSong.Album       = metadata['xesam:album'].encode('utf-8')
    except:
        pass
    
    try:
        retSong.Title       = metadata['xesam:title'].encode('utf-8')
    except:
        pass
        
    try:
        retSong.Genre       = (metadata['xesam:genre'])[0].encode('utf-8')
    except:
        pass
        
    try:
        retSong.Comment     = (metadata['xesam:comment'])[0].encode('utf-8')
    except:
        pass
        
    try:
        retSong.Composer    = (Track[u'composer']).encode('utf-8')
    except:
        pass
        
    try:
        retSong.Year        = (metadata['xesam:contentCreated'])[:4].encode('utf-8')
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

