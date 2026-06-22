#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
# This Python file uses the following encoding: utf-8
#
# Played History / Session History
#
# Appends entries to a per-session file set: played tracks plus important
# non-track events (blackout, messages, playback state, ...). Independent of the
# player backends: it consumes the normalized SongObject / display state.
#
# A session is one Beam process/run. The logger is created once at startup; the
# session timestamp is fixed on the first write and only changes on the next
# Beam launch. Player/playback/blackout/display changes never start a new file
# set.
#
import csv
import logging
import os
import threading
import time

# Same identity logged again within this window is ignored, guarding against
# polling repeats. A genuine track identity change always logs immediately.
DUPLICATE_WINDOW_SECONDS = 30

# Playback states we treat as real transitions. Other values (e.g. 'Ambiguous',
# '') are ignored so they cannot flap the paused/stopped/resumed events.
_KNOWN_STATUSES = ('Playing', 'Paused', 'Stopped')

# CSV header. row_type distinguishes 'track' rows from 'event' rows; event rows
# fill timestamp/event and leave the track columns empty.
_CSV_HEADER = [
    'timestamp', 'row_type', 'player', 'mood', 'genre', 'album_artist',
    'artist', 'singer', 'title', 'year', 'album', 'file_path', 'event',
]


def _song_field(song, attribute):
    return str(getattr(song, attribute, '') or '').strip()


