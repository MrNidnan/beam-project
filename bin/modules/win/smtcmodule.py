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
# Reads the Windows System Media Transport Controls (SMTC) "now playing"
# session - the same metadata the Windows volume/media flyout shows. This is an
# OS-level, offline, app-agnostic source: any player that publishes a media
# session (Spotify, Apple Music app, YouTube Music, Amazon Music, browsers...)
# is readable through the one interface, so no per-app integration is needed.

import asyncio
import atexit
import glob
import hashlib
import logging
import os
import tempfile
from types import SimpleNamespace

from bin.songclass import SongObject

# Cover thumbnails are written to temp files (the cover pipeline is path-based).
# All share this prefix so they can be swept as a group.
_COVER_PREFIX = 'beam_smtc_'


def _sweep_cover_temp():
    # Remove every cover file we may have left behind. Run at import (clears
    # leftovers from a previous crashed run) and at exit (clean shutdown).
    # Assumes a single Beam instance - a concurrent instance's covers would also
    # be swept, which is acceptable since each rewrites its cover every cycle.
    pattern = os.path.join(tempfile.gettempdir(), _COVER_PREFIX + '*')
    for path in glob.glob(pattern):
        try:
            os.remove(path)
        except OSError:
            pass


_sweep_cover_temp()
atexit.register(_sweep_cover_temp)

# The WinRT SMTC API is exposed by the pywinrt split packages under the `winrt`
# namespace (preferred - prebuilt wheels, no compile) and by the older monolithic
# `winsdk` package as a fallback. Import is guarded (like icecastmodule) so this
# module always imports and caches: nowplayingdata re-imports it every read cycle,
# and the dependency is Windows-only / optional.
try:
    from winrt.windows.media.control import (
        GlobalSystemMediaTransportControlsSessionManager as _SessionManager,
        GlobalSystemMediaTransportControlsSessionPlaybackStatus as _PlaybackStatus,
    )
    _IMPORT_ERROR = None
except Exception:  # noqa: BLE001 - fall back to winsdk, else degrade gracefully
    try:
        from winsdk.windows.media.control import (
            GlobalSystemMediaTransportControlsSessionManager as _SessionManager,
            GlobalSystemMediaTransportControlsSessionPlaybackStatus as _PlaybackStatus,
        )
        _IMPORT_ERROR = None
    except Exception as _import_error:  # noqa: BLE001 - report the failure
        _SessionManager = None
        _PlaybackStatus = None
        _IMPORT_ERROR = _import_error

# Reading the album-art thumbnail needs the Storage.Streams types (DataReader /
# Buffer). Optional: if absent, text metadata still works, only cover art is
# skipped. Same winrt -> winsdk fallback as above.
try:
    from winrt.windows.storage.streams import DataReader as _DataReader, Buffer as _Buffer
except Exception:  # noqa: BLE001
    try:
        from winsdk.windows.storage.streams import DataReader as _DataReader, Buffer as _Buffer
    except Exception:  # noqa: BLE001
        _DataReader = None
        _Buffer = None

if _IMPORT_ERROR is not None:
    logging.info("smtcmodule: WinRT import failed, SMTC unavailable: %s", _IMPORT_ERROR)


# Diagnostic logging is gated on change so the per-cycle poll does not spam the
# log. _log_once stores the last message keyed by tag and only emits on change.
_LAST_LOG = {}


def _log_once(tag, level, msg, *args):
    rendered = msg % args if args else msg
    if _LAST_LOG.get(tag) != rendered:
        _LAST_LOG[tag] = rendered
        logging.log(level, "smtcmodule: %s", rendered)


# WinRT GlobalSystemMediaTransportControlsSessionPlaybackStatus integer values:
# CLOSED=0, OPENED=1, CHANGING=2, STOPPED=3, PLAYING=4, PAUSED=5. We map by the
# integer value so the logic is testable without importing winsdk.
_STATUS_MAP = {
    4: 'Playing',
    5: 'Paused',
    2: 'Paused',  # CHANGING - a transition; treat as paused (keeps prior playlist)
}


# Best-effort AUMID (Application User Model ID) -> friendly label. AUMIDs carry
# version/hash suffixes, so matching is substring-based; unknown apps fall back
# to the raw AUMID.
_AUMID_FRIENDLY = (
    ('Spotify.exe', 'Spotify'),
    ('SpotifyAB.SpotifyMusic', 'Spotify (Store)'),
    ('AppleInc.AppleMusicWin', 'Apple Music'),
    ('AppleInc.iTunes', 'iTunes'),
    ('AmazonMobileLLC.AmazonMusic', 'Amazon Music'),
    ('AmazonMusic', 'Amazon Music'),
    ('youtube_music', 'YouTube Music'),
    ('YouTubeMusic', 'YouTube Music'),
    ('Chrome', 'Google Chrome'),
    ('MSEdge', 'Microsoft Edge'),
    ('msedge', 'Microsoft Edge'),
    ('308046B0AF4A39CB', 'Firefox'),
    ('Tidal', 'TIDAL'),
    ('Deezer', 'Deezer'),
)


