import logging
import urllib.parse
import urllib.request

from bin.beamsettings import beamSettings
from bin.songclass import SongObject


DEFAULT_VIRTUALDJ_HOST = '127.0.0.1'
DEFAULT_VIRTUALDJ_PORT = 80
DEFAULT_VIRTUALDJ_QUERY_MODE = 'Master'
QUERY_ENDPOINT = '/query'
QUERY_MODE_TARGETS = {
    'Master': 'deck master',
    'Deck 1': 'deck 1',
    'Deck 2': 'deck 2',
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


def run(max_tanda_length, raw_playlist=None):
    _ = max_tanda_length, raw_playlist
    playlist = []

    try:
        now_playing = query_virtualdj(get_playing_script())
    except Exception as error:
        logging.error(error, exc_info=True)
        return playlist, 'PlayerNotRunning'

    if now_playing == '':
        return playlist, 'Stopped'

    song = get_song_from_text(now_playing)

    try:
        populate_song_metadata(song)
    except Exception as error:
        logging.debug('VirtualDJ metadata enrichment failed: %s', error, exc_info=True)

    if song_has_metadata(song):
        playlist.append(song)

    return playlist, 'Playing'


def query_virtualdj(script):
    query_params = {'script': script}
    token = beamSettings.getVirtualDJBearerToken()
    if token:
        query_params['bearer'] = token

    url = build_virtualdj_url(QUERY_ENDPOINT, query_params)
    request = urllib.request.Request(url, headers={'Accept': 'text/plain'})

    if token:
        request.add_header('Authorization', 'Bearer ' + token)

    with urllib.request.urlopen(request, timeout=get_virtualdj_timeout()) as response:
        return response.read().decode('utf-8', 'replace').strip()


def get_query_target():
    query_mode = beamSettings.getVirtualDJQueryMode()
    return QUERY_MODE_TARGETS.get(query_mode, QUERY_MODE_TARGETS[DEFAULT_VIRTUALDJ_QUERY_MODE])


def get_playing_script():
    return PLAYING_SCRIPT_TEMPLATE.format(target=get_query_target())


def get_field_script(field_name):
    return FIELD_SCRIPT_TEMPLATES[field_name].format(target=get_query_target())


def build_virtualdj_url(path, query_params=None):
    host = beamSettings.getVirtualDJHost().strip() or DEFAULT_VIRTUALDJ_HOST
    port = beamSettings.getVirtualDJPort()
    netloc = '{0}:{1}'.format(host, int(port))
    query_string = urllib.parse.urlencode(query_params or {})
    return urllib.parse.urlunsplit(('http', netloc, path, query_string, ''))


def get_virtualdj_timeout():
    try:
        refresh_seconds = float(beamSettings.getUpdtime()) / 1000.0
    except Exception:
        refresh_seconds = 1.0

    return max(min(refresh_seconds, 5.0), 1.0)


def get_song_from_text(track_text):
    artist, title = split_artist_title(track_text)
    song = SongObject()
    song.Artist = artist
    song.Title = title
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
    metadata = {}

    for field_name in FIELD_SCRIPT_TEMPLATES:
        metadata[field_name] = query_virtualdj(get_field_script(field_name))

    return metadata


def split_artist_title(track_text):
    normalized_text = str(track_text).strip()
    if normalized_text == '':
        return '', ''

    if ' - ' in normalized_text:
        artist, title = normalized_text.split(' - ', 1)
        return artist.strip(), title.strip()

    return '', normalized_text


def song_has_metadata(song):
    return any([
        song.Artist,
        song.Album,
        song.Title,
        song.Genre,
        song.Year,
        song.FilePath,
    ])