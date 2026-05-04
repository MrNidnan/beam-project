#!/usr/bin/env python

import os
import sqlite3
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


MIXXX_DB_FILENAME = 'mixxxdb.sqlite'
PRIMARY_ARTIST = 'Ricardo Tanturi'
SECONDARY_ARTIST = 'Carlos Di Sarli'
PRIMARY_PATH = r'C:\Music\Ricardo Tanturi\Una Emocion.flac'
SECONDARY_PATH = r'C:\Music\Carlos Di Sarli\Bahia Blanca.flac'


def create_fixture_database(sqlite_path, schema_variant='current', include_playlist_rows=True):
    connection = sqlite3.connect(sqlite_path)

    try:
        cursor = connection.cursor()
        cursor.execute('create table Playlists (id integer primary key, hidden integer not null)')
        cursor.execute('create table PlaylistTracks (playlist_id integer not null, position integer not null, track_id integer not null)')
        if schema_variant == 'legacy':
            cursor.execute(
                'create table library ('
                'id integer primary key, '
                'artist text, '
                'album text, '
                'title text, '
                'genre text, '
                'year text, '
                'location integer not null'
                ')'
            )
        elif schema_variant == 'broken':
            cursor.execute(
                'create table library ('
                'id integer primary key, '
                'artist text, '
                'album text, '
                'genre text, '
                'comment text, '
                'composer text, '
                'year text'
                ')'
            )
        else:
            cursor.execute(
                'create table library ('
                'id integer primary key, '
                'artist text, '
                'album text, '
                'title text, '
                'genre text, '
                'comment text, '
                'composer text, '
                'year text, '
                'album_artist text, '
                'location integer not null'
                ')'
            )
        cursor.execute('create table track_locations (id integer primary key, location text not null)')

        cursor.execute('insert into track_locations (id, location) values (?, ?)', (1, PRIMARY_PATH))
        cursor.execute('insert into track_locations (id, location) values (?, ?)', (2, SECONDARY_PATH))

        if schema_variant == 'legacy':
            cursor.execute(
                'insert into library (id, artist, album, title, genre, year, location) '
                'values (?, ?, ?, ?, ?, ?, ?)',
                (1, PRIMARY_ARTIST, '1942', 'Una Emocion', 'Tango', '1942', 1),
            )
            cursor.execute(
                'insert into library (id, artist, album, title, genre, year, location) '
                'values (?, ?, ?, ?, ?, ?, ?)',
                (2, SECONDARY_ARTIST, '1957', 'Bahia Blanca', 'Tango', '1957', 2),
            )
        elif schema_variant == 'broken':
            cursor.execute(
                'insert into library (id, artist, album, genre, comment, composer, year) '
                'values (?, ?, ?, ?, ?, ?, ?)',
                (1, PRIMARY_ARTIST, '1942', 'Tango', 'Broken schema', 'Tanturi', '1942'),
            )
            cursor.execute(
                'insert into library (id, artist, album, genre, comment, composer, year) '
                'values (?, ?, ?, ?, ?, ?, ?)',
                (2, SECONDARY_ARTIST, '1957', 'Tango', 'Broken schema', 'Di Sarli', '1957'),
            )
        else:
            cursor.execute(
                'insert into library (id, artist, album, title, genre, comment, composer, year, album_artist, location) '
                'values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (1, PRIMARY_ARTIST, '1942', 'Una Emocion', 'Tango', 'History entry', 'Tanturi', '1942', PRIMARY_ARTIST, 1),
            )
            cursor.execute(
                'insert into library (id, artist, album, title, genre, comment, composer, year, album_artist, location) '
                'values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (2, SECONDARY_ARTIST, '1957', 'Bahia Blanca', 'Tango', 'Auto DJ', 'Di Sarli', '1957', SECONDARY_ARTIST, 2),
            )

        if include_playlist_rows:
            cursor.execute('insert into Playlists (id, hidden) values (?, ?)', (10, 2))
            cursor.execute('insert into Playlists (id, hidden) values (?, ?)', (11, 1))
            cursor.execute('insert into PlaylistTracks (playlist_id, position, track_id) values (?, ?, ?)', (10, 0, 1))
            cursor.execute('insert into PlaylistTracks (playlist_id, position, track_id) values (?, ?, ?)', (11, 0, 2))

        connection.commit()
    finally:
        connection.close()


