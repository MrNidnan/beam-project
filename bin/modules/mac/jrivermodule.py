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
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from bin.beamsettings import beamSettings
from bin.songclass import SongObject



###############################################################
#
# Define operations
#
###############################################################


def get_playback_status(xml_root):
    state_item = xml_root.find("Item[@Name='State']")
    if state_item is not None and state_item.text is not None:
        state_value = state_item.text.strip()
        if state_value == '0':
            return 'Stopped'
        if state_value == '1':
            return 'Paused'
        if state_value == '2':
            return 'Playing'
        return 'Unknown'

    status_item = xml_root.find("Item[@Name='Status']")
    if status_item is None or status_item.text is None:
        return 'Unknown'

    status_value = status_item.text.strip().lower()
    if status_value == 'playing':
        return 'Playing'
    if status_value == 'paused':
        return 'Paused'
    if status_value == 'stopped':
        return 'Stopped'

    return 'Unknown'


def get_xml_text(node, default=''):
    if node is None or node.text is None:
        return default

    return node.text


def get_target_zone():
    return beamSettings.getJRiverTargetZone()


def build_mcws_url(base_url, path, query_params=None):
    encoded_query = urllib.parse.urlencode(query_params or {})
    if encoded_query == '':
        return base_url + path

    return base_url + path + '?' + encoded_query


def fetch_mcws_xml(mcws_base_url, path, query_params=None):
    url = build_mcws_url(mcws_base_url, path, query_params)
    with urllib.request.urlopen(url) as response:
        payload = response.read()
        response.close()

    return ET.fromstring(payload)


def read_mcws_zones(mcws_base_url):
    zones_xml = fetch_mcws_xml(mcws_base_url, "/Playback/Zones")
    zones_by_index = {}

    for item in zones_xml.findall('Item'):
        item_name = item.attrib.get('Name', '')
        if item_name.startswith('ZoneID'):
            zone_index = item_name[len('ZoneID'):]
            zone_entry = zones_by_index.setdefault(zone_index, {})
            zone_entry['id'] = get_xml_text(item).strip()
        elif item_name.startswith('ZoneName'):
            zone_index = item_name[len('ZoneName'):]
            zone_entry = zones_by_index.setdefault(zone_index, {})
            zone_entry['name'] = get_xml_text(item).strip()

    ordered_zone_indexes = sorted(
        zones_by_index.keys(),
        key=lambda zone_index: int(zone_index) if zone_index.isdigit() else zone_index,
    )

    zones = []
    for zone_index in ordered_zone_indexes:
        zone_entry = zones_by_index[zone_index]
        zone_id = zone_entry.get('id', '').strip()
        if zone_id == '':
            continue
        zones.append({
            'index': zone_index,
            'id': zone_id,
            'name': zone_entry.get('name', '').strip(),
        })

    return zones


def resolve_mcws_target_zone(mcws_base_url, target_zone):
    normalized_target_zone = str(target_zone).strip()
    if normalized_target_zone in ('', '-1'):
        return '-1'

    normalized_lookup = normalized_target_zone.lower()
    explicit_prefix, separator, explicit_value = normalized_target_zone.partition(':')
    if separator:
        explicit_prefix = explicit_prefix.strip().lower()
        explicit_value = explicit_value.strip()
    else:
        explicit_prefix = ''
        explicit_value = normalized_target_zone

    zones = read_mcws_zones(mcws_base_url)
    if explicit_prefix == 'id':
        return explicit_value or normalized_target_zone

    if explicit_prefix == 'name':
        for zone in zones:
            if zone['name'].lower() == explicit_value.lower():
                return zone['id']
        return explicit_value or normalized_target_zone

    if explicit_prefix == 'index':
        try:
            requested_index = int(explicit_value)
        except ValueError:
            return explicit_value or normalized_target_zone

        if 0 <= requested_index < len(zones):
            return zones[requested_index]['id']
        return explicit_value or normalized_target_zone

    for zone in zones:
        if zone['id'] == normalized_target_zone:
            return zone['id']

    for zone in zones:
        if zone['name'].lower() == normalized_lookup:
            return zone['id']

    try:
        requested_zone_number = int(normalized_target_zone)
    except ValueError:
        return normalized_target_zone

    if 1 <= requested_zone_number <= len(zones):
        return zones[requested_zone_number - 1]['id']

    if 0 <= requested_zone_number < len(zones):
        return zones[requested_zone_number]['id']

    return normalized_target_zone


def run(MaxTandaLength):
    playlist = []
    playbackStatus = ''

    # setup client for JRiver Media Center
    MCWS = "http://localhost:52199/MCWS/v1"
    target_zone = resolve_mcws_target_zone(MCWS, get_target_zone())

    try:
        # get current player status and play position
        xml = fetch_mcws_xml(MCWS, "/Playback/Info", {'Zone': target_zone})
        playbackStatus = get_playback_status(xml)
        f = xml.find("Item[@Name='PlayingNowPosition']")

        minpos = int(get_xml_text(f, '0'))
        # maxpos = int((g.text)) - 1
        # get playlist (only the required fields
        xml = fetch_mcws_xml(
            MCWS,
            "/Playback/Playlist",
            {
                'Zone': target_zone,
                'Fields': 'Artist,Album,Name,Genre,Comment,Year,Album Artist,Filename',
            }
        )

        # header:  < MPL Version = "2.0" Title = "MCWS - Files - 123145321799680" PathSeparator = "/" >
        # value "123145321799680" (example) can change with every readout

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
                    value = get_xml_text(tag)

                    if name == 'Artist':
                        retSong.Artist = value
                    elif name == 'Album':
                        retSong.Album = value
                    elif name == 'Name':
                        retSong.Title = value
                    elif name == 'Genre':
                        retSong.Genre = value
                    elif name == 'Comment':
                        retSong.Comment = value
                    elif name == 'Date (year)':
                        retSong.Year = value
                    elif name == 'Album Artist':
                        retSong.AlbumArtist = value
                    elif name == 'Filename':
                        retSong.FilePath = value

                # add it to playlist
                playlist.append(retSong)
            idx = idx + 1

        return playlist, playbackStatus

    except urllib.error.URLError:
        playlist = []
        playbackStatus = 'PlayerNotRunning'
        return playlist, playbackStatus
    except (AttributeError, TypeError, ValueError, ET.ParseError):
        playlist = []
        playbackStatus = 'Unknown'
        return playlist, playbackStatus
