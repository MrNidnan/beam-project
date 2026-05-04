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

from mutagen._file import File as mutagen_file

from bin.beamsettings import beamSettings
from bin.songclass import SongObject


DEFAULT_BEEFWEB_URL = "http://localhost:8880/api/"
DEFAULT_TIMEOUT_SECONDS = 2.0
PLAYLIST_LOOKAHEAD_PADDING = 8
PLAYLIST_LOOKAHEAD_LIMIT = 24
_beefweb_warning_logged = False
_beefweb_error_context = {}
_player_state_warning_logged = False
_metadata_fallback_cache = {}
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


def reset_warning_flags():
    global _beefweb_warning_logged, _player_state_warning_logged

    _beefweb_warning_logged = False
    _player_state_warning_logged = False


def append_active_song(playlist, active_item, playback_status):
    current_song = get_song_from_columns(active_item.get('columns') or [])

    if song_has_metadata(current_song):
        playlist.append(current_song)
        return

    if playback_status in ('Playing', 'Paused'):
        logging.debug(
            "Foobar2000 active item contained no Beam metadata columns. playlistId=%s index=%s columns=%s",
            active_item.get('playlistId'),
            active_item.get('index'),
            active_item.get('columns'),
        )


def extend_playlist_from_active_item(playlist, active_item, max_tanda_length):
    playlist_id = active_item.get('playlistId')
    active_index = active_item.get('index')
    item_count = get_playlist_fetch_count(max_tanda_length)

    if not has_valid_playlist_reference(playlist_id, active_index):
        logging.debug(
            "Foobar2000 active item did not provide a valid playlist reference: playlistId=%s index=%s",
            playlist_id,
            active_index,
        )
        return

    playlist_items = get_playlist_items(playlist_id, active_index, item_count)
    if playlist_items:
        playlist[:] = playlist_items
        logging.debug(
            "Foobar2000 playlist items fetched: playlistId=%s index=%s count=%s returned=%s",
            playlist_id,
            active_index,
            item_count,
            len(playlist_items),
        )


def get_playlist_fetch_count(max_tanda_length):
    try:
        base_count = int(max_tanda_length or 1)
    except (TypeError, ValueError):
        base_count = 1

    base_count = max(base_count, 1)
    return min(base_count + PLAYLIST_LOOKAHEAD_PADDING, PLAYLIST_LOOKAHEAD_LIMIT)


def get_active_item(player_state):
    global _player_state_warning_logged

    active_item = player_state.get('activeItem') or {}
    if not active_item and not _player_state_warning_logged:
        logging.warning(
            "Foobar2000 Beefweb returned playbackState=%s but no activeItem. URL=%s",
            player_state.get('playbackState'),
            get_beefweb_base_url(),
        )
        _player_state_warning_logged = True
    return active_item


def get_error_playback_status(playlist):
    if playlist:
        return 'Playing'
    return 'BeefwebUnavailable'


def run(max_tanda_length):
    playlist, playback_status, _ = run_with_details(max_tanda_length, emit_debug_log=True)
    return playlist, playback_status


def run_with_details(max_tanda_length, emit_debug_log=True):
    global _beefweb_warning_logged

    playlist = []
    playback_status = ''
    details = {
        'route': 'beefweb',
        'baseUrl': get_beefweb_base_url(),
        'authMode': describe_auth_mode(),
        'status': '',
        'requestMode': 'player+playlist',
    }

    logging.debug(
        "Foobar2000 run start: url=%s timeout=%s auth=%s max_tanda_length=%s",
        get_beefweb_base_url(),
        get_beefweb_timeout(),
        describe_auth_mode(),
        max_tanda_length,
    )

    try:
        player_state = get_player_state()
        playback_status = map_playback_status(player_state.get('playbackState'))
        logging.debug(
            "Foobar2000 player state: playbackState=%s activeItemKeys=%s",
            player_state.get('playbackState'),
            sorted((player_state.get('activeItem') or {}).keys()),
        )

        if playback_status == 'Stopped':
            reset_warning_flags()
            details['status'] = playback_status
            if emit_debug_log:
                log_foobar_poll_result(details)
            return playlist, playback_status, details

        active_item = get_active_item(player_state)
        details['playbackState'] = str(player_state.get('playbackState') or '')
        details['activePlaylistId'] = str(active_item.get('playlistId') or '')
        details['activeIndex'] = str(active_item.get('index') or '')
        append_active_song(playlist, active_item, playback_status)
        extend_playlist_from_active_item(playlist, active_item, max_tanda_length)
        reset_warning_flags()

    except urllib.error.URLError as error:
        if not _beefweb_warning_logged:
            logging.warning("Foobar2000 Beefweb request failed: %s", describe_beefweb_error(error))
            _beefweb_warning_logged = True
        playback_status = get_error_playback_status(playlist)
        details['error'] = describe_beefweb_error(error)
    except Exception as error:
        logging.error(error, exc_info=True)
        playback_status = get_error_playback_status(playlist)
        details['error'] = str(error)

    details['status'] = playback_status
    if emit_debug_log:
        log_foobar_poll_result(details)
    return playlist, playback_status, details

