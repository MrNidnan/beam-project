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
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from bin.beamsettings import beamSettings
from bin.songclass import SongObject

try:
    import pythoncom
    import win32com.client
except ImportError:
    pythoncom = None
    win32com = None
from bin.modules.win.winutils import applicationrunning

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


def populate_song_from_fields(song, fields):
    song.Artist = fields.get('Artist', '')
    song.Album = fields.get('Album', '')
    song.Title = fields.get('Name', '')
    song.Genre = fields.get('Genre', '')
    song.Comment = fields.get('Comment', '')
    song.Year = fields.get('Date (year)', fields.get('Year', ''))
    song.AlbumArtist = fields.get('Album Artist', '')
    song.FilePath = fields.get('Filename', '')
    return song


def read_playlist_from_xml(xml_root, minpos):
    playlist = []

    for idx, item in enumerate(xml_root):
        if idx < minpos:
            continue

        fields = {}
        for tag in item:
            fields[tag.attrib.get('Name', '')] = get_xml_text(tag)

        playlist.append(populate_song_from_fields(SongObject(), fields))

    return playlist


def call_with_optional_zone(target, method_name, target_zone):
    method = getattr(target, method_name)
    if str(target_zone).strip() in ('', '-1'):
        return method()

    zone_candidates = []
    try:
        zone_candidates.append(int(str(target_zone).strip()))
    except ValueError:
        pass
    zone_candidates.append(str(target_zone).strip())

    for zone_candidate in zone_candidates:
        try:
            return method(zone_candidate)
        except TypeError:
            break
        except Exception:
            continue

    return method()


def is_jriver_running():
    for process_hint in ('Media Center', 'JRiver'):
        if applicationrunning(process_hint):
            return True

    return False


def run_with_mcws(target_zone):
    mcws_base_url = "http://localhost:52199/MCWS/v1"
    resolved_target_zone = resolve_mcws_target_zone(mcws_base_url, target_zone)
    info_xml = fetch_mcws_xml(mcws_base_url, "/Playback/Info", {'Zone': resolved_target_zone})
    playback_status = get_playback_status(info_xml)
    minpos = int(get_xml_text(info_xml.find("Item[@Name='PlayingNowPosition']"), '0'))

    playlist_xml = fetch_mcws_xml(
        mcws_base_url,
        "/Playback/Playlist",
        {
            'Zone': resolved_target_zone,
            'Fields': 'Artist,Album,Name,Genre,Comment,Year,Album Artist,Filename',
        }
    )
    playlist = read_playlist_from_xml(playlist_xml, minpos)
    return playlist, playback_status


def run_with_com(target_zone):
    if pythoncom is None or win32com is None:
        raise ImportError()

    playlist = []
    pythoncom.CoInitialize()
    try:
        mjautomation = win32com.client.Dispatch("MediaJukebox Application")

        mjplayback = call_with_optional_zone(mjautomation, 'GetPlayback', target_zone)
        mjstate = getattr(mjplayback, 'State', None)

        if mjstate == 0:
            playback_status = 'Stopped'
        elif mjstate == 1:
            playback_status = 'Paused'
        elif mjstate == 2:
            playback_status = 'Playing'
            mjplaylist = call_with_optional_zone(mjautomation, 'GetCurPlaylist', target_zone)
            minpos = int(getattr(mjplaylist, 'Position', 0))
            maxpos = int(mjplaylist.GetNumberFiles())
            for songpos in range(minpos, maxpos):
                playlist.append(getSongAt(mjplaylist, songpos))
        else:
            playback_status = 'Unknown'
    finally:
        pythoncom.CoUninitialize()

    return playlist, playback_status

def run(_max_tanda_length):
    target_zone = get_target_zone()
    try:
        return run_with_mcws(target_zone)
    except urllib.error.URLError:
        pass
    except (AttributeError, TypeError, ValueError, ET.ParseError):
        return [], 'Unknown'

    if str(target_zone).strip() not in ('', '-1'):
        if is_jriver_running():
            return [], 'Unknown'
        return [], 'PlayerNotRunning'

    try:
        return run_with_com(target_zone)
    except ImportError:
        pass
    except Exception:
        if is_jriver_running():
            return [], 'Unknown'

    if is_jriver_running():
        return [], 'Unknown'

    return [], 'PlayerNotRunning'

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
