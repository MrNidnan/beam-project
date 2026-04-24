from copy import deepcopy

from bin.network.events import PROTOCOL_VERSION, SCHEMA_VERSION


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

    return {
        'schemaVersion': SCHEMA_VERSION,
        'protocolVersion': PROTOCOL_VERSION,
        'module': beam_settings.getSelectedModuleName(),
        'playbackStatus': display_data.currentPlaybackStatus,
        'previousPlaybackStatus': getattr(display_data, 'previousPlaybackStatus', ''),
        'statusMessage': now_playing.StatusMessage,
        'moodName': display_data.currentMoodName,
        'background': {
            'available': bool(display_data._currentBackgroundPath),
            'sourcePath': display_data._currentBackgroundPath,
            'url': '/media/background/current',
        },
        'displayRows': list(display_data.currentDisplayRows),
        'displayItems': build_display_items(display_data.currentDisplayRows, display_data.currentDisplaySettings),
        'playlist': playlist,
        'currentSong': song_to_dict(playlist and now_playing.currentPlaylist[0] or None),
        'previousSong': song_to_dict(now_playing.prevPlayedSong),
        'nextSong': song_to_dict(len(now_playing.currentPlaylist) > 1 and now_playing.currentPlaylist[1] or None),
        'nextTandaSong': song_to_dict(now_playing.nextTandaSong),
        'displayTimer': now_playing.playlistchangetime,
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
        },
        'displayRows': [],
        'displayItems': [],
        'playlist': [],
        'currentSong': None,
        'previousSong': None,
        'nextSong': None,
        'nextTandaSong': None,
        'displayTimer': 0,
        'coverArtAvailable': False,
    }