class PlayedHistoryLogger:
    #
    # One instance per running Beam (created with NowPlayingData). Writes come
    # from both the worker thread (tracks/playback) and the main thread (UI
    # events), so a lock serialises them.
    #
    def __init__(self):
        self._lock = threading.Lock()
        self._session_stamp = None
        self._txt_path = None
        self._csv_path = None
        self._m3u8_path = None

        self._last_identity = None
        # identity -> last log time, pruned to the duplicate window. Lets the
        # guard suppress a quick A -> B -> A reappearance, not just consecutive
        # polling repeats.
        self._recent = {}

        # Transition state so events are only emitted when state actually
        # changes (no event spam).
        self._last_player = None
        self._last_status = None

    ###############################################################
    # Public entry points
    ###############################################################

    #
    # Worker-thread polling path (NowPlayingData.processData). Safe to call on
    # every processed poll: dedup and transition detection are handled here.
    # Detects player/playback transitions first, then logs the track when
    # playing.
    #
    def observe(self, song, mood_name, player_name, status, settings):
        if not settings.getPlayedHistoryEnabled():
            return
        with self._lock:
            self._note_player(player_name, settings)
            self._note_playback(status, settings)
            if status == 'Playing' and song is not None:
                self._log_track(song, mood_name, player_name, settings)

    #
    # Main-thread event path (blackout, messages, display, ...). Records a
    # comment-style line in TXT and an event row in CSV. Never touches M3U8.
    # Callers are responsible for only calling on genuine state changes.
    #
    def log_event(self, event_text, settings):
        if not settings.getPlayedHistoryEnabled():
            return
        event_text = str(event_text or '').strip()
        if not event_text:
            return
        with self._lock:
            self._write_event(event_text, settings)

    ###############################################################
    # Transition detection (called under lock)
    ###############################################################

    def _note_player(self, player_name, settings):
        player_name = str(player_name or '').strip()
        if player_name == '':
            return
        if self._last_player is None:
            self._last_player = player_name
            self._write_event('Player selected: ' + player_name, settings)
        elif player_name != self._last_player:
            previous_player = self._last_player
            self._last_player = player_name
            self._write_event('Player changed: ' + previous_player + ' -> ' + player_name, settings)

    def _note_playback(self, status, settings):
        status = str(status or '').strip()
        if status not in _KNOWN_STATUSES or status == self._last_status:
            return

        previous_status = self._last_status
        self._last_status = status
        if status == 'Paused':
            self._write_event('Playback paused', settings)
        elif status == 'Stopped':
            self._write_event('Playback stopped', settings)
        elif status == 'Playing' and previous_status in ('Paused', 'Stopped'):
            self._write_event('Playback resumed', settings)

    ###############################################################
    # Track logging (called under lock)
    ###############################################################

    def _identity(self, song):
        return (
            _song_field(song, 'Title').lower(),
            _song_field(song, 'Artist').lower(),
            _song_field(song, 'FilePath').lower(),
        )

    def _is_duplicate(self, identity, now):
        # Same identity as the last logged track: skip consecutive polling
        # repeats so each played song is logged once.
        if identity == self._last_identity:
            return True
        # Identity changed, but the same track reappeared inside the window
        # (e.g. A -> B -> A); treat it as a repeat too.
        previous_time = self._recent.get(identity)
        return previous_time is not None and (now - previous_time) < DUPLICATE_WINDOW_SECONDS

    def _prune_recent(self, now):
        for identity in [key for key, when in self._recent.items()
                         if (now - when) >= DUPLICATE_WINDOW_SECONDS]:
            del self._recent[identity]

    def _log_track(self, song, mood_name, player_name, settings):
        # Require at least a title or file path so empty/placeholder reads don't
        # create noise entries.
        if not _song_field(song, 'Title') and not _song_field(song, 'FilePath'):
            return

        now = time.time()
        self._prune_recent(now)
        identity = self._identity(song)
        if self._is_duplicate(identity, now):
            return

        if not self._ensure_session(settings):
            return

        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        if settings.getPlayedHistoryTxtEnabled():
            self._append_txt_track(song, mood_name)
        if settings.getPlayedHistoryCsvEnabled():
            self._append_csv_track(song, mood_name, player_name, timestamp)
        if settings.getPlayedHistoryM3u8Enabled():
            self._append_m3u8(song)

        self._last_identity = identity
        self._recent[identity] = now
        logging.debug("PlayedHistory: logged track %s", identity)

    ###############################################################
    # Type / artist labels for human-readable output
    ###############################################################

    def _type_label(self, song, mood_name):
        if _song_field(song, 'IsCortina').lower() == 'yes':
            return 'Cortina'
        genre = _song_field(song, 'Genre')
        if genre:
            return genre
        if str(mood_name or '').strip():
            return str(mood_name).strip()
        return 'Track'

    def _artist_label(self, song):
        for attribute in ('AlbumArtist', 'Artist', 'Performer'):
            value = _song_field(song, attribute)
            if value:
                return value
        return ''

    def _build_txt_line(self, song, mood_name):
        label = self._type_label(song, mood_name)
        artist = self._artist_label(song)
        singer = _song_field(song, 'Singer')
        title = _song_field(song, 'Title')
        year = _song_field(song, 'Year')

        body = artist
        if singer:
            body = (body + ' - ' + singer).strip(' -')
        if title:
            separator = ' > ' if singer else ' - '
            body = (body + separator + title) if body else title
        if year:
            body = (body + ' ' + year).strip()

        return '[' + label + '] ' + body

    ###############################################################
    # Session bootstrap + low level writers (called under lock)
    ###############################################################

    def _ensure_session(self, settings):
        if self._session_stamp is not None:
            return True

        folder = settings.getPlayedHistoryFolder()
        try:
            os.makedirs(folder, exist_ok=True)
        except OSError as error:
            logging.error("PlayedHistory: cannot create folder '%s': %s", folder, error)
            return False

        now = time.localtime()
        self._session_stamp = time.strftime('%Y-%m-%d %H-%M', now)
        base = os.path.join(folder, 'Beam History ' + self._session_stamp)
        self._txt_path = base + '.txt'
        self._csv_path = base + '.csv'
        self._m3u8_path = base + '.m3u8'

        header_time = time.strftime('%a %b %d %Y %H:%M:%S', now)
        if settings.getPlayedHistoryTxtEnabled():
            self._write_txt_header(header_time)
        if settings.getPlayedHistoryCsvEnabled():
            self._write_csv_header()
        if settings.getPlayedHistoryM3u8Enabled():
            self._write_m3u8_header()

        # First line of content: a clear session marker in TXT/CSV (not M3U8).
        self._write_event('Beam session started', settings, _session_already_open=True)
        return True

    def _write_txt_header(self, header_time):
        try:
            with open(self._txt_path, 'a', encoding='utf-8') as txt_file:
                txt_file.write(header_time + '\n\n')
        except OSError as error:
            logging.error("PlayedHistory: cannot write TXT header: %s", error)

    def _write_csv_header(self):
        try:
            with open(self._csv_path, 'a', encoding='utf-8', newline='') as csv_file:
                csv.writer(csv_file).writerow(_CSV_HEADER)
        except OSError as error:
            logging.error("PlayedHistory: cannot write CSV header: %s", error)

    def _write_m3u8_header(self):
        try:
            with open(self._m3u8_path, 'a', encoding='utf-8') as m3u8_file:
                m3u8_file.write('#EXTM3U\n')
        except OSError as error:
            logging.error("PlayedHistory: cannot write M3U8 header: %s", error)

    def _append_txt_track(self, song, mood_name):
        try:
            with open(self._txt_path, 'a', encoding='utf-8') as txt_file:
                txt_file.write(self._build_txt_line(song, mood_name) + '\n')
        except OSError as error:
            logging.error("PlayedHistory: cannot append TXT entry: %s", error)

    def _append_csv_track(self, song, mood_name, player_name, timestamp):
        try:
            with open(self._csv_path, 'a', encoding='utf-8', newline='') as csv_file:
                csv.writer(csv_file).writerow([
                    timestamp,
                    'track',
                    str(player_name or ''),
                    str(mood_name or ''),
                    _song_field(song, 'Genre'),
                    _song_field(song, 'AlbumArtist'),
                    _song_field(song, 'Artist'),
                    _song_field(song, 'Singer'),
                    _song_field(song, 'Title'),
                    _song_field(song, 'Year'),
                    _song_field(song, 'Album'),
                    _song_field(song, 'FilePath'),
                    '',
                ])
        except OSError as error:
            logging.error("PlayedHistory: cannot append CSV entry: %s", error)

    #
    # Best effort only: tracks without a real local file path are skipped in the
    # playlist (but still logged to TXT/CSV). M3U8 stays a clean, playable list:
    # header + #EXTINF entries only, no comments/events.
    #
    def _append_m3u8(self, song):
        file_path = _song_field(song, 'FilePath')
        if not file_path or not os.path.isabs(file_path):
            return
        artist = self._artist_label(song)
        title = _song_field(song, 'Title')
        display = (artist + ' - ' + title).strip(' -') if title else artist
        try:
            with open(self._m3u8_path, 'a', encoding='utf-8') as m3u8_file:
                m3u8_file.write('#EXTINF:-1,' + display + '\n')
                m3u8_file.write(file_path + '\n')
        except OSError as error:
            logging.error("PlayedHistory: cannot append M3U8 entry: %s", error)

    #
    # Write a non-track event to TXT (comment line) and CSV (event row). Must be
    # called under the lock. _session_already_open avoids re-entering
    # _ensure_session while it is bootstrapping the session marker.
    #
    def _write_event(self, event_text, settings, _session_already_open=False):
        if not _session_already_open and not self._ensure_session(settings):
            return

        now = time.localtime()
        if settings.getPlayedHistoryTxtEnabled():
            try:
                with open(self._txt_path, 'a', encoding='utf-8') as txt_file:
                    txt_file.write('# ' + time.strftime('%H:%M:%S', now) + ' ' + event_text + '\n')
            except OSError as error:
                logging.error("PlayedHistory: cannot append TXT event: %s", error)

        if settings.getPlayedHistoryCsvEnabled():
            try:
                with open(self._csv_path, 'a', encoding='utf-8', newline='') as csv_file:
                    csv.writer(csv_file).writerow([
                        time.strftime('%Y-%m-%d %H:%M:%S', now),
                        'event',
                        str(self._last_player or ''),
                        '', '', '', '', '', '', '', '', '',
                        event_text,
                    ])
            except OSError as error:
                logging.error("PlayedHistory: cannot append CSV event: %s", error)

        logging.debug("PlayedHistory: logged event '%s'", event_text)
