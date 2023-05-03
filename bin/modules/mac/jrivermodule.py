#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    Copyright (C) 2022 Hagen Eckert http://www.beam-project.com
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
#    XX/XX/2022 Version 1.0
#       - Initial release
#
# This Python file uses the following encoding: utf-8


import urllib
import xml.etree.ElementTree as ET
from bin.songclass import SongObject



###############################################################
#
# Define operations
#
###############################################################


def run(MaxTandaLength):
    playlist = []
    playbackStatus = ''

    # setup client for JRiver Media Center
    MCWS = "http://localhost:52199/MCWS/v1"

    try:
        # get current player status and play position
        url = MCWS + "/Playback/Info"
        with urllib.request.urlopen(url) as response:
            resp = response.read()
            response.close()

        #xmlData = resp.decode("UTF-8")
        xml = ET.fromstring(resp)
        e = xml.find("Item[@Name='Status']")

        playbackStatus = e.text
        f = xml.find("Item[@Name='PlayingNowPosition']")
        g = xml.find("Item[@Name='PlayingNowTracks']")

        # print(e.text, f.text, g.text)
        minpos = int((f.text))
        # maxpos = int((g.text)) - 1
        # get playlist (only the required fields
        url = MCWS + "/Playback/Playlist?Fields=Artist,Album,Name,Genre,Comment,Year,Album%20Artist,Filename"

        with urllib.request.urlopen(url) as response:
            resp = response.read()
            response.close()

        # header:  < MPL Version = "2.0" Title = "MCWS - Files - 123145321799680" PathSeparator = "/" >
        # value "123145321799680" (example) can change with every readout

        xml = ET.fromstring(resp)

        idx = 0
        for item in xml:
            # drop already played songs
            if (idx >= minpos):
                # tags = {}
                # clear retSong
                retSong = SongObject()
                # check tag names and fill retSong
                for tag in item:
                    name = tag.attrib["Name"]

                    if name == 'Artist':
                        retSong.Artist = tag.text
                    elif name == 'Album':
                        retSong.Album = tag.text
                    elif name == 'Name':
                        retSong.Title = tag.text
                    elif name == 'Genre':
                        retSong.Genre = tag.text
                    elif name == 'Comment':
                        retSong.Comment = tag.text
                    elif name == 'Date (year)':
                        retSong.Year = tag.text
                    elif name == 'Album Artist':
                        retSong.AlbumArtist = tag.text
                    elif name == 'Filename':
                        retSong.Filepath = tag.text

                # add it to playlist
                playlist.append(retSong)
            idx = idx + 1

        return playlist, playbackStatus

    except:
        playlist = []
        playbackStatus = 'unknown'
        return playlist, playbackStatus
