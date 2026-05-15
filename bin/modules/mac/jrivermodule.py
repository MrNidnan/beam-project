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
import socket
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from bin.beamsettings import beamSettings
from bin.songclass import SongObject

_ZONE_RESOLUTION_CACHE = {}
PLAYLIST_LOOKAHEAD_LIMIT = 64


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


def get_first_non_empty_value(fields, *field_names):
    for field_name in field_names:
        field_value = fields.get(field_name, '')
        if str(field_value).strip() != '':
            return field_value

    return ''


def get_target_zone():
    return beamSettings.getJRiverTargetZone()


def get_playlist_fetch_count(max_tanda_length):
    try:
        base_count = int(max_tanda_length or 1)
    except (TypeError, ValueError):
        base_count = 1

    return max(base_count, 1) + 2


def build_mcws_url(base_url, path, query_params=None):
    encoded_query = urllib.parse.urlencode(query_params or {})
    if encoded_query == '':
        return base_url + path

    return base_url + path + '?' + encoded_query


def fetch_mcws_xml(mcws_base_url, path, query_params=None):
    url = build_mcws_url(mcws_base_url, path, query_params)
    request = urllib.request.Request(url, headers={'Connection': 'close'})

    for _attempt in range(2):
        try:
            with urllib.request.urlopen(request, timeout=2.5) as response:
                payload = response.read()
                response.close()
            return ET.fromstring(payload)
        except (ConnectionResetError, socket.timeout, TimeoutError, OSError) as error:
            if _attempt == 1:
                raise urllib.error.URLError(error)

    raise urllib.error.URLError('Unable to fetch MCWS XML')


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

    if explicit_prefix == 'id':
        return explicit_value or normalized_target_zone

    cache_key = (mcws_base_url, normalized_target_zone)
    cached_zone_id = _ZONE_RESOLUTION_CACHE.get(cache_key)
    if cached_zone_id:
        return cached_zone_id

    zones = read_mcws_zones(mcws_base_url)
    resolved_zone_id = normalized_target_zone

    if explicit_prefix == 'name':
        for zone in zones:
            if zone['name'].lower() == explicit_value.lower():
                resolved_zone_id = zone['id']
                break
        else:
            resolved_zone_id = explicit_value or normalized_target_zone
        _ZONE_RESOLUTION_CACHE[cache_key] = resolved_zone_id
        return resolved_zone_id

    if explicit_prefix == 'index':
        try:
            requested_index = int(explicit_value)
        except ValueError:
            resolved_zone_id = explicit_value or normalized_target_zone
            _ZONE_RESOLUTION_CACHE[cache_key] = resolved_zone_id
            return resolved_zone_id

        if 0 <= requested_index < len(zones):
            resolved_zone_id = zones[requested_index]['id']
        else:
            resolved_zone_id = explicit_value or normalized_target_zone
        _ZONE_RESOLUTION_CACHE[cache_key] = resolved_zone_id
        return resolved_zone_id

    for zone in zones:
        if zone['id'] == normalized_target_zone:
            resolved_zone_id = zone['id']
            _ZONE_RESOLUTION_CACHE[cache_key] = resolved_zone_id
            return resolved_zone_id

    for zone in zones:
        if zone['name'].lower() == normalized_lookup:
            resolved_zone_id = zone['id']
            _ZONE_RESOLUTION_CACHE[cache_key] = resolved_zone_id
            return resolved_zone_id

    try:
        requested_zone_number = int(normalized_target_zone)
    except ValueError:
        _ZONE_RESOLUTION_CACHE[cache_key] = resolved_zone_id
        return resolved_zone_id

    if 1 <= requested_zone_number <= len(zones):
        resolved_zone_id = zones[requested_zone_number - 1]['id']
        _ZONE_RESOLUTION_CACHE[cache_key] = resolved_zone_id
        return resolved_zone_id

    if 0 <= requested_zone_number < len(zones):
        resolved_zone_id = zones[requested_zone_number]['id']
        _ZONE_RESOLUTION_CACHE[cache_key] = resolved_zone_id
        return resolved_zone_id

    _ZONE_RESOLUTION_CACHE[cache_key] = resolved_zone_id
    return resolved_zone_id


def populate_song_from_fields(song, fields):
    song.Artist = fields.get('Artist', '')
    song.Album = fields.get('Album', '')
    song.Title = fields.get('Name', '')
    song.Genre = fields.get('Genre', '')
    song.Comment = fields.get('Comment', '')
    song.Year = fields.get('Date (year)', fields.get('Year', ''))
    song.Singer = get_first_non_empty_value(fields, 'Original Singer', 'Singer')
    song.AlbumArtist = fields.get('Album Artist', '')
    song.FilePath = fields.get('Filename', '')
    song.Composer = fields.get('Composer', '')
    return song


def _annotate_current_song_since_last_cortina(playlist, previous_songs):
    if not playlist:
        return playlist

    rules = beamSettings.getRules()
    current_song = playlist[0]
    current_song.applySongRules(rules)
    if current_song.IsCortina == 'yes':
        current_song.SinceLastCortinaCountOverride = 0
        return playlist

    since_last_cortina_count = 1

    for previous_song in reversed(previous_songs):
        previous_song.applySongRules(rules)
        if previous_song.IsCortina == 'yes':
            break
        since_last_cortina_count = since_last_cortina_count + 1

    current_song.SinceLastCortinaCountOverride = since_last_cortina_count
    return playlist


def _has_next_tanda_boundary(playlist):
    if len(playlist) < 2:
        return False

    rules = beamSettings.getRules()
    current_song = playlist[0]
    current_song.applySongRules(rules)
    seen_cortina = current_song.IsCortina == 'yes'

    for song in playlist[1:]:
        song.applySongRules(rules)
        if not seen_cortina:
            if song.IsCortina == 'yes':
                seen_cortina = True
            continue

        if song.IsCortina != 'yes':
            return True

    return False


def read_playlist_from_xml(xml_root, minpos, max_tanda_length):
    playlist = []
    min_items = get_playlist_fetch_count(max_tanda_length)
    previous_songs = []

    for idx, item in enumerate(xml_root):
        fields = {}
        for tag in item:
            fields[tag.attrib.get('Name', '')] = get_xml_text(tag)

        song = populate_song_from_fields(SongObject(), fields)

        if idx < minpos:
            previous_songs.append(song)
            continue

        playlist.append(song)

        if len(playlist) >= PLAYLIST_LOOKAHEAD_LIMIT:
            break

        if len(playlist) >= min_items and _has_next_tanda_boundary(playlist):
            break

    return _annotate_current_song_since_last_cortina(playlist, previous_songs)


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
                'Fields': 'Artist,Album,Name,Genre,Composer,Comment,Year,Original Singer,Singer,Album Artist,Filename',
            }
        )

        # header:  < MPL Version = "2.0" Title = "MCWS - Files - 123145321799680" PathSeparator = "/" >
        # value "123145321799680" (example) can change with every readout

        playlist = read_playlist_from_xml(xml, minpos, MaxTandaLength)

        return playlist, playbackStatus

    except urllib.error.URLError:
        playlist = []
        playbackStatus = 'PlayerNotRunning'
        return playlist, playbackStatus
    except (AttributeError, TypeError, ValueError, ET.ParseError):
        playlist = []
        playbackStatus = 'Unknown'
        return playlist, playbackStatus