def _safe_str(value):
    return '' if value is None else str(value)


def aumid_friendly_name(aumid):
    normalized = _safe_str(aumid).strip()
    if normalized == '':
        return ''
    lowered = normalized.lower()
    for key, name in _AUMID_FRIENDLY:
        if key.lower() in lowered:
            return name
    return normalized


def _status_to_beam(status):
    # Accepts a WinRT enum member (has .value) or a plain int.
    try:
        value = int(status.value) if hasattr(status, 'value') else int(status)
    except (TypeError, ValueError):
        return 'PlayerNotRunning'
    return _STATUS_MAP.get(value, 'PlayerNotRunning')


def _props_to_song(props):
    song = SongObject()
    song.Title = _safe_str(getattr(props, 'title', ''))
    song.Artist = _safe_str(getattr(props, 'artist', ''))
    song.Album = _safe_str(getattr(props, 'album_title', ''))
    song.AlbumArtist = _safe_str(getattr(props, 'album_artist', ''))

    # SMTC has a genres list, but virtually every app leaves it empty. Read it
    # anyway for the rare app that fills it.
    genres = getattr(props, 'genres', None)
    if genres:
        try:
            first_genre = list(genres)[0]
            song.Genre = _safe_str(first_genre)
        except Exception:
            pass

    return song


def _session_aumid(session):
    return _safe_str(getattr(session, 'source_app_user_model_id', ''))


# Tracks the last cover file we wrote so it can be removed when the song changes,
# keeping the temp dir from accumulating one jpg per track played.
_LAST_COVER_PATH = None


async def _read_thumbnail_bytes(props):
    # props.thumbnail is an IRandomAccessStreamReference (or None). Open it, pull
    # the bytes through a DataReader. Best-effort: any failure -> no cover art.
    if _DataReader is None or _Buffer is None:
        _log_once("thumb", logging.INFO, "thumbnail skipped: Storage.Streams not importable")
        return None
    ref = getattr(props, 'thumbnail', None)
    if ref is None:
        _log_once("thumb", logging.INFO, "thumbnail skipped: props.thumbnail is None")
        return None
    try:
        stream = await ref.open_read_async()
        size = int(stream.size)
        if size <= 0:
            _log_once("thumb", logging.INFO, "thumbnail skipped: stream size=%d", size)
            return None
        reader = _DataReader(stream)
        await reader.load_async(size)
        # pywinrt read_bytes() fills a pre-sized bytes-like buffer in place rather
        # than taking a count and returning the data.
        buffer = bytearray(size)
        reader.read_bytes(buffer)
        data = bytes(buffer)
        _log_once("thumb", logging.INFO, "thumbnail read OK: %d bytes", len(data))
        return data
    except Exception as error:  # noqa: BLE001
        _log_once("thumb", logging.INFO, "thumbnail read failed: %s", error)
        logging.debug("smtcmodule: thumbnail read failed", exc_info=True)
        return None


def _image_extension(data):
    # Detect the thumbnail's real format from its magic bytes so the temp file
    # gets a matching extension. SMTC apps publish JPEG, PNG or BMP (and rarely
    # GIF), so the cover must not be assumed to be any single format. Unknown
    # signatures get no extension -> treated as undecodable.
    if data[:3] == b'\xff\xd8\xff':
        return '.jpg'
    if data[:8] == b'\x89PNG\r\n\x1a\n':
        return '.png'
    if data[:2] == b'BM':
        return '.bmp'
    if data[:6] in (b'GIF87a', b'GIF89a'):
        return '.gif'
    return ''


def _write_cover_temp(data, key):
    # Persist thumbnail bytes to a stable temp file named by a hash of the track
    # key, so the path changes when the song changes (forcing Beam to reload the
    # cover) but is reused for the same track. The extension matches the real
    # format; mutagenutils.readCoverArtData reads an image file at FilePath
    # directly using the mime implied by that extension.
    global _LAST_COVER_PATH
    extension = _image_extension(data)
    if extension == '':
        _log_once("cover_path", logging.INFO, "cover skipped: unrecognized thumbnail format")
        return ''
    digest = hashlib.md5(key.encode('utf-8', 'replace')).hexdigest()[:12]
    path = os.path.join(tempfile.gettempdir(), '%s%s%s' % (_COVER_PREFIX, digest, extension))
    try:
        with open(path, 'wb') as handle:
            handle.write(data)
    except OSError:
        logging.debug("smtcmodule: cover write failed", exc_info=True)
        return ''

    if _LAST_COVER_PATH and _LAST_COVER_PATH != path:
        try:
            os.remove(_LAST_COVER_PATH)
        except OSError:
            pass
    _LAST_COVER_PATH = path
    return path


def _pick_session(manager, preferred_aumid):
    if manager is None:
        return None

    preferred = _safe_str(preferred_aumid).strip()
    if preferred:
        for session in manager.get_sessions():
            if _session_aumid(session) == preferred:
                return session
        # Preferred app has no active session right now; fall back to whatever
        # the system considers current rather than reporting nothing.

    return manager.get_current_session()


async def _read_session_async(preferred_aumid):
    manager = await _SessionManager.request_async()
    sessions = list(manager.get_sessions())
    _log_once(
        "sessions",
        logging.DEBUG,
        "%d session(s) published: %s | preferred=%r",
        len(sessions),
        [_session_aumid(s) for s in sessions],
        _safe_str(preferred_aumid),
    )
    session = _pick_session(manager, preferred_aumid)
    if session is None:
        _log_once("picked", logging.INFO, "no session picked (current_session is None)")
        return SimpleNamespace(status='PlayerNotRunning', song=None, aumid='', sessionCount=len(sessions))

    aumid = _session_aumid(session)
    raw_status = session.get_playback_info().playback_status
    status = _status_to_beam(raw_status)
    _log_once(
        "picked",
        logging.DEBUG,
        "picked aumid=%r raw_status=%r -> status=%r",
        aumid, getattr(raw_status, 'value', raw_status), status,
    )

    song = None
    if status == 'Playing':
        props = await session.try_get_media_properties_async()
        song = _props_to_song(props)
        cover_bytes = await _read_thumbnail_bytes(props)
        if cover_bytes:
            song.FilePath = _write_cover_temp(
                cover_bytes, '|'.join((aumid, song.Title, song.Artist))
            )
            _log_once("cover_path", logging.INFO, "cover written to FilePath=%r", song.FilePath)
        _log_once(
            "props",
            logging.DEBUG,
            "props title=%r artist=%r album=%r cover=%s",
            song.Title, song.Artist, song.Album, bool(cover_bytes),
        )

    return SimpleNamespace(status=status, song=song, aumid=aumid, sessionCount=len(sessions))


def _read_now_playing(preferred_aumid, timeout=5):
    # A fresh event loop per call: run() executes on Beam's worker thread which
    # has no running loop. wait_for bounds a wedged WinRT query so it cannot hang
    # the non-daemon reader thread on shutdown.
    try:
        return asyncio.run(asyncio.wait_for(_read_session_async(preferred_aumid), timeout))
    except Exception as error:  # noqa: BLE001 - includes asyncio.TimeoutError
        _log_once("read_error", logging.INFO, "read failed: %s", error)
        logging.debug("smtcmodule: read failed", exc_info=True)
        return None


async def _list_sessions_async():
    manager = await _SessionManager.request_async()
    sessions = []
    for session in manager.get_sessions():
        aumid = _session_aumid(session)
        try:
            status = _status_to_beam(session.get_playback_info().playback_status)
        except Exception:
            status = 'PlayerNotRunning'
        sessions.append({'aumid': aumid, 'name': aumid_friendly_name(aumid), 'status': status})
    return sessions


def list_sessions(timeout=5):
    # For the preferences picker: enumerate the apps currently publishing a
    # media session. Returns a list of {aumid, name, status} dicts.
    if _SessionManager is None:
        return []
    try:
        return asyncio.run(asyncio.wait_for(_list_sessions_async(), timeout))
    except Exception as error:  # noqa: BLE001 - includes asyncio.TimeoutError
        logging.debug("smtcmodule: list_sessions failed: %s", error, exc_info=True)
        return []


def run_with_details(MaxTandaLength, preferred_aumid=''):
    details = {'route': 'smtc', 'aumid': '', 'appName': '', 'sessionCount': 0}

    if _SessionManager is None:
        details['route'] = 'unavailable'
        details['error'] = str(_IMPORT_ERROR)
        return [], 'PlayerNotRunning', details

    reading = _read_now_playing(preferred_aumid)
    if reading is None:
        details['error'] = 'No media session could be read.'
        return [], 'PlayerNotRunning', details

    details['aumid'] = reading.aumid
    details['appName'] = aumid_friendly_name(reading.aumid)
    details['sessionCount'] = reading.sessionCount

    # Only surface a playlist while actually playing; Paused/Stopped return an
    # empty list so nowplayingdata keeps the previous reading.
    playlist = [reading.song] if (reading.status == 'Playing' and reading.song is not None) else []
    return playlist, reading.status, details


def run(MaxTandaLength, preferred_aumid=''):
    playlist, status, _details = run_with_details(MaxTandaLength, preferred_aumid)
    return playlist, status
