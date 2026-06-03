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
# Reads the Linux MPRIS "now playing" session over D-Bus - the Linux analog to
# the Windows SMTC reader (smtcmodule). MPRIS (org.mpris.MediaPlayer2) is the
# desktop-wide media interface any compliant player publishes (Spotify, VLC,
# browsers via plasma/chrome integration, Rhythmbox, Strawberry...), so this is
# an app-agnostic source needing no per-app integration. Public API mirrors
# smtcmodule exactly (aumid_friendly_name / list_sessions / run_with_details /
# run) so nowplayingsource can swap backends by platform.

import asyncio
import atexit
import glob
import hashlib
import logging
import os
import tempfile
from types import SimpleNamespace
from urllib.parse import urlparse, unquote
from urllib.request import url2pathname, urlopen

from bin.songclass import SongObject

# Cover art is written to temp files (the cover pipeline is path-based). All
# share this prefix so they can be swept as a group. Distinct from the SMTC
# prefix so the two backends never fight over each other's files.
_COVER_PREFIX = 'beam_mpris_'


def _sweep_cover_temp():
    # Remove every cover file we may have left behind. Run at import (clears
    # leftovers from a previous crashed run) and at exit (clean shutdown).
    pattern = os.path.join(tempfile.gettempdir(), _COVER_PREFIX + '*')
    for path in glob.glob(pattern):
        try:
            os.remove(path)
        except OSError:
            pass


_sweep_cover_temp()
atexit.register(_sweep_cover_temp)

# Two D-Bus bindings are supported, preferring dbus-next (async, pure-python).
# dbus-python is the fallback: it is already a guaranteed Linux dependency and is
# what the existing per-app lin modules use, so MPRIS keeps working on installs
# that have not added dbus-next, and adding dbus-next never breaks them. Imports
# are guarded (like smtcmodule's winrt -> winsdk fallback) so the module always
# imports and caches.
try:
    from dbus_next.aio import MessageBus
    from dbus_next.constants import BusType
    _HAS_DBUS_NEXT = True
except Exception:  # noqa: BLE001
    MessageBus = None
    BusType = None
    _HAS_DBUS_NEXT = False

try:
    import dbus as _dbus
    _HAS_DBUS_PYTHON = True
except Exception:  # noqa: BLE001
    _dbus = None
    _HAS_DBUS_PYTHON = False

_IMPORT_ERROR = None if (_HAS_DBUS_NEXT or _HAS_DBUS_PYTHON) else 'no D-Bus binding (install dbus-next or dbus-python)'

if _IMPORT_ERROR is not None:
    logging.info("mprismodule: %s, MPRIS unavailable", _IMPORT_ERROR)


def _available():
    return _HAS_DBUS_NEXT or _HAS_DBUS_PYTHON


# Diagnostic logging is gated on change so the per-cycle poll does not spam the
# log. _log_once stores the last message keyed by tag and only emits on change.
_LAST_LOG = {}


def _log_once(tag, level, msg, *args):
    rendered = msg % args if args else msg
    if _LAST_LOG.get(tag) != rendered:
        _LAST_LOG[tag] = rendered
        logging.log(level, "mprismodule: %s", rendered)


_MPRIS_PREFIX = 'org.mpris.MediaPlayer2.'
_PLAYER_OBJECT = '/org/mpris/MediaPlayer2'
_PLAYER_IFACE = 'org.mpris.MediaPlayer2.Player'
_PROPS_IFACE = 'org.freedesktop.DBus.Properties'

# MPRIS PlaybackStatus is a string: 'Playing' | 'Paused' | 'Stopped'. Map to the
# Beam vocabulary; anything else means nothing useful is playing.
_STATUS_MAP = {
    'Playing': 'Playing',
    'Paused': 'Paused',
}

