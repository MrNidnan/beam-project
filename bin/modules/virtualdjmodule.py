import logging
import os
import platform
import re
import time
import urllib.error
import urllib.parse
import urllib.request

from bin.beamsettings import beamSettings
from bin.songclass import SongObject


DEFAULT_VIRTUALDJ_INTEGRATION_MODE = 'History File'
HYBRID_VIRTUALDJ_INTEGRATION_MODE = 'Auto (Network -> History)'
DEFAULT_VIRTUALDJ_HOST = '127.0.0.1'
DEFAULT_VIRTUALDJ_PORT = 80
DEFAULT_VIRTUALDJ_QUERY_MODE = 'Master'
DEFAULT_VIRTUALDJ_HISTORY_DECK = 'Deck 1'
ANY_VIRTUALDJ_HISTORY_DECK = '-1'
DEFAULT_VIRTUALDJ_RECENT_TRACK_WINDOW = 300
QUERY_ENDPOINT = '/query'
TIMESTAMP_PREFIX_RE = re.compile(r'^\d{1,2}:\d{2}(?::\d{2})?\s*:\s*')
HISTORY_DECK_PREFIX_RE = re.compile(r'^deck\s*=\s*(\d+)\s+(.*)$', re.IGNORECASE)
HISTORY_FIELD_RE = re.compile(r'(?<!\S)([A-Za-z_]\w*)=')
HISTORY_FILE_ENCODINGS = ('utf-8-sig', 'utf-8', 'cp1252', 'latin-1')
QUERY_MODE_TARGETS = {
    'Master': 'deck master',
    'Deck 1': 'deck 1',
    'Deck 2': 'deck 2',
    'Left': 'deck left',
    'Right': 'deck right',
}
HISTORY_DECK_TARGETS = {
    ANY_VIRTUALDJ_HISTORY_DECK: ANY_VIRTUALDJ_HISTORY_DECK,
    DEFAULT_VIRTUALDJ_HISTORY_DECK: '1',
    'Deck 2': '2',
}
FIELD_SCRIPT_TEMPLATES = {
    'Artist': "{target} get_loaded_song 'artist'",
    'Title': "{target} get_loaded_song 'title'",
    'Album': "{target} get_loaded_song 'album'",
    'Genre': "{target} get_loaded_song 'genre'",
    'Year': "{target} get_loaded_song 'year'",
    'FilePath': "{target} get_loaded_song 'filepath'",
}
PLAYING_SCRIPT_TEMPLATE = "{target} is_audible ? {target} get_artist_title : get_text ''"
METADATA_SCRIPT_TEMPLATE = (
    '{target} get_text "artist=`{target} get_loaded_song \'artist\'`\\n'
    'title=`{target} get_loaded_song \'title\'`\\n'
    'album=`{target} get_loaded_song \'album\'`\\n'
    'genre=`{target} get_loaded_song \'genre\'`\\n'
    'year=`{target} get_loaded_song \'year\'`\\n'
    'filepath=`{target} get_loaded_song \'filepath\'`"'
)
_virtualdj_network_warning_logged = False


def run(max_tanda_length, raw_playlist=None):
    playlist, status, _ = run_with_details(max_tanda_length, raw_playlist)
    return playlist, status


def run_with_details(max_tanda_length, raw_playlist=None, emit_debug_log=True):
    integration_mode = beamSettings.getVirtualDJIntegrationMode()

    if integration_mode == 'Network Control':
        playlist, status, details = run_network_control(max_tanda_length, raw_playlist, route='network')
    elif integration_mode == HYBRID_VIRTUALDJ_INTEGRATION_MODE:
        playlist, status, details = run_network_control(max_tanda_length, raw_playlist, route='network')
        if status == 'PlayerNotRunning':
            playlist, status, details = run_history_file(max_tanda_length, raw_playlist, route='fallback-history')
    else:
        playlist, status, details = run_history_file(max_tanda_length, raw_playlist, route='history')

    details['integrationMode'] = integration_mode
    if emit_debug_log:
        log_virtualdj_poll_result(details)
    return playlist, status, details


