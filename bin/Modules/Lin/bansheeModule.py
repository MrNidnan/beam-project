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
    BansheeState = ''
    
    try:
        bus = dbus.SessionBus()
        banshee = bus.get_object("org.bansheeproject.Banshee", "/org/bansheeproject/Banshee/PlayerEngine")
        BansheeState = banshee.GetCurrentState()
    except:
        playbackStatus  = 'PlayerNotRunning'
        return playlist, playbackStatus
   
    if BansheeState == 'playing':
        playbackStatus = 'Playing'
        # Retrieve current song
        currentTrack = banshee.GetCurrentTrack()
        playlist.append(getSongObjectFromTrack(currentTrack))
    if BansheeState == 'paused':
        playbackStatus = 'Paused'
    if BansheeState == 'stopped':
        playbackStatus = 'Stopped'

    return playlist, playbackStatus


def getSongObjectFromTrack(Track):
    retSong = SongObject()
    
    try:
        retSong.Artist      = (Track[u'artist']).encode('utf-8')
    except:
        pass
        
    try:
        retSong.Album       = (Track[u'album']).encode('utf-8')
    except:
        pass
    
    try:
        retSong.Title       = (Track[u'name']).encode('utf-8')
    except:
        pass
        
    try:
        retSong.Genre       = (Track[u'genre']).encode('utf-8')
    except:
        pass
        
    try:
        retSong.Comment     = (Track[u'comment']).encode('utf-8')
    except:
        pass
        
    try:
        retSong.Composer    = (Track[u'composer']).encode('utf-8')
    except:
        pass
        
    try:
        retSong.Year        = (Track[u'year'])
    except:
        pass
        
    #retSong.Singer
    
    try:
        retSong.AlbumArtist = (Track[u'album artist']).encode('utf-8')
    except:
        pass
        
    try:
        retSong.Performer   = (Track[u'performer']).encode('utf-8')
    except:
         pass
     #retSong.IsCortina
    
    return retSong