# Best-effort bus-suffix -> friendly label. The MPRIS bus name suffix (the part
# after the prefix, e.g. 'spotify', 'chromium.instance1234') plays the role of
# the SMTC AUMID. Matching is substring-based; unknown players fall back to the
# raw bus name.
_BUS_FRIENDLY = (
    ('spotify', 'Spotify'),
    ('chromium', 'Chromium'),
    ('chrome', 'Google Chrome'),
    ('firefox', 'Firefox'),
    ('vlc', 'VLC'),
    ('mpv', 'mpv'),
    ('rhythmbox', 'Rhythmbox'),
    ('clementine', 'Clementine'),
    ('strawberry', 'Strawberry'),
    ('audacious', 'Audacious'),
    ('banshee', 'Banshee'),
    ('amarok', 'Amarok'),
    ('elisa', 'Elisa'),
    ('lollypop', 'Lollypop'),
    ('youtube', 'YouTube Music'),
    ('tidal', 'TIDAL'),
    ('deezer', 'Deezer'),
)


def _safe_str(value):
    return '' if value is None else str(value)


def aumid_friendly_name(bus_name):
    # Named to match the SMTC backend's API. The "aumid" here is the MPRIS bus
    # name; the friendly label is matched on its suffix.
    normalized = _safe_str(bus_name).strip()
    if normalized == '':
        return ''
    suffix = normalized[len(_MPRIS_PREFIX):] if normalized.startswith(_MPRIS_PREFIX) else normalized
    lowered = suffix.lower()
    for key, name in _BUS_FRIENDLY:
        if key in lowered:
            return name
    return normalized


def _status_to_beam(status):
    return _STATUS_MAP.get(_safe_str(status), 'PlayerNotRunning')


def _variant_value(value):
    # dbus-next wraps property values in Variant objects (a .value attribute).
    # Metadata is a{sv}, so its members are Variants too. Unwrap one level.
    return getattr(value, 'value', value)


def _meta_get(metadata, key):
    if key not in metadata:
        return None
    return _variant_value(metadata[key])


def _first(value):
    # xesam:artist / albumArtist / genre are string arrays; take the first.
    if isinstance(value, (list, tuple)):
        return value[0] if value else ''
    return value


def _metadata_to_song(metadata):
    song = SongObject()
    song.Title = _safe_str(_meta_get(metadata, 'xesam:title'))
    song.Artist = _safe_str(_first(_meta_get(metadata, 'xesam:artist')))
    song.Album = _safe_str(_meta_get(metadata, 'xesam:album'))
    song.AlbumArtist = _safe_str(_first(_meta_get(metadata, 'xesam:albumArtist')))
    song.Genre = _safe_str(_first(_meta_get(metadata, 'xesam:genre')))
    return song


# Tracks the last cover file we wrote so it can be removed when the song changes.
_LAST_COVER_PATH = None


def _image_extension(data):
    # Detect the image's real format from its magic bytes so the temp file gets a
    # matching extension (mutagenutils.readCoverArtData reads it back by mime).
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
    # Persist cover bytes to a stable temp file named by a hash of the track key
    # (path changes per song -> forces Beam to reload; reused for the same song).
    global _LAST_COVER_PATH
    extension = _image_extension(data)
    if extension == '':
        _log_once("cover_path", logging.INFO, "cover skipped: unrecognized image format")
        return ''
    digest = hashlib.md5(key.encode('utf-8', 'replace')).hexdigest()[:12]
    path = os.path.join(tempfile.gettempdir(), '%s%s%s' % (_COVER_PREFIX, digest, extension))
    try:
        with open(path, 'wb') as handle:
            handle.write(data)
    except OSError:
        logging.debug("mprismodule: cover write failed", exc_info=True)
        return ''

    if _LAST_COVER_PATH and _LAST_COVER_PATH != path:
        try:
            os.remove(_LAST_COVER_PATH)
        except OSError:
            pass
    _LAST_COVER_PATH = path
    return path


def _resolve_art(art_url, key):
    # mpris:artUrl is a URI. file:// points at a local image we can hand straight
    # to the path-based cover reader; http(s):// is downloaded to a temp file.
    url = _safe_str(art_url).strip()
    if url == '':
        return ''
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()

    if scheme == 'file':
        local_path = url2pathname(unquote(parsed.path))
        if os.path.isfile(local_path):
            return local_path
        _log_once("cover_path", logging.INFO, "cover file missing: %r", local_path)
        return ''

    if scheme in ('http', 'https'):
        try:
            with urlopen(url, timeout=4) as response:  # noqa: S310 - art from local player
                data = response.read()
        except Exception as error:  # noqa: BLE001
            _log_once("cover_path", logging.INFO, "cover download failed: %s", error)
            return ''
        return _write_cover_temp(data, key)

    _log_once("cover_path", logging.INFO, "cover skipped: unsupported scheme %r", scheme)
    return ''


def _pick_name(names, preferred, status_of):
    # MPRIS has no system-wide "current session" concept, so we choose: the
    # preferred player if present, else the first that is Playing, else the first.
    # status_of(name) -> Beam status string; backend-specific, injected.
    preferred = _safe_str(preferred).strip()
    if preferred and preferred in names:
        return preferred
    for name in names:
        try:
            if status_of(name) == 'Playing':
                return name
        except Exception:  # noqa: BLE001 - skip a player that errors mid-enumeration
            continue
    return names[0] if names else None


def _build_reading(bus_name, names, status, metadata):
    # Shared across both backends: turn a picked player's status + metadata dict
    # (plain dict; values may be dbus-next Variants or dbus-python types, both
    # handled by _meta_get) into the SimpleNamespace the public API returns.
    _log_once("picked", logging.DEBUG, "picked bus=%r -> status=%r", bus_name, status)
    song = None
    if status == 'Playing':
        song = _metadata_to_song(metadata or {})
        art = _resolve_art(_meta_get(metadata or {}, 'mpris:artUrl'), '|'.join((bus_name, song.Title, song.Artist)))
        if art:
            song.FilePath = art
            _log_once("cover_path", logging.INFO, "cover at FilePath=%r", song.FilePath)
        _log_once(
            "props", logging.DEBUG,
            "props title=%r artist=%r album=%r cover=%s",
            song.Title, song.Artist, song.Album, bool(art),
        )
    return SimpleNamespace(status=status, song=song, aumid=bus_name, sessionCount=len(names))


# --- dbus-next backend (async) ----------------------------------------------

async def _next_props(bus, bus_name):
    introspection = await bus.introspect(bus_name, _PLAYER_OBJECT)
    proxy = bus.get_proxy_object(bus_name, _PLAYER_OBJECT, introspection)
    return proxy.get_interface(_PROPS_IFACE)


async def _next_names(bus):
    introspection = await bus.introspect('org.freedesktop.DBus', '/org/freedesktop/DBus')
    proxy = bus.get_proxy_object('org.freedesktop.DBus', '/org/freedesktop/DBus', introspection)
    dbus_iface = proxy.get_interface('org.freedesktop.DBus')
    names = await dbus_iface.call_list_names()
    return [name for name in names if name.startswith(_MPRIS_PREFIX)]


async def _next_status(bus, bus_name):
    props = await _next_props(bus, bus_name)
    return _status_to_beam(_variant_value(await props.call_get(_PLAYER_IFACE, 'PlaybackStatus')))


async def _next_read_async(preferred_bus):
    bus = await MessageBus(bus_type=BusType.SESSION).connect()
    try:
        names = await _next_names(bus)
        _log_once("sessions", logging.DEBUG, "%d player(s) published: %s | preferred=%r",
                  len(names), names, _safe_str(preferred_bus))
        # _pick_name needs a sync status callback; pre-fetch statuses once.
        status_cache = {}

        def status_of(name):
            return status_cache.get(name, 'PlayerNotRunning')

        for name in names:
            try:
                status_cache[name] = await _next_status(bus, name)
            except Exception:  # noqa: BLE001
                status_cache[name] = 'PlayerNotRunning'

        bus_name = _pick_name(names, preferred_bus, status_of)
        if bus_name is None:
            _log_once("picked", logging.INFO, "no player picked (none published)")
            return SimpleNamespace(status='PlayerNotRunning', song=None, aumid='', sessionCount=len(names))

        props = await _next_props(bus, bus_name)
        status = _status_to_beam(_variant_value(await props.call_get(_PLAYER_IFACE, 'PlaybackStatus')))
        metadata = {}
        if status == 'Playing':
            metadata = _variant_value(await props.call_get(_PLAYER_IFACE, 'Metadata')) or {}
        return _build_reading(bus_name, names, status, metadata)
    finally:
        bus.disconnect()