def get_player_state():
    try:
        response = open_json('/player', {'columns': BEAM_BEEFWEB_COLUMNS})
    except urllib.error.HTTPError as error:
        if error.code != 400:
            raise
        logging.info(
            "Foobar2000 Beefweb /player rejected custom columns with HTTP 400. Retrying without columns. URL=%s",
            get_beefweb_base_url(),
        )
        response = open_json('/player')
    player = response.get('player') or {}
    if not player:
        logging.debug("Foobar2000 Beefweb /player returned no 'player' object: keys=%s", sorted(response.keys()))
    return player


def get_playlist_items(playlist_id, active_index, item_count):
    playlist_path = '/playlists/{0}/items/{1}:{2}'.format(
        urllib.parse.quote(str(playlist_id), safe=''),
        int(active_index),
        int(item_count),
    )
    response = open_json(playlist_path, {'columns': BEAM_BEEFWEB_COLUMNS})
    items = (((response.get('playlistItems') or {}).get('items')) or [])
    if not items:
        logging.debug(
            "Foobar2000 Beefweb playlist slice returned no items: playlistId=%s index=%s count=%s responseKeys=%s",
            playlist_id,
            active_index,
            item_count,
            sorted(response.keys()),
        )
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

    # In case the columns provided by Beefweb are missing metadata, attempt to enrich from file metadata if possible.
    # This can help with certain playlist types that don't support custom columns, or if the user hasn't configured the columns correctly.
    enrich_song_from_file_metadata(ret_song)

    return ret_song


def enrich_song_from_file_metadata(song):
    if not song.FilePath or not song_needs_metadata_fallback(song):
        return song

    metadata = get_file_metadata(song.FilePath)
    if not metadata:
        return song

    apply_missing_song_metadata(song, metadata)
    return song


def song_needs_metadata_fallback(song):
    return not song.Genre


def get_file_metadata(file_path):
    normalized_path = os.path.normcase(os.path.abspath(file_path))
    if normalized_path in _metadata_fallback_cache:
        return _metadata_fallback_cache[normalized_path]

    metadata = {}

    if not os.path.exists(file_path):
        _metadata_fallback_cache[normalized_path] = metadata
        return metadata

    try:
        audio = mutagen_file(file_path, easy=True)
    except Exception as error:
        logging.debug("Foobar2000 metadata fallback failed for '%s': %s", file_path, error, exc_info=True)
        _metadata_fallback_cache[normalized_path] = metadata
        return metadata

    if not audio:
        _metadata_fallback_cache[normalized_path] = metadata
        return metadata

    metadata = {
        'Artist': get_first_metadata_value(audio, 'artist'),
        'Album': get_first_metadata_value(audio, 'album'),
        'Title': get_first_metadata_value(audio, 'title'),
        'Genre': get_first_metadata_value(audio, 'genre'),
        'Comment': get_first_metadata_value(audio, 'comment'),
        'Composer': get_first_metadata_value(audio, 'composer'),
        'Year': get_first_metadata_value(audio, 'date'),
        'AlbumArtist': get_first_metadata_value(audio, 'albumartist'),
        'Performer': get_first_metadata_value(audio, 'performer'),
    }
    _metadata_fallback_cache[normalized_path] = metadata
    return metadata


def get_first_metadata_value(audio, key):
    value = audio.get(key)
    if isinstance(value, list):
        value = value[0] if value else ''

    value = getattr(value, 'value', value)

    if value is None:
        return ''

    return str(value)


def apply_missing_song_metadata(song, metadata):
    for field_name, value in metadata.items():
        if value and not getattr(song, field_name):
            setattr(song, field_name, value)


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
    logging.debug("Foobar2000 Beefweb request: url=%s auth=%s", url, describe_auth_mode())

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

    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        logging.error(
            "Foobar2000 Beefweb returned invalid JSON from '%s'. Payload prefix: %s",
            url,
            payload[:400],
            exc_info=True,
        )
        raise


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


def describe_auth_mode():
    user = beamSettings.getFoobarBeefwebUser()
    password = beamSettings.getFoobarBeefwebPassword()

    if not user and not password:
        user = os.environ.get('BEAM_BEEFWEB_USER', '')
        password = os.environ.get('BEAM_BEEFWEB_PASSWORD', '')

    if user or password:
        return 'basic-auth'
    return 'none'


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


def log_foobar_poll_result(details):
    logging.debug(
        'Foobar2000 poll route=%s status=%s base_url=%s auth=%s active_playlist=%s active_index=%s',
        details.get('route', 'unknown'),
        details.get('status', 'unknown'),
        details.get('baseUrl', ''),
        details.get('authMode', ''),
        details.get('activePlaylistId', ''),
        details.get('activeIndex', ''),
    )
