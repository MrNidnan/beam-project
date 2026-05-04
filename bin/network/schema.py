from copy import deepcopy

from bin.network.events import PROTOCOL_VERSION, SCHEMA_VERSION


def background_layer_to_dict(layer, layer_name=''):
    layer = layer or {}
    background_url = ''
    if layer_name in ('base', 'overlay'):
        background_url = '/media/background/{0}'.format(layer_name)

    return {
        'available': bool(layer.get('available')),
        'sourcePath': layer.get('sourcePath', ''),
        'currentPath': layer.get('currentPath', ''),
        'url': background_url,
        'reference': layer.get('reference', ''),
        'canonicalReference': layer.get('canonicalReference', ''),
        'relativePath': layer.get('relativePath', ''),
        'scope': layer.get('scope'),
        'kind': layer.get('kind', ''),
        'rotate': layer.get('rotate', 'no'),
        'rotateTimer': layer.get('rotateTimer', 0),
        'mode': layer.get('mode', ''),
        'opacity': layer.get('opacity', 100),
        'name': layer.get('name', ''),
        'field': layer.get('field', ''),
        'matchedField': layer.get('matchedField', ''),
        'operator': layer.get('operator', ''),
        'value': layer.get('value', ''),
    }


def song_to_dict(song):
    if not song:
        return None

    return {
        'artist': song.Artist,
        'album': song.Album,
        'title': song.Title,
        'genre': song.Genre,
        'comment': song.Comment,
        'composer': song.Composer,
        'year': song.Year,
        'singer': song.Singer,
        'albumArtist': song.AlbumArtist,
        'performer': song.Performer,
        'isCortina': song.IsCortina,
        'filePath': song.FilePath,
        'moduleMessage': song.ModuleMessage,
        'ignoreSong': song.IgnoreSong,
    }


def build_display_items(rows, settings):
    items = []

    for index in range(0, len(settings)):
        setting = deepcopy(settings[index])
        text = ''
        if index < len(rows):
            text = rows[index]

        items.append({
            'index': index,
            'text': text,
            'field': setting.get('Field', ''),
            'active': setting.get('Active', 'no'),
            'alignment': setting.get('Alignment', 'Center'),
            'font': setting.get('Font', ''),
            'fontColor': setting.get('FontColor', '(255, 255, 255, 255)'),
            'size': setting.get('Size', 0),
            'style': setting.get('Style', 'Normal'),
            'weight': setting.get('Weight', 'Normal'),
            'position': list(setting.get('Position', [0, 0])),
            'hideControl': setting.get('HideControl', ''),
            'textFlow': setting.get('TextFlow', 'Cut'),
        })

    return items


def snapshot_from_display_data(display_data, beam_settings):
    now_playing = display_data.nowPlayingData
    playlist = []
    for song in now_playing.currentPlaylist:
        playlist.append(song_to_dict(song))

    legacy_background_path_getter = getattr(display_data, 'getLegacyBackgroundPath', None)
    if callable(legacy_background_path_getter):
        legacy_background_path = legacy_background_path_getter()
    else:
        background_layers = getattr(display_data, 'backgroundLayers', {}) or {}
        overlay_layer = background_layers.get('overlay', {}) or {}
        if overlay_layer.get('available') and str(overlay_layer.get('mode', '')).lower() == 'replace':
            legacy_background_path = overlay_layer.get('currentPath') or overlay_layer.get('sourcePath') or ''
        else:
            base_layer = background_layers.get('base', {}) or {}
            legacy_background_path = base_layer.get('currentPath') or base_layer.get('sourcePath') or ''

    return {
        'schemaVersion': SCHEMA_VERSION,
        'protocolVersion': PROTOCOL_VERSION,
        'module': beam_settings.getSelectedModuleName(),
        'playbackStatus': display_data.currentPlaybackStatus,
        'previousPlaybackStatus': getattr(display_data, 'previousPlaybackStatus', ''),
        'statusMessage': now_playing.StatusMessage,
        'moodName': display_data.currentMoodName,
        'background': {
            'available': bool(legacy_background_path),
            'sourcePath': legacy_background_path,
            'url': '/media/background/current',
            'base': background_layer_to_dict(display_data.backgroundLayers.get('base'), 'base'),
            'overlay': background_layer_to_dict(display_data.backgroundLayers.get('overlay'), 'overlay'),
        },
        'displayRows': list(display_data.currentDisplayRows),
        'displayItems': build_display_items(display_data.currentDisplayRows, display_data.currentDisplaySettings),
        'playlist': playlist,
        'currentSong': song_to_dict(playlist and now_playing.currentPlaylist[0] or None),
        'previousSong': song_to_dict(now_playing.prevPlayedSong),
        'nextSong': song_to_dict(len(now_playing.currentPlaylist) > 1 and now_playing.currentPlaylist[1] or None),
        'nextTandaSong': song_to_dict(now_playing.nextTandaSong),
        'displayTimer': now_playing.playlistchangetime,
        'coverArt': {
            'available': now_playing.currentCoverArtImage is not None,
            'url': '/media/cover-art/current',
            'sourcePath': getattr(now_playing, 'currentCoverArtPath', '') or '',
        },
        'coverArtAvailable': now_playing.currentCoverArtImage is not None,
    }


def empty_snapshot(beam_settings):
    return {
        'schemaVersion': SCHEMA_VERSION,
        'protocolVersion': PROTOCOL_VERSION,
        'module': beam_settings.getSelectedModuleName(),
        'playbackStatus': '',
        'previousPlaybackStatus': '',
        'statusMessage': '',
        'moodName': '',
        'background': {
            'available': False,
            'sourcePath': '',
            'url': '/media/background/current',
            'base': background_layer_to_dict(None, 'base'),
            'overlay': background_layer_to_dict(None, 'overlay'),
        },
        'displayRows': [],
        'displayItems': [],
        'playlist': [],
        'currentSong': None,
        'previousSong': None,
        'nextSong': None,
        'nextTandaSong': None,
        'displayTimer': 0,
        'coverArt': {
            'available': False,
            'url': '/media/cover-art/current',
            'sourcePath': '',
        },
        'coverArtAvailable': False,
    }