def assert_platform_candidates(mixxxutils, temp_home):
    with patch('platform.system', return_value='Windows'):
        with patch.dict(os.environ, {'LOCALAPPDATA': str(Path(temp_home) / 'win-local'), 'APPDATA': str(Path(temp_home) / 'win-roaming')}, clear=False):
            candidates = mixxxutils.get_mixxx_database_candidates()
            assert str(Path(temp_home) / 'win-local' / 'Mixxx' / MIXXX_DB_FILENAME) in candidates
            assert str(Path(temp_home) / 'win-roaming' / 'Mixxx' / MIXXX_DB_FILENAME) in candidates

    with patch('platform.system', return_value='Darwin'):
        candidates = mixxxutils.get_mixxx_database_candidates()
        assert str(Path(temp_home) / 'Library' / 'Application Support' / 'Mixxx' / MIXXX_DB_FILENAME) in candidates
        assert str(Path(temp_home) / 'Library' / 'Containers' / 'org.mixxx.mixxx' / 'Data' / 'Library' / 'Application Support' / 'Mixxx' / MIXXX_DB_FILENAME) in candidates

    with patch('platform.system', return_value='Linux'):
        candidates = mixxxutils.get_mixxx_database_candidates()
        assert str(Path(temp_home) / '.mixxx' / MIXXX_DB_FILENAME) in candidates
        assert str(Path(temp_home) / '.local' / 'share' / 'mixxx' / MIXXX_DB_FILENAME) in candidates


def assert_now_playing_status_flow(auto_db_path):
    from bin.beamsettings import beamSettings
    from bin.nowplayingdata import NowPlayingData

    config_data = beamSettings.loadConfigData(beamSettings.getDefaultConfigFilePath())
    config_data['Module'] = 'Mixxx'
    Path(beamSettings.getBeamConfigFilePath()).parent.mkdir(parents=True, exist_ok=True)
    beamSettings.dumpConfigData(beamSettings.getBeamConfigFilePath(), config_data)
    beamSettings.loadConfig()
    beamSettings.setSelectedModuleName('Mixxx')
    beamSettings.setMixxxDatabasePath(str(auto_db_path))

    now_playing = NowPlayingData()

    if sys.platform.startswith('win'):
        with patch('bin.modules.win.winutils.applicationrunning', return_value=True):
            now_playing.readData(beamSettings)
    else:
        now_playing.readData(beamSettings)

    assert now_playing.PlaybackStatus == 'Playing'
    assert now_playing.currentPlaylist[0].ModuleMessage != ''
    assert 'playback inferred from sqlite' in now_playing.currentPlaylist[0].ModuleMessage
    assert 'history-first metadata' in now_playing.StatusMessage


