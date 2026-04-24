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
import json
import logging
import os
import urllib.error
import urllib.parse
import urllib.request

from bin.beamsettings import beamSettings
from bin.songclass import SongObject
from bin.modules.win.winutils import applicationrunning


DEFAULT_BEEFWEB_URL = "http://localhost:8880/"
DEFAULT_TIMEOUT_SECONDS = 2.0
_beefweb_warning_logged = False
_beefweb_error_context = {}
BEAM_BEEFWEB_COLUMNS = [
    "[%artist%]",
    "[%album%]",
    "[%title%]",
    "[%genre%]",
    "[%comment%]",
    "[%composer%]",
    "[%date%]",
    "[%album artist%]",
    "[%performer%]",
    "[%path%]",
]

###############################################################
#
# Define operations
#
###############################################################

def run(max_tanda_length):
    global _beefweb_warning_logged

    playlist = []
    playback_status = ''
    
    #
    # Player Status
    #
    if not applicationrunning("foobar2000.exe"):
        playback_status = 'PlayerNotRunning'
        return playlist, playback_status

    try:
        player_state = get_player_state()
        playback_status = map_playback_status(player_state.get('playbackState'))

        if playback_status == 'Stopped':
            _beefweb_warning_logged = False
            return playlist, playback_status

        active_item = player_state.get('activeItem') or {}
        current_song = get_song_from_columns(active_item.get('columns') or [])

        if song_has_metadata(current_song):
            playlist.append(current_song)

        playlist_id = active_item.get('playlistId')
        active_index = active_item.get('index')
        item_count = max(int(max_tanda_length or 1), 1)

        if has_valid_playlist_reference(playlist_id, active_index):
            playlist_items = get_playlist_items(playlist_id, active_index, item_count)
            if playlist_items:
                playlist = playlist_items

        _beefweb_warning_logged = False

    except urllib.error.URLError as error:
        if not _beefweb_warning_logged:
            logging.warning("Foobar2000 is running but %s", describe_beefweb_error(error))
            _beefweb_warning_logged = True
        if playlist:
            playback_status = 'Playing'
        else:
            playback_status = 'BeefwebUnavailable'
    except Exception as error:
        logging.error(error, exc_info=True)
        if playlist:
            playback_status = 'Playing'
        else:
            playback_status = 'BeefwebUnavailable'

    return playlist, playback_status

def get_player_state():
    try:
        response = open_json('/player', {'columns': BEAM_BEEFWEB_COLUMNS})
    except urllib.error.HTTPError as error:
        if error.code != 400:
            raise
        response = open_json('/player')
    return response.get('player') or {}


def get_playlist_items(playlist_id, active_index, item_count):
    playlist_path = '/playlists/{0}/items/{1}:{2}'.format(
        urllib.parse.quote(str(playlist_id), safe=''),
        int(active_index),
        int(item_count),
    )
    response = open_json(playlist_path, {'columns': BEAM_BEEFWEB_COLUMNS})
    items = (((response.get('playlistItems') or {}).get('items')) or [])
    return [get_song_from_columns(item.get('columns') or []) for item in items]


def has_valid_playlist_reference(playlist_id, active_index):
    if playlist_id in (None, ''):
        return False

    try:
        return int(active_index) >= 0
    except (TypeError, ValueError):
        return False


def get_song_from_columns(columns):
    ret_song = SongObject()
    normalized_columns = list(columns) + [''] * (len(BEAM_BEEFWEB_COLUMNS) - len(columns))

    ret_song.Artist = normalized_columns[0]
    ret_song.Album = normalized_columns[1]
    ret_song.Title = normalized_columns[2]
    ret_song.Genre = normalized_columns[3]
    ret_song.Comment = normalized_columns[4]
    ret_song.Composer = normalized_columns[5]
    ret_song.Year = normalized_columns[6]
    ret_song.AlbumArtist = normalized_columns[7]
    ret_song.Performer = normalized_columns[8]
    ret_song.FilePath = normalized_columns[9]

    return ret_song


