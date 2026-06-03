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
import logging
from types import SimpleNamespace

from bin.songclass import SongObject

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
    session = _pick_session(manager, preferred_aumid)
    if session is None:
        return SimpleNamespace(status='PlayerNotRunning', song=None, aumid='', sessionCount=len(sessions))

    aumid = _session_aumid(session)
    status = _status_to_beam(session.get_playback_info().playback_status)

    song = None
    if status == 'Playing':
        props = await session.try_get_media_properties_async()
        song = _props_to_song(props)

    return SimpleNamespace(status=status, song=song, aumid=aumid, sessionCount=len(sessions))


def _read_now_playing(preferred_aumid, timeout=5):
    # A fresh event loop per call: run() executes on Beam's worker thread which
    # has no running loop. wait_for bounds a wedged WinRT query so it cannot hang
    # the non-daemon reader thread on shutdown.
    try:
        return asyncio.run(asyncio.wait_for(_read_session_async(preferred_aumid), timeout))
    except Exception as error:  # noqa: BLE001 - includes asyncio.TimeoutError
        logging.debug("smtcmodule: read failed: %s", error, exc_info=True)
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