def main():
    temp_home = tempfile.mkdtemp(prefix='beam-mixxx-smoke-')
    os.environ['HOME'] = temp_home
    os.environ['USERPROFILE'] = temp_home
    os.environ['LOCALAPPDATA'] = temp_home
    os.environ['APPDATA'] = temp_home

    from bin.modules import mixxxutils

    auto_candidates = mixxxutils.get_mixxx_database_candidates()
    assert auto_candidates, 'Expected at least one Mixxx database auto-detection candidate'

    auto_db_path = Path(auto_candidates[0])
    auto_db_path.parent.mkdir(parents=True, exist_ok=True)
    create_fixture_database(str(auto_db_path))

    playlist, status, details = mixxxutils.run_with_details(4, emit_debug_log=False)

    assert status == 'Playing'
    assert details['route'] == 'sqlite'
    assert details['pathSource'] == 'auto'
    assert details['databasePath'] == str(auto_db_path)
    assert details['playlistSource'] == 'history-first'
    assert details['metadataSource'] == 'History row plus Auto DJ queue'
    assert details['stateModel'] == 'sqlite-inferred'
    assert details['schemaFlavor'] == 'current'
    assert len(playlist) == 2
    assert playlist[0].Artist == PRIMARY_ARTIST
    assert playlist[0].Title == 'Una Emocion'
    assert playlist[0].FilePath == PRIMARY_PATH
    assert 'history-first metadata' in playlist[0].ModuleMessage
    assert playlist[1].Artist == SECONDARY_ARTIST

    explicit_db_path = Path(temp_home) / 'custom' / MIXXX_DB_FILENAME
    explicit_db_path.parent.mkdir(parents=True, exist_ok=True)
    create_fixture_database(str(explicit_db_path))

    playlist, status, details = mixxxutils.run_with_details(4, sqlite_path=str(explicit_db_path), emit_debug_log=False)

    assert status == 'Playing'
    assert details['pathSource'] == 'explicit'
    assert details['databasePath'] == str(explicit_db_path)
    assert playlist[0].Artist == PRIMARY_ARTIST

    legacy_db_path = Path(temp_home) / 'legacy' / MIXXX_DB_FILENAME
    legacy_db_path.parent.mkdir(parents=True, exist_ok=True)
    create_fixture_database(str(legacy_db_path), schema_variant='legacy')

    playlist, status, details = mixxxutils.run_with_details(4, sqlite_path=str(legacy_db_path), emit_debug_log=False)

    assert status == 'Playing'
    assert details['schemaFlavor'] == 'legacy-optional-columns-missing'
    assert details['schemaMissingColumns'] == ['comment', 'composer', 'album_artist']
    assert playlist[0].Comment == ''
    assert playlist[0].Composer == ''
    assert playlist[0].AlbumArtist == ''

    broken_db_path = Path(temp_home) / 'broken' / MIXXX_DB_FILENAME
    broken_db_path.parent.mkdir(parents=True, exist_ok=True)
    create_fixture_database(str(broken_db_path), schema_variant='broken')

    playlist, status, details = mixxxutils.run_with_details(4, sqlite_path=str(broken_db_path), emit_debug_log=False)

    assert status == 'No database'
    assert playlist == []
    assert 'missing required columns' in details['error']
    assert 'title' in details['error']
    assert 'location' in details['error']
    assert 'database unavailable' in mixxxutils.describe_mixxx_status_message(details)

    unknown_db_path = Path(temp_home) / 'unknown' / MIXXX_DB_FILENAME
    unknown_db_path.parent.mkdir(parents=True, exist_ok=True)
    create_fixture_database(str(unknown_db_path), include_playlist_rows=False)

    playlist, status, details = mixxxutils.run_with_details(4, sqlite_path=str(unknown_db_path), emit_debug_log=False)

    assert status == 'Unknown'
    assert playlist == []
    assert 'cannot prove paused or stopped' in mixxxutils.describe_mixxx_status_message(details)

    playlist, status, details = mixxxutils.run_with_details(4, process_running=False, emit_debug_log=False)

    assert status == 'PlayerNotRunning'
    assert playlist == []
    assert details['status'] == 'PlayerNotRunning'

    missing_db_path = Path(temp_home) / 'missing' / MIXXX_DB_FILENAME
    playlist, status, details = mixxxutils.run_with_details(4, sqlite_path=str(missing_db_path), emit_debug_log=False)

    assert status == 'No database'
    assert playlist == []
    assert details['pathSource'] == 'explicit-missing'

    assert_platform_candidates(mixxxutils, temp_home)
    assert_now_playing_status_flow(auto_db_path)

    print('Mixxx smoke test passed')


if __name__ == '__main__':
    main()