def run_history_file(max_tanda_length, raw_playlist=None, route='history'):
    _ = max_tanda_length, raw_playlist
    playlist = []
    history_target_deck = get_history_target_deck()
    details = {
        'route': route,
        'status': 'Stopped',
        'historyDeck': history_target_deck,
        'historyFilePath': '',
    }

    try:
        history_file_path = resolve_history_file_path()
    except Exception as error:
        logging.error(error, exc_info=True)
        return playlist, 'Stopped', details

    details['historyFilePath'] = history_file_path

    if not history_file_path:
        return playlist, 'Stopped', details

    if not is_recent_history_file(history_file_path):
        return playlist, 'Stopped', details

    track_line = read_last_valid_track_line(history_file_path)
    if track_line == '':
        return playlist, 'Stopped', details

    song = get_song_from_text(track_line)
    if song_has_metadata(song):
        playlist.append(song)

    details['status'] = 'Playing'
    details['trackLine'] = track_line
    return playlist, 'Playing', details


def run_network_control(max_tanda_length, raw_playlist=None, route='network'):
    global _virtualdj_network_warning_logged

    _ = max_tanda_length, raw_playlist
    playlist = []
    details = {
        'route': route,
        'status': 'PlayerNotRunning',
        'queryMode': beamSettings.getVirtualDJQueryMode(),
        'baseUrl': get_virtualdj_base_url(),
    }

    try:
        now_playing = query_virtualdj(get_playing_script())
        _virtualdj_network_warning_logged = False
    except urllib.error.URLError as error:
        if not _virtualdj_network_warning_logged:
            logging.warning('VirtualDJ Network Control is unavailable: %s', describe_virtualdj_network_error(error))
            _virtualdj_network_warning_logged = True
        details['error'] = describe_virtualdj_network_error(error)
        return playlist, 'PlayerNotRunning', details
    except Exception as error:
        logging.error(error, exc_info=True)
        details['error'] = str(error)
        return playlist, 'PlayerNotRunning', details

    if now_playing == '':
        details['status'] = 'Stopped'
        return playlist, 'Stopped', details

    song = get_song_from_text(now_playing)
    details['nowPlaying'] = now_playing

    try:
        populate_song_metadata(song)
    except urllib.error.URLError as error:
        if not _virtualdj_network_warning_logged:
            logging.warning('VirtualDJ Network Control metadata lookup failed: %s', describe_virtualdj_network_error(error))
            _virtualdj_network_warning_logged = True
        details['metadataError'] = describe_virtualdj_network_error(error)
    except Exception as error:
        logging.debug('VirtualDJ metadata enrichment failed: %s', error, exc_info=True)
        details['metadataError'] = str(error)

    if song_has_metadata(song):
        playlist.append(song)

    details['status'] = 'Playing'
    return playlist, 'Playing', details


def resolve_history_file_path():
    configured_history_path = normalize_virtualdj_path(beamSettings.getVirtualDJHistoryPath())
    if configured_history_path:
        if os.path.isdir(configured_history_path):
            return find_history_file_in_directory(configured_history_path)
        if os.path.isfile(configured_history_path):
            return configured_history_path

    for home_path in get_virtualdj_home_candidates():
        history_directory = os.path.join(home_path, 'History')
        history_file_path = find_history_file_in_directory(history_directory)
        if history_file_path:
            return history_file_path

    return ''


