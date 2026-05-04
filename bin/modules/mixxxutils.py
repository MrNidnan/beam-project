# -*- encoding: utf-8 -*-
#    Copyright (C) 2014 Mikael Holber http://www.beam-project.com
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
#    Version 1.0
#    	- Initial release
#

import logging
import os
import platform
import sqlite3
from pathlib import Path

from bin.beamsettings import beamSettings
from bin.songclass import SongObject

###############################################################
#
# Define operations
#
###############################################################


MIXXX_ROUTE = 'sqlite'
MIXXX_PLAYLIST_HISTORY = 'history-first'
MIXXX_PLAYLIST_AUTODJ = 'autodj-only'
MIXXX_STATUS_NO_DATABASE = 'No database'
MIXXX_STATUS_STOPPED = 'Stopped'
MIXXX_STATUS_PLAYING = 'Playing'
MIXXX_STATUS_PLAYER_NOT_RUNNING = 'PlayerNotRunning'
MIXXX_STATUS_UNKNOWN = 'Unknown'
MIXXX_DB_FILENAME = 'mixxxdb.sqlite'
MIXXX_STATE_MODEL = 'sqlite-inferred'
MIXXX_SCHEMA_CURRENT = 'current'
MIXXX_SCHEMA_LEGACY = 'legacy-optional-columns-missing'
MIXXX_OPTIONAL_LIBRARY_COLUMNS = ('comment', 'composer', 'album_artist')
MIXXX_REQUIRED_LIBRARY_COLUMNS = ('id', 'artist', 'album', 'title', 'genre', 'year', 'location')


def run(maxtandalength, lastplaylist=None, sqlite_path=None, process_running=None, preferred_paths=None):
    playlist, playback_status, _ = run_with_details(
        maxtandalength,
        lastplaylist,
        sqlite_path=sqlite_path,
        process_running=process_running,
        preferred_paths=preferred_paths,
        emit_debug_log=True,
    )
    return playlist, playback_status


def run_with_details(maxtandalength, lastplaylist=None, sqlite_path=None, process_running=None, preferred_paths=None, emit_debug_log=True):
    _ = lastplaylist

    details = build_mixxx_details(preferred_paths=preferred_paths)

    if process_running is False:
        return finalize_mixxx_result(MIXXX_STATUS_PLAYER_NOT_RUNNING, details, emit_debug_log=emit_debug_log)

    resolved_path, path_source = resolve_mixxx_database_path(sqlite_path, preferred_paths=preferred_paths)
    details['databasePath'] = resolved_path
    details['pathSource'] = path_source

    if resolved_path == '':
        if path_source == 'configured-missing':
            details['error'] = 'Configured Mixxx database path does not exist.'
        elif path_source == 'explicit-missing':
            details['error'] = 'Explicit Mixxx database path does not exist.'
        else:
            details['error'] = 'No Mixxx database file was found in the expected locations.'
        return finalize_mixxx_result(MIXXX_STATUS_NO_DATABASE, details, emit_debug_log=emit_debug_log)

    try:
        sqliteconn = open_mixxx_database(resolved_path)
    except Exception as error:
        logging.debug('Mixxx database open failed: %s', error, exc_info=True)
        details['error'] = str(error)
        return finalize_mixxx_result(MIXXX_STATUS_NO_DATABASE, details, emit_debug_log=emit_debug_log)

    try:
        playlist, playlist_source, schema_details = getplaylist(sqliteconn, maxtandalength)
    except Exception as error:
        logging.debug('Mixxx playlist query failed: %s', error, exc_info=True)
        details['error'] = str(error)
        return finalize_mixxx_result(MIXXX_STATUS_NO_DATABASE, details, emit_debug_log=emit_debug_log)
    finally:
        sqliteconn.close()

    details['playlistSource'] = playlist_source
    details.update(schema_details)
    details['metadataSource'] = describe_mixxx_metadata_source(playlist_source)
    if playlist:
        apply_mixxx_diagnostics_to_playlist(playlist, details)
        return finalize_mixxx_result(MIXXX_STATUS_PLAYING, details, playlist=playlist, emit_debug_log=emit_debug_log)

    details['metadataSource'] = 'No current Mixxx playlist rows'
    return finalize_mixxx_result(MIXXX_STATUS_UNKNOWN, details, emit_debug_log=emit_debug_log)


# Static for skipping refresh until next normal switch when the playlist got modified by hand
run.currentmod = False
run.lastMixxxPlaylist = None



###############################################################
#
# Full read - Player specific
#
###############################################################

def getplaylist(sqliteconn, maxtandalength):
    new_playlist = []
    playlist_source = ''
    schema_details = inspect_mixxx_schema(sqliteconn)

    playlist_sql = build_mixxx_playlist_sql(schema_details)

    cursor = sqliteconn.cursor()
    try:
        cursor.execute(playlist_sql)

        curr_track_arr = cursor.fetchmany(maxtandalength + 2)
        # if not empty and at least the last one in the history
        if len(curr_track_arr) > 0 and curr_track_arr[0]['playlist_pos'] == 1:
            if curr_track_arr[0]['playlist_hidden'] == 2:
                playlist_source = MIXXX_PLAYLIST_HISTORY
            else:
                playlist_source = MIXXX_PLAYLIST_AUTODJ

            for curr_track in curr_track_arr:
                playlist_song = SongObject()

                playlist_song.Artist = curr_track['artist']
                playlist_song.Album = curr_track['album']
                playlist_song.Title = curr_track['title']
                playlist_song.Genre = curr_track['genre']
                playlist_song.Comment = curr_track['comment']
                playlist_song.Composer = curr_track['composer']
                playlist_song.Year = curr_track['year']
                # playlist_song._Singer Defined by beam
                playlist_song.AlbumArtist = curr_track['album_artist']
                # playlist_song.IsCortina   Defined by beam
                playlist_song.FilePath = curr_track['file_path']

                # for compare of changes
                playlist_song.sanitizeFields()

                new_playlist.append(playlist_song)

    finally:
        cursor.close()

    return new_playlist, playlist_source, schema_details


def log_mixxx_poll_result(details):
    logging.debug(
        'Mixxx poll route=%s status=%s pathSource=%s databasePath=%s playlistSource=%s metadataSource=%s stateModel=%s schemaFlavor=%s',
        details.get('route', ''),
        details.get('status', ''),
        details.get('pathSource', ''),
        details.get('databasePath', ''),
        details.get('playlistSource', ''),
        details.get('metadataSource', ''),
        details.get('stateModel', ''),
        details.get('schemaFlavor', ''),
    )


def build_mixxx_details(preferred_paths=None):
    return {
        'route': MIXXX_ROUTE,
        'status': MIXXX_STATUS_STOPPED,
        'databasePath': '',
        'pathSource': '',
        'playlistSource': '',
        'metadataSource': '',
        'stateModel': MIXXX_STATE_MODEL,
        'schemaFlavor': MIXXX_SCHEMA_CURRENT,
        'schemaMissingColumns': [],
        'candidatePaths': get_mixxx_database_candidates(preferred_paths=preferred_paths),
    }


def finalize_mixxx_result(status, details, playlist=None, emit_debug_log=True):
    details['status'] = status
    if emit_debug_log:
        log_mixxx_poll_result(details)
    return playlist or [], status, details


def get_configured_mixxx_database_path():
    if not hasattr(beamSettings, '_beamConfigData'):
        return ''

    path_getter = getattr(beamSettings, 'getMixxxDatabasePath', None)
    if callable(path_getter):
        return normalize_mixxx_path(path_getter())
    return ''


def resolve_mixxx_database_path(explicit_path=None, preferred_paths=None):
    normalized_explicit_path = normalize_mixxx_path(explicit_path)
    if normalized_explicit_path:
        if os.path.isfile(normalized_explicit_path):
            return normalized_explicit_path, 'explicit'
        return '', 'explicit-missing'

    configured_path = get_configured_mixxx_database_path()
    if configured_path:
        if os.path.isfile(configured_path):
            return configured_path, 'configured'
        return '', 'configured-missing'

    for candidate_path in get_mixxx_database_candidates(preferred_paths=preferred_paths):
        if os.path.isfile(candidate_path):
            path_source = 'auto'
            if preferred_paths and candidate_path in [normalize_mixxx_path(path) for path in preferred_paths if normalize_mixxx_path(path)]:
                path_source = 'default'
            return candidate_path, path_source

    return '', 'auto'


def get_mixxx_database_candidates(preferred_paths=None):
    candidate_paths = []
    home_directory = os.path.expanduser('~')

    for preferred_path in preferred_paths or []:
        normalized_preferred_path = normalize_mixxx_path(preferred_path)
        if normalized_preferred_path and normalized_preferred_path not in candidate_paths:
            candidate_paths.append(normalized_preferred_path)

    if platform.system() == 'Windows':
        local_app_data = os.environ.get('LOCALAPPDATA', '').strip()
        roaming_app_data = os.environ.get('APPDATA', '').strip()
        if local_app_data:
            candidate_paths.append(os.path.join(local_app_data, 'Mixxx', MIXXX_DB_FILENAME))
        if roaming_app_data:
            candidate_paths.append(os.path.join(roaming_app_data, 'Mixxx', MIXXX_DB_FILENAME))
        candidate_paths.append(os.path.join(home_directory, 'AppData', 'Local', 'Mixxx', MIXXX_DB_FILENAME))
    elif platform.system() == 'Darwin':
        candidate_paths.append(os.path.join(home_directory, 'Library', 'Application Support', 'Mixxx', MIXXX_DB_FILENAME))
        candidate_paths.append(os.path.join(home_directory, 'Library', 'Containers', 'org.mixxx.mixxx', 'Data', 'Library', 'Application Support', 'Mixxx', MIXXX_DB_FILENAME))
    else:
        candidate_paths.append(os.path.join(home_directory, '.mixxx', MIXXX_DB_FILENAME))
        candidate_paths.append(os.path.join(home_directory, '.local', 'share', 'mixxx', MIXXX_DB_FILENAME))

    normalized_candidates = []
    for candidate_path in candidate_paths:
        normalized_candidate = normalize_mixxx_path(candidate_path)
        if normalized_candidate and normalized_candidate not in normalized_candidates:
            normalized_candidates.append(normalized_candidate)

    return normalized_candidates


def normalize_mixxx_path(path):
    normalized_path = str(path or '').strip()
    if normalized_path == '':
        return ''

    return os.path.normpath(os.path.expandvars(os.path.expanduser(normalized_path)))


def open_mixxx_database(sqlite_path):
    database_uri = '{0}?mode=ro'.format(Path(sqlite_path).resolve().as_uri())
    connection = sqlite3.connect(database_uri, uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def inspect_mixxx_schema(sqliteconn):
    library_columns = get_table_columns(sqliteconn, 'library')
    missing_required_columns = [column_name for column_name in MIXXX_REQUIRED_LIBRARY_COLUMNS if column_name not in library_columns]
    if missing_required_columns:
        raise sqlite3.OperationalError('Mixxx library schema is missing required columns: ' + ', '.join(missing_required_columns))

    missing_optional_columns = [column_name for column_name in MIXXX_OPTIONAL_LIBRARY_COLUMNS if column_name not in library_columns]
    schema_flavor = MIXXX_SCHEMA_CURRENT
    if missing_optional_columns:
        schema_flavor = MIXXX_SCHEMA_LEGACY

    return {
        'schemaFlavor': schema_flavor,
        'schemaMissingColumns': missing_optional_columns,
    }


def get_table_columns(sqliteconn, table_name):
    cursor = sqliteconn.cursor()
    try:
        cursor.execute("PRAGMA table_info('{0}')".format(table_name))
        return [row[1] for row in cursor.fetchall()]
    finally:
        cursor.close()


def build_mixxx_playlist_sql(schema_details):
    missing_columns = schema_details.get('schemaMissingColumns', [])
    select_columns = [
        'pl.hidden as playlist_hidden',
        "case pl.hidden when 2 THEN 1 else pt.position+1 end as playlist_pos",
        'li.id as track_id',
        'li.artist as artist',
        'li.album as album',
        'li.title as title',
        'li.genre as genre',
        get_library_column_sql('comment', missing_columns),
        get_library_column_sql('composer', missing_columns),
        'li.year as year',
        get_library_column_sql('album_artist', missing_columns),
        'tl.location as file_path',
    ]

    return (
        'select ' + ', '.join(select_columns) +
        ' from Playlists pl' +
        ' join PlaylistTracks pt ON pt.playlist_id = pl.id' +
        ' join library li ON pt.track_id = li.id' +
        ' join track_locations tl ON tl.id = li.location' +
        ' where (pl.id = (select max(id) from Playlists where hidden = 2)' +
        '        and pt.position = (select max(position) from PlaylistTracks where playlist_id=pl.id)' +
        '       )' +
        '    or (pl.hidden = 1)' +
        ' order by playlist_pos'
    )


def get_library_column_sql(column_name, missing_columns):
    if column_name in missing_columns:
        return "'' as {0}".format(column_name)
    return 'li.{0} as {0}'.format(column_name)


def describe_mixxx_metadata_source(playlist_source):
    if playlist_source == MIXXX_PLAYLIST_HISTORY:
        return 'History row plus Auto DJ queue'
    if playlist_source == MIXXX_PLAYLIST_AUTODJ:
        return 'Auto DJ queue'
    return 'Mixxx sqlite library metadata'


def describe_mixxx_status_message(details, include_database_path=False):
    message_parts = []
    status = details.get('status', '')

    if status == MIXXX_STATUS_PLAYER_NOT_RUNNING:
        message_parts.append('Mixxx player process not running')
    elif status == MIXXX_STATUS_NO_DATABASE:
        message_parts.append('Mixxx database unavailable')
    elif status == MIXXX_STATUS_UNKNOWN:
        message_parts.append('sqlite cannot prove paused or stopped')
    else:
        if details.get('playlistSource') == MIXXX_PLAYLIST_HISTORY:
            message_parts.append('history-first metadata')
        elif details.get('playlistSource') == MIXXX_PLAYLIST_AUTODJ:
            message_parts.append('Auto DJ metadata')

        message_parts.append('playback inferred from sqlite')

    if details.get('pathSource'):
        message_parts.append('path=' + str(details.get('pathSource')))

    if details.get('schemaFlavor') == MIXXX_SCHEMA_LEGACY:
        missing_columns = details.get('schemaMissingColumns', [])
        if missing_columns:
            message_parts.append('legacy schema missing ' + '/'.join(missing_columns))
        else:
            message_parts.append('legacy schema')

    if include_database_path and details.get('databasePath'):
        message_parts.append('db=' + str(details.get('databasePath')))

    if details.get('error'):
        message_parts.append(str(details.get('error')))

    return ', '.join(message_parts)


def apply_mixxx_diagnostics_to_playlist(playlist, details):
    if not playlist:
        return

    playlist[0].ModuleMessage = describe_mixxx_status_message(details)