def song_has_metadata(song):
    return any([
        song.Artist,
        song.Album,
        song.Title,
        song.Genre,
        song.Comment,
        song.Composer,
        song.Year,
        song.AlbumArtist,
        song.Performer,
        song.FilePath,
    ])


def map_playback_status(beefweb_status):
    if beefweb_status == 'playing':
        return 'Playing'
    if beefweb_status == 'paused':
        return 'Paused'
    return 'Stopped'


def open_json(path, query_params=None):
    opener = build_url_opener()
    url = build_api_url(path, query_params)
    request = urllib.request.Request(url, headers={'Accept': 'application/json'})

    try:
        with opener.open(request, timeout=get_beefweb_timeout()) as response:
            payload = response.read().decode('utf-8')
    except urllib.error.HTTPError as error:
        error_context = {'request_url': url, 'response_body': ''}
        try:
            error_context['response_body'] = error.read().decode('utf-8', 'replace')
        except Exception:
            pass
        _beefweb_error_context[id(error)] = error_context
        raise
    except urllib.error.URLError as error:
        _beefweb_error_context[id(error)] = {'request_url': url, 'response_body': ''}
        raise

    return json.loads(payload)


def describe_beefweb_error(error):
    error_context = _beefweb_error_context.pop(id(error), {})
    request_url = error_context.get('request_url')
    if request_url is None:
        request_url = get_beefweb_base_url()

    if isinstance(error, urllib.error.HTTPError):
        reason = getattr(error, 'reason', '')
        summary = 'HTTP {0}'.format(error.code)
        if reason:
            summary = '{0} {1}'.format(summary, reason)

        response_body = error_context.get('response_body', '').strip()
        if response_body:
            return "Beefweb request failed at '{0}': {1}. Response body: {2}".format(
                request_url,
                summary,
                response_body,
            )

        return "Beefweb request failed at '{0}': {1}".format(request_url, summary)

    return "Beefweb request failed at '{0}': {1}".format(request_url, error)


def build_url_opener():
    user = beamSettings.getFoobarBeefwebUser()
    password = beamSettings.getFoobarBeefwebPassword()

    if not user and not password:
        user = os.environ.get('BEAM_BEEFWEB_USER', '')
        password = os.environ.get('BEAM_BEEFWEB_PASSWORD', '')

    if not user and not password:
        return urllib.request.build_opener()

    password_manager = urllib.request.HTTPPasswordMgrWithDefaultRealm()
    password_manager.add_password(None, get_beefweb_base_url(), user, password)
    auth_handler = urllib.request.HTTPBasicAuthHandler(password_manager)
    return urllib.request.build_opener(auth_handler)


def build_api_url(path, query_params=None):
    query_string = ''
    if query_params:
        encoded_params = []
        for key, value in query_params.items():
            if isinstance(value, (list, tuple)):
                value = ','.join([str(item) for item in value])
            encoded_params.append((key, value))
        query_string = urllib.parse.urlencode(encoded_params)

    url = get_beefweb_base_url().rstrip('/') + path
    if query_string:
        url = url + '?' + query_string
    return url


def get_beefweb_base_url():
    configured_url = beamSettings.getFoobarBeefwebUrl()
    if not configured_url:
        configured_url = os.environ.get('BEAM_BEEFWEB_URL', DEFAULT_BEEFWEB_URL)
    parsed_url = urllib.parse.urlsplit(configured_url)
    normalized_path = parsed_url.path.rstrip('/')

    if normalized_path in ('', '/api'):
        normalized_path = '/api'

    return urllib.parse.urlunsplit((
        parsed_url.scheme,
        parsed_url.netloc,
        normalized_path,
        parsed_url.query,
        parsed_url.fragment,
    ))


def get_beefweb_timeout():
    try:
        return float(os.environ.get('BEAM_BEEFWEB_TIMEOUT', DEFAULT_TIMEOUT_SECONDS))
    except ValueError:
        return DEFAULT_TIMEOUT_SECONDS