def get_virtualdj_home_candidates():
    candidate_paths = []

    if platform.system() == 'Windows':
        local_app_data = os.environ.get('LOCALAPPDATA', '').strip()
        if local_app_data:
            candidate_paths.append(os.path.join(local_app_data, 'VirtualDJ'))
        candidate_paths.append(os.path.join(os.path.expanduser('~'), 'Documents', 'VirtualDJ'))
    elif platform.system() == 'Darwin':
        candidate_paths.append(os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', 'VirtualDJ'))
        candidate_paths.append(os.path.join(os.path.expanduser('~'), 'Documents', 'VirtualDJ'))
    else:
        candidate_paths.append(os.path.join(os.path.expanduser('~'), 'Documents', 'VirtualDJ'))

    normalized_candidates = []
    for candidate_path in candidate_paths:
        normalized_candidate = normalize_virtualdj_path(candidate_path)
        if normalized_candidate and normalized_candidate not in normalized_candidates and os.path.isdir(normalized_candidate):
            normalized_candidates.append(normalized_candidate)

    return normalized_candidates


def find_history_file_in_directory(history_directory):
    normalized_directory = normalize_virtualdj_path(history_directory)
    if not normalized_directory or not os.path.isdir(normalized_directory):
        return ''

    tracklist_path = os.path.join(normalized_directory, 'tracklist.txt')
    if os.path.isfile(tracklist_path):
        return tracklist_path

    history_candidates = []
    for entry_name in os.listdir(normalized_directory):
        if not entry_name.lower().endswith('.txt'):
            continue
        entry_path = os.path.join(normalized_directory, entry_name)
        if os.path.isfile(entry_path):
            history_candidates.append(entry_path)

    history_candidates.sort(key=os.path.getmtime, reverse=True)
    if history_candidates:
        return history_candidates[0]

    return ''


def normalize_virtualdj_path(path):
    normalized_path = str(path or '').strip()
    if normalized_path == '':
        return ''

    return os.path.normpath(os.path.expandvars(os.path.expanduser(normalized_path)))


def is_recent_history_file(history_file_path):
    max_age_seconds = max(int(beamSettings.getVirtualDJRecentTrackWindowSec()), 0)
    if max_age_seconds == 0:
        return True

    try:
        return (time.time() - os.path.getmtime(history_file_path)) <= max_age_seconds
    except OSError:
        return False


def read_last_valid_track_line(history_file_path):
    file_contents = read_history_file_text(history_file_path)

    for raw_line in reversed(file_contents.splitlines()):
        stripped_line = strip_timestamp_prefix(raw_line).strip()
        if stripped_line == '' or stripped_line.startswith('#'):
            continue

        if should_ignore_history_line(stripped_line):
            continue

        if stripped_line:
            return stripped_line

    return ''


def read_history_file_text(history_file_path):
    for encoding_name in HISTORY_FILE_ENCODINGS:
        try:
            with open(history_file_path, 'r', encoding=encoding_name) as history_file:
                return history_file.read()
        except UnicodeDecodeError:
            continue

    with open(history_file_path, 'r', encoding='latin-1', errors='replace') as history_file:
        return history_file.read()


def query_virtualdj(script):
    query_params = {'script': script}
    token = beamSettings.getVirtualDJBearerToken()

    url = build_virtualdj_url(QUERY_ENDPOINT, query_params)
    request = urllib.request.Request(url, headers={'Accept': 'text/plain'})

    if token:
        request.add_header('Authorization', 'Bearer ' + token)

    with urllib.request.urlopen(request, timeout=get_virtualdj_timeout()) as response:
        return response.read().decode('utf-8', 'replace').strip()


def get_query_target():
    query_mode = beamSettings.getVirtualDJQueryMode()
    return QUERY_MODE_TARGETS.get(query_mode, QUERY_MODE_TARGETS[DEFAULT_VIRTUALDJ_QUERY_MODE])


def get_history_target_deck():
    history_deck = beamSettings.getVirtualDJHistoryDeck()
    return HISTORY_DECK_TARGETS.get(history_deck, HISTORY_DECK_TARGETS[DEFAULT_VIRTUALDJ_HISTORY_DECK])


def describe_history_target_deck(history_target_deck):
    if history_target_deck == ANY_VIRTUALDJ_HISTORY_DECK:
        return 'any'
    return history_target_deck


def get_playing_script():
    return PLAYING_SCRIPT_TEMPLATE.format(target=get_query_target())


def get_field_script(field_name):
    return FIELD_SCRIPT_TEMPLATES[field_name].format(target=get_query_target())


def get_metadata_script():
    return METADATA_SCRIPT_TEMPLATE.format(target=get_query_target())


def build_virtualdj_url(path, query_params=None):
    host = beamSettings.getVirtualDJHost().strip() or DEFAULT_VIRTUALDJ_HOST
    port = beamSettings.getVirtualDJPort()
    netloc = '{0}:{1}'.format(host, int(port))
    query_string = urllib.parse.urlencode(query_params or {})
    return urllib.parse.urlunsplit(('http', netloc, path, query_string, ''))


def get_virtualdj_base_url():
    return build_virtualdj_url('', None).rstrip('/')


def describe_virtualdj_network_error(error):
    if isinstance(error, urllib.error.HTTPError):
        reason = getattr(error, 'reason', '')
        summary = 'HTTP {0}'.format(error.code)
        if reason:
            summary = '{0} {1}'.format(summary, reason)
        return "request to '{0}' failed: {1}. Start the Network Control plugin or switch VirtualDJ integration to History File.".format(
            get_virtualdj_base_url(),
            summary,
        )

    reason = getattr(error, 'reason', error)
    return "request to '{0}' failed: {1}. Start the Network Control plugin or switch VirtualDJ integration to History File.".format(
        get_virtualdj_base_url(),
        reason,
    )


def get_virtualdj_timeout():
    try:
        refresh_seconds = float(beamSettings.getUpdtime()) / 1000.0
    except Exception:
        refresh_seconds = 1.0

    return max(min(refresh_seconds, 5.0), 1.0)


def get_song_from_text(track_text):
    parsed_track = parse_track_text(track_text)
    song = SongObject()
    song.Artist = parsed_track['Artist']
    song.Title = parsed_track['Title']
    song.Genre = parsed_track['Genre']
    song.Year = parsed_track['Year']
    song.FilePath = parsed_track['FilePath']
    return song


def populate_song_metadata(song):
    metadata = get_virtualdj_metadata()

    if metadata.get('Artist'):
        song.Artist = metadata['Artist']
    if metadata.get('Title'):
        song.Title = metadata['Title']
    if metadata.get('Album'):
        song.Album = metadata['Album']
    if metadata.get('Genre'):
        song.Genre = metadata['Genre']
    if metadata.get('Year'):
        song.Year = metadata['Year']
    if metadata.get('FilePath'):
        song.FilePath = metadata['FilePath']


def get_virtualdj_metadata():
    metadata_text = query_virtualdj(get_metadata_script())
    return parse_virtualdj_metadata_text(metadata_text)


def parse_virtualdj_metadata_text(metadata_text):
    metadata = {
        'Artist': '',
        'Title': '',
        'Album': '',
        'Genre': '',
        'Year': '',
        'FilePath': '',
    }
    field_matches = list(HISTORY_FIELD_RE.finditer(metadata_text))

    for index, field_match in enumerate(field_matches):
        field_name = field_match.group(1).strip().lower()
        field_value_start = field_match.end()
        field_value_end = field_matches[index + 1].start() if (index + 1) < len(field_matches) else len(metadata_text)
        field_value = metadata_text[field_value_start:field_value_end].strip()

        if field_name == 'artist':
            metadata['Artist'] = field_value
        elif field_name == 'title':
            metadata['Title'] = field_value
        elif field_name == 'album':
            metadata['Album'] = field_value
        elif field_name == 'genre':
            metadata['Genre'] = field_value
        elif field_name == 'year':
            metadata['Year'] = field_value
        elif field_name == 'filepath':
            metadata['FilePath'] = field_value

    return metadata


def split_artist_title(track_text):
    parsed_track = parse_track_text(track_text)
    return parsed_track['Artist'], parsed_track['Title']


def parse_track_text(track_text):
    normalized_text = strip_timestamp_prefix(track_text).strip()
    parsed_track = {
        'Deck': '',
        'Artist': '',
        'Title': '',
        'Genre': '',
        'Year': '',
        'FilePath': '',
    }

    if normalized_text == '':
        return parsed_track

    key_value_track = parse_key_value_track_text(normalized_text)
    if is_key_value_track_text(normalized_text, key_value_track):
        parsed_track.update(key_value_track)
        return parsed_track

    metadata_text = normalized_text
    deck_match = HISTORY_DECK_PREFIX_RE.match(normalized_text)
    if deck_match:
        parsed_track['Deck'] = deck_match.group(1).strip()
        metadata_text = deck_match.group(2).strip()

    track_parts = [part.strip() for part in metadata_text.split(' - ')]
    if len(track_parts) >= 3:
        parsed_track['Artist'] = track_parts[0]
        parsed_track['Genre'] = track_parts[1]
        parsed_track['Title'] = ' - '.join(track_parts[2:])
        return parsed_track

    if len(track_parts) >= 2:
        parsed_track['Artist'] = track_parts[0]
        parsed_track['Title'] = ' - '.join(track_parts[1:])
        return parsed_track

    parsed_track['Title'] = metadata_text
    return parsed_track


def parse_key_value_track_text(track_text):
    parsed_track = {
        'Deck': '',
        'Artist': '',
        'Title': '',
        'Genre': '',
        'Year': '',
        'FilePath': '',
    }
    field_matches = list(HISTORY_FIELD_RE.finditer(track_text))

    if not field_matches:
        return parsed_track

    for index, field_match in enumerate(field_matches):
        field_name = field_match.group(1).strip().lower()
        field_value_start = field_match.end()
        field_value_end = field_matches[index + 1].start() if (index + 1) < len(field_matches) else len(track_text)
        field_value = track_text[field_value_start:field_value_end].strip()

        if field_name == 'deck':
            parsed_track['Deck'] = field_value
        elif field_name == 'artist':
            parsed_track['Artist'] = field_value
        elif field_name == 'title':
            parsed_track['Title'] = field_value
        elif field_name == 'genre':
            parsed_track['Genre'] = field_value
        elif field_name == 'year':
            parsed_track['Year'] = field_value
        elif field_name == 'filepath':
            parsed_track['FilePath'] = field_value

    return parsed_track


def has_key_value_track_metadata(parsed_track):
    return any([
        parsed_track['Deck'],
        parsed_track['Artist'],
        parsed_track['Title'],
        parsed_track['Genre'],
        parsed_track['Year'],
        parsed_track['FilePath'],
    ])


def is_key_value_track_text(track_text, parsed_track):
    if not has_key_value_track_metadata(parsed_track):
        return False

    field_matches = list(HISTORY_FIELD_RE.finditer(track_text))
    if len(field_matches) > 1:
        return True

    deck_value = parsed_track['Deck']
    return deck_value != '' and len(deck_value.split()) == 1


def should_ignore_history_line(track_text):
    parsed_track = parse_track_text(track_text)
    history_target_deck = get_history_target_deck()
    if history_target_deck == ANY_VIRTUALDJ_HISTORY_DECK:
        return False
    return parsed_track['Deck'] not in ('', history_target_deck)


def strip_timestamp_prefix(track_text):
    return TIMESTAMP_PREFIX_RE.sub('', str(track_text or '').lstrip('\ufeff'))


def song_has_metadata(song):
    return any([
        song.Artist,
        song.Album,
        song.Title,
        song.Genre,
        song.Year,
        song.FilePath,
    ])


def log_virtualdj_poll_result(details):
    route = details.get('route', 'unknown')
    status = details.get('status', 'unknown')

    if route in ('history', 'fallback-history'):
        logging.debug(
            'VirtualDJ poll route=%s status=%s history_deck=%s history_file=%s',
            route,
            status,
            describe_history_target_deck(details.get('historyDeck', '')),
            details.get('historyFilePath', ''),
        )
        return

    logging.debug(
        'VirtualDJ poll route=%s status=%s query_mode=%s base_url=%s',
        route,
        status,
        details.get('queryMode', ''),
        details.get('baseUrl', ''),
    )