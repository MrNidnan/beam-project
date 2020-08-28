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
# An Mpris2 angepasst von Dominik und Peter Wenger 27.11.18

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
    mprisVersion=1
    
    try:
        bus = dbus.SessionBus()
        player = bus.get_object('org.mpris.clementine', '/Player')
        tracklist = bus.get_object('org.mpris.clementine', '/TrackList')
        mprisVersion=1
    except:
        try:
            bus = dbus.SessionBus()
            player = bus.get_object('org.mpris.MediaPlayer2.clementine', '/org/mpris/MediaPlayer2')
            
            mprisVersion=2
        except:
            playbackStatus  = 'PlayerNotRunning'
            return playlist, playbackStatus
    
    # Playstatus: 0 = Playing, 1 = Paused, 2 = Stopped
    if mprisVersion == 1:
        Status = player.GetStatus()[0] 
        if Status == 0:
            playbackStatus = 'Playing'
        
            
            #Extract the playlist songs
            currentsong = tracklist.GetCurrentTrack()
            playlistlength = tracklist.GetLength()
            iterator_song = currentsong 
            
            while iterator_song < currentsong+MaxTandaLength+2 and iterator_song < playlistlength:
                playlist.append(getSongObjectFromTrack(tracklist.GetMetadata(iterator_song)))
                iterator_song = iterator_song+1
            
        if Status == 1:
            playbackStatus = 'Paused'
        if Status == 2:
            playbackStatus = 'Stopped'
        
        
    elif mprisVersion ==2:
        StatusString = player.Get('org.mpris.MediaPlayer2.Player','PlaybackStatus',dbus_interface='org.freedesktop.DBus.Properties')
        if StatusString == 'Playing': 
            currentMetadata = player.Get('org.mpris.MediaPlayer2.Player','Metadata',dbus_interface='org.freedesktop.DBus.Properties')
            playlist.append(getSongObjectFromTrackMpris2(currentMetadata))
           
            #tracklist = player.Get('org.mpris.MediaPlayer2.TrackList','Tracks',dbus_interface='org.freedesktop.DBus.Properties')
            #tracklist from clementine is empty ??
           
        playbackStatus = StatusString
    return playlist, playbackStatus

def getSongObjectFromTrackMpris2(Track):
    retSong = SongObject()
    
    try:
        retSong.Artist      = Track['xesam:artist'][0]
    except:
        pass
        
    try:
        retSong.Album       = Track['xesam:album']
    except:
        pass
    
    try:
        retSong.Title       = Track['xesam:title']
    except:
        pass
        
    try:
        retSong.Genre       = Track['xesam:genre'][0]
    except:
        pass
        
    try:
        retSong.Comment     = Track['xesam:comment'][0]
    except:
        pass
        
    try:
        retSong.Composer    = Track['xesam:composer']
    except:
        pass
        
    try:
        # Integer
        retSong.Year        = Track['year']
    except:
        pass
        
    #retSong.Singer
    
    try:
        retSong.AlbumArtist = Track['xesam:albumArtist'][0]
    except:
        pass
        
    try:
        # nicht implementiert?
        retSong.Performer   = Track['xesam:performer']
    except:
         pass
     #retSong.IsCortina
     
    return retSong


def getSongObjectFromTrack(Track):
    retSong = SongObject()
    
    try:
        retSong.Artist      = Track['artist']
        
    except:
        pass
        
    try:
        retSong.Album       = Track['album']
    except:
        pass
    
    try:
        retSong.Title       = Track['title']
    except:
        pass
        
    try:
        retSong.Genre       = Track['genre']
    except:
        pass
        
    try:
        retSong.Comment     = Track['comment']
    except:
        pass
        
    try:
        retSong.Composer    = Track['composer']
    except:
        pass
        
    try:
        retSong.Year        = Track['contentCreated'][:3]
    except:
        pass
        
    #retSong.Singer
    
    try:
        retSong.AlbumArtist = Track['album artist']
    except:
        pass
        
    try:
        retSong.Performer   = Track['performer']
    except:
         pass
     #retSong.IsCortina
     
    return retSong

