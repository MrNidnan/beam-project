#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    Copyright (C) 2014 Mikael Holber http://http://www.beam-project.com
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
#       - Initial release
#
# This Python file uses the following encoding: utf-8
from copy import deepcopy
import logging

from bin.songclass import SongObject

try:
    import pythoncom
    import pywintypes
    import win32com.client
except ImportError:
    pass
from bin.modules.win.winutils import applicationrunning

###############################################################
#
# Define operations
#
###############################################################

PLAYER_STATE_STOPPED = 0
PLAYER_STATE_PLAYING = 1


def run(MaxTandaLength, last_playlist=None):

    playlist = []
    if last_playlist is None:
        last_playlist = []

    #
    # Player Status
    #
    if not applicationrunning("iTunes.exe"):
        playbackStatus = 'PlayerNotRunning'
        return playlist, playbackStatus
    else:
        pythoncom.CoInitialize()
        try:
            try:
                iTunes = win32com.client.gencache.EnsureDispatch ("iTunes.Application")
                current_track = getattr(iTunes, 'CurrentTrack', None)
                raw_player_state = getattr(iTunes, 'PlayerState', None)
                version = getattr(iTunes, 'Version', None)
                player_position = getattr(iTunes, 'PlayerPosition', None)
            except (AttributeError, pythoncom.com_error, pywintypes.com_error) as error:
                return handle_itunes_com_failure(error)

            logging.info(
                "Windows iTunes COM probe: version=%r player_state=%r player_position=%r current_track=%s",
                version,
                raw_player_state,
                player_position,
                describe_track(current_track),
            )

            #
            # Playback Status
            #
            playbackStatus = normalize_playback_status(raw_player_state, current_track, last_playlist)
            fallback_playlist = get_non_playing_fallback_playlist(
                playbackStatus,
                last_playlist,
                raw_player_state,
                version,
                current_track,
            )
            if fallback_playlist is not None:
                return fallback_playlist, playbackStatus

            #
            # Playback = Playing
            #
            playbackStatus = 'Playing'

            # Declare our position
            try:
                currentsong = iTunes.CurrentTrack.PlayOrderIndex
            except (AttributeError, pythoncom.com_error, pywintypes.com_error) as error:
                return handle_itunes_com_failure(error)
            playlistlength = currentsong + MaxTandaLength + 2  # Not available for iTunes
            searchsong = currentsong

            #
            # Full-read
            #
            while searchsong < playlistlength and searchsong < currentsong + MaxTandaLength + 2:
                try:
                    songObj = getSongAt(iTunes, searchsong)
                except (AttributeError, pythoncom.com_error, pywintypes.com_error) as error:
                    return handle_itunes_com_failure(error)
                playlist.append(songObj)
                searchsong = searchsong + 1
        finally:
            pythoncom.CoUninitialize()

    return playlist, playbackStatus

###############################################################
#
# Full read - Player specific
#
###############################################################

def normalize_playback_status(raw_player_state, current_track, last_playlist):
    if raw_player_state == PLAYER_STATE_PLAYING:
        return 'Playing'

    if raw_player_state == PLAYER_STATE_STOPPED:
        if current_track is None:
            return 'Stopped'

        if last_playlist and track_matches_song(current_track, last_playlist[0]):
            return 'Paused'

        if track_has_metadata(current_track):
            return 'Ambiguous'

        return 'Stopped'

    return 'Ambiguous'


def get_non_playing_fallback_playlist(playback_status, last_playlist, raw_player_state, version, current_track):
    if playback_status == 'Stopped':
        return []

    if playback_status == 'Paused':
        if last_playlist:
            return deepcopy(last_playlist)
        return []

    if playback_status == 'Ambiguous':
        logging.warning(
            "Windows iTunes COM state is ambiguous; preserving last playlist if available. player_state=%r version=%r track=%s",
            raw_player_state,
            version,
            describe_track(current_track),
        )
        if last_playlist:
            return deepcopy(last_playlist)
        return []

    return None


def track_matches_song(track, song):
    if track is None or song is None:
        return False

    return (
        safe_track_value(track, 'Artist') == str(getattr(song, 'Artist', '') or '')
        and safe_track_value(track, 'Name') == str(getattr(song, 'Title', '') or '')
        and safe_track_value(track, 'Album') == str(getattr(song, 'Album', '') or '')
    )


def track_has_metadata(track):
    if track is None:
        return False

    for field_name in ('Artist', 'Name', 'Album'):
        if safe_track_value(track, field_name).strip() != '':
            return True

    return False


def safe_track_value(track, attribute_name, default=''):
    if track is None:
        return default

    try:
        value = getattr(track, attribute_name)
    except Exception:
        return default

    if value is None:
        return default

    return str(value)


def describe_track(track):
    if track is None:
        return 'None'

    details = {
        'Artist': safe_track_value(track, 'Artist'),
        'Name': safe_track_value(track, 'Name'),
        'Album': safe_track_value(track, 'Album'),
        'PlayOrderIndex': safe_track_value(track, 'PlayOrderIndex'),
        'Kind': safe_track_value(track, 'Kind'),
    }

    return ', '.join('%s=%r' % (key, value) for key, value in details.items())


def handle_itunes_com_failure(error):
    app_running = applicationrunning("iTunes.exe")
    logging.warning(
        "Windows iTunes COM access failed; treating as %s. error=%r",
        'Ambiguous' if app_running else 'PlayerNotRunning',
        error,
        exc_info=True,
    )

    if app_running:
        return [], 'Ambiguous'

    return [], 'PlayerNotRunning'

def getSongAt(itunes, songPosition):
    retSong = SongObject()
    iTrack = itunes.CurrentTrack.Playlist.Tracks.Item(songPosition)

    retSong.Artist      = iTrack.Artist
    retSong.Album       = iTrack.Album
    retSong.Title       = iTrack.Name
    retSong.Genre       = iTrack.Genre
    retSong.Comment     = iTrack.Comment
    retSong.Composer    = iTrack.Composer
    retSong.Year        = iTrack.Year

    if iTrack.Kind in [1, 2]: # [ITTrackKindFile, TTrackKindCD]:
        iTrack = win32com.client.CastTo(iTrack, "IITFileOrCDTrack")

        retSong.AlbumArtist = iTrack.AlbumArtist
        retSong.FilePath   = iTrack.Location
    else:
        logging.warning("iTrack.Kind not in [ITTrackKindFile, TTrackKindCD]")

    #retSong._Singer     Defined by beam
    #retSong.Performer   = (Track.Performer) # Does not exist for iTunes?
    #retSong.IsCortina   Defined by beam
    #retSong.ModuleMessage = Not needed for iTunes
    
    return retSong

###############################################################
#
# Application running Windows-specific
#
###############################################################

def ApplicationRunning(AppName):
    from subprocess import Popen, PIPE
    cmd = 'WMIC PROCESS get Caption,Commandline,Processid'
    proc = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    for line in proc.stdout:
        if AppName in line:
            proc.kill()
            return True
    proc.kill()
    return False
