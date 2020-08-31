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
#
#    Revision History:
#
#    Version 1.0
#    	- Initial release
#

from bin.songclass import SongObject
from bin.beamsettings import *
import sqlite3

###############################################################
#
# Define operations
#
###############################################################


class MixxxSqlite:
    sqlitePath = ""
    try:
        # can only get executed in MainThread
        if platform.system() == 'Windows':
            sqlitePath = os.path.expandvars(r'%LOCALAPPDATA%\Mixxx\mixxxdb.sqlite')
            # "C:\\Users\\<user>\\AppData\Local\\Mixxx\\mixxxdb.sqlite"
        if platform.system() == 'Linux':
            sqlitePath = os.path.expandvars(r'$HOME/.mixxx/mixxxdb.sqlite')
            # "/home/<username>/.mixxx/mixxxdb.sqlite"
            # Funktioniert nicht: r'~/.mixxx/mixxxdb.sqlite'
        if platform.system() == 'Darwin':
            # MacOS:
            sqlitePath = os.path.expandvars(r'$HOME/Library/Application\ Support/Mixxx/mixxxdb.sqlite')
    except Exception as e:
        print("MixxxSqlite() Exception:")
        print(e)
        print(sqlitePath)
        raise e

def run(maxtandalength, lastlplaylist):
    # print("mixxxSqlite.run()");
    sqlitepath = MixxxSqlite.sqlitePath
    # print("mixxxSqlite.run() connect to: " + sqlitepath)

    sqliteconn = sqlite3.connect(sqlitepath)
    try:
        playlist = getplaylist(sqliteconn, maxtandalength)

        # if not the first round and something changed
        if (len(lastlplaylist) > 0) and (playlist != lastlplaylist):
            if not run.currentmod:
                # check for modification without switch
                if (len(playlist) != len(lastlplaylist)) or (playlist[0] != lastlplaylist[1]):
                    run.currentmod = True
                    print("Auto-DJ modified")
            else:
                # check for correction (by a switchover)
                if playlist[0] == lastlplaylist[1]:
                    # next switchover occured
                    run.currentmod = False
                    print("Auto-DJ correced")

        if run.currentmod:
            # skip this round
            playlist = lastlplaylist
            # playback_status = 'Paused'

        # always playing, we don't know better
        playback_status = 'Playing'

    except Exception as e:
        print("mixxxSqlite.run() Exception")
        print(e)
        raise e
    finally:
        sqliteconn.close()

    return playlist, playback_status


# Static for skipping refresh until next normal switch
run.currentmod = False


###############################################################
#
# Full read - Player specific
#
###############################################################

def getplaylist(sqliteconn, maxtandalength):
    new_playlist = []
    playlist_sql = \
        "select CASE pt.position" \
        "  when (select max(position) from PlaylistTracks where playlist_id = pl.id) THEN 1" \
        "  ELSE pt.position+1" \
        "  END" \
        "     , li.id, li.artist, li.album, li.title, li.genre, li.comment, li.composer" \
        "     , li.year, li.album_artist, li.url" \
        "  from Playlists pl" \
        "  join PlaylistTracks pt ON pt.playlist_id = pl.id" \
        "  join library li ON pt.track_id = li.id" \
        " where pl.name = 'Auto DJ'" \
        " order by 1"

    cursor = sqliteconn.cursor()
    try:
        cursor.execute(playlist_sql)

        curr_track_arr = cursor.fetchmany(maxtandalength + 2)
        for currTrack in curr_track_arr:
            playlist_song = SongObject()

            playlist_song.Artist = getnotnull(currTrack[2])
            playlist_song.Album = getnotnull(currTrack[3])
            playlist_song.Title = getnotnull(currTrack[4])
            playlist_song.Genre = getnotnull(currTrack[5])
            playlist_song.Comment = getnotnull(currTrack[6])
            playlist_song.Composer = getnotnull(currTrack[7])
            playlist_song.Year = getnotnull(currTrack[8])
            # playlist_song._Singer Defined by beam
            playlist_song.AlbumArtist = getnotnull(currTrack[9])
            # playlist_song.Performer   = "Performer"
            # playlist_song.IsCortina   Defined by beam
            playlist_song.fileUrl = getnotnull(currTrack[10])

            new_playlist.append(playlist_song)

    except Exception as e:
        print("mixxxSqlite.getPlaylist() Exception")
        print(e)
        raise e
    finally:
        cursor.close()

    return new_playlist


def getnotnull(curr_str):
    if curr_str is not None:
        ret_str = curr_str
    else:
        ret_str = ""
    return ret_str
