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
import urllib
from bin.modules.lin.dbusutils import getDbusPlayerValue, getDbusSessionStatus
from bin.songclass import SongObject


def run(MaxTandaLength):

    playlist = []

    dbusSess, playbackStatus = getDbusSessionStatus('org.mpris.MediaPlayer2.clementine')
    if playbackStatus == 'Playing':
        currentMetadata = getDbusPlayerValue(dbusSess, 'Metadata')
        playlist.append(getSongObjectFromTrackMpris2(currentMetadata))
        # tracklist = player.Get('org.mpris.MediaPlayer2.TrackList','Tracks',dbus_interface='org.freedesktop.DBus.Properties')
        # tracklist from clementine is empty ??

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
        url = Track['xesam:url']
        # file:///home/
        retSong.FilePath = urllib.request.url2pathname(url[5:])
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

