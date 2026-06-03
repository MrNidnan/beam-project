# -*- encoding: utf-8 -*-
#    Copyright (C) 2014 Mikael Holber http://mywebsite.com
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
#    	- Initial release
#

from bin.songclass import SongObject
import logging

try:
	import win32gui
	import win32process
except Exception:
	win32gui = None
	win32process = None
from bin.modules.win.winutils import applicationrunning, get_process_ids

###############################################################
#
# Define operations
#
###############################################################

def collect_window_titles_for_pids(pids):
    # Collect visible top-level window titles owned by the given PIDs. Scoping by
    # PID (instead of matching a fixed window class) keeps detection working as
    # Spotify changes its Chromium window class - and avoids grabbing the titles
    # of other Chromium/Electron apps (Discord, VS Code, Slack) that share it.
    titles = []
    if win32gui is None or win32process is None or not pids:
        return titles

    def _callback(hwnd, _context):
        try:
            if not win32gui.IsWindowVisible(hwnd):
                return
            text = win32gui.GetWindowText(hwnd)
            if not text:
                return
            _thread_id, process_id = win32process.GetWindowThreadProcessId(hwnd)
            if process_id in pids:
                titles.append(text)
        except Exception:
            # A window can vanish mid-enumeration; skip it rather than abort.
            return

    win32gui.EnumWindows(_callback, None)
    return titles


def parse_track_title(title_text):
    # Spotify's window title is "Artist - Track" while playing. Local files may
    # only carry a track name, so fall back to an empty artist.
    try:
        artist, track = title_text.split(" - ", 1)
    except ValueError:
        artist = ''
        track = title_text
    return artist, track


def run(MaxTandaLength):
    playlist = []

    if not applicationrunning("Spotify.exe"):
        return playlist, 'PlayerNotRunning'

    try:
        spotify_pids = get_process_ids("Spotify.exe")
        titles = [title.strip() for title in collect_window_titles_for_pids(spotify_pids) if title.strip()]

        # No Spotify-owned window with a title: not playing/visible.
        if not titles:
            return playlist, 'PlayerNotRunning'

        # When paused the window title is just the app name ("Spotify",
        # "Spotify Premium", "Spotify Free"); a track title contains the song.
        track_titles = [title for title in titles if not title.startswith('Spotify')]
        if not track_titles:
            return playlist, 'Paused'

        artist, track = parse_track_title(track_titles[0])

        retSong = SongObject()
        retSong.Artist = artist
        retSong.Title = track
        playlist.append(retSong)

        return playlist, 'Playing'
    except Exception as e:
        logging.debug(e, exc_info=True)
        return playlist, 'PlayerNotRunning'