async def _next_list_async():
    bus = await MessageBus(bus_type=BusType.SESSION).connect()
    try:
        sessions = []
        for bus_name in await _next_names(bus):
            try:
                status = await _next_status(bus, bus_name)
            except Exception:  # noqa: BLE001
                status = 'PlayerNotRunning'
            sessions.append({'aumid': bus_name, 'name': aumid_friendly_name(bus_name), 'status': status})
        return sessions
    finally:
        bus.disconnect()


# --- dbus-python backend (sync) ---------------------------------------------

def _py_names(bus):
    return [str(n) for n in bus.list_names() if str(n).startswith(_MPRIS_PREFIX)]


def _py_status(bus, bus_name, timeout=4):
    obj = bus.get_object(bus_name, _PLAYER_OBJECT)
    props = _dbus.Interface(obj, _PROPS_IFACE)
    return _status_to_beam(str(props.Get(_PLAYER_IFACE, 'PlaybackStatus', timeout=timeout)))


def _py_read(preferred_bus):
    bus = _dbus.SessionBus()
    names = _py_names(bus)
    _log_once("sessions", logging.DEBUG, "%d player(s) published: %s | preferred=%r",
              len(names), names, _safe_str(preferred_bus))
    bus_name = _pick_name(names, preferred_bus, lambda n: _py_status(bus, n))
    if bus_name is None:
        _log_once("picked", logging.INFO, "no player picked (none published)")
        return SimpleNamespace(status='PlayerNotRunning', song=None, aumid='', sessionCount=len(names))

    obj = bus.get_object(bus_name, _PLAYER_OBJECT)
    props = _dbus.Interface(obj, _PROPS_IFACE)
    status = _status_to_beam(str(props.Get(_PLAYER_IFACE, 'PlaybackStatus', timeout=4)))
    metadata = {}
    if status == 'Playing':
        # dbus-python returns a dbus.Dictionary of dbus types; dict() gives plain
        # keys, values stay dbus types which _meta_get handles transparently.
        metadata = dict(props.Get(_PLAYER_IFACE, 'Metadata', timeout=4) or {})
    return _build_reading(bus_name, names, status, metadata)


def _py_list():
    bus = _dbus.SessionBus()
    sessions = []
    for bus_name in _py_names(bus):
        try:
            status = _py_status(bus, bus_name)
        except Exception:  # noqa: BLE001
            status = 'PlayerNotRunning'
        sessions.append({'aumid': bus_name, 'name': aumid_friendly_name(bus_name), 'status': status})
    return sessions


# --- backend dispatch --------------------------------------------------------

def _read_now_playing(preferred_bus, timeout=5):
    # Prefer dbus-next (async; a fresh loop per call since run() is on Beam's
    # worker thread, wait_for bounding an unresponsive player). Fall back to the
    # synchronous dbus-python path (per-call Get timeouts bound it instead).
    try:
        if _HAS_DBUS_NEXT:
            return asyncio.run(asyncio.wait_for(_next_read_async(preferred_bus), timeout))
        if _HAS_DBUS_PYTHON:
            return _py_read(preferred_bus)
        return None
    except Exception as error:  # noqa: BLE001 - includes asyncio.TimeoutError
        _log_once("read_error", logging.INFO, "read failed: %s", error)
        logging.debug("mprismodule: read failed", exc_info=True)
        return None


def list_sessions(timeout=5):
    # For the preferences picker: enumerate the players currently on the bus.
    # Returns a list of {aumid, name, status} dicts (keys match the SMTC backend).
    try:
        if _HAS_DBUS_NEXT:
            return asyncio.run(asyncio.wait_for(_next_list_async(), timeout))
        if _HAS_DBUS_PYTHON:
            return _py_list()
        return []
    except Exception as error:  # noqa: BLE001 - includes asyncio.TimeoutError
        logging.debug("mprismodule: list_sessions failed: %s", error, exc_info=True)
        return []


def run_with_details(MaxTandaLength, preferred_aumid=''):
    backend = 'dbus-next' if _HAS_DBUS_NEXT else ('dbus-python' if _HAS_DBUS_PYTHON else 'none')
    details = {'route': 'mpris (%s)' % backend, 'aumid': '', 'appName': '', 'sessionCount': 0}

    if not _available():
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
