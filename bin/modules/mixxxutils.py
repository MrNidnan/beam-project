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

import urllib.request
from bin.songclass import SongObject
import sqlite3
import logging

###############################################################
#
# Define operations
#
###############################################################


# class MixxxSqlite:
#   sqlitePath = ""

def run(maxtandalength, lastlplaylist, sqlitePath):
    # lastplaylist gets updated only after next data processing
    # so local lastMixxxPlaylist gets used instead here

    sqliteconn = None
    try:
        sqliteconn = sqlite3.connect(sqlitePath)
        try:
            playlist = getplaylist(sqliteconn, maxtandalength)
            playback_status = 'Playing'

            '''
            # if (not the first round) and (playlist changed)
            if run.lastMixxxPlaylist and (playlist != run.lastMixxxPlaylist):
                if not run.currentmod:
                    # check for modification without switch
                    if (len(playlist) != len(run.lastMixxxPlaylist)) or (playlist[0] != run.lastMixxxPlaylist[1]):
                        run.currentmod = True
                        # remember the manually modified playlist to detect further switchover
                        logging.info("Auto-DJ modified")
                else:
                    # check for correction by a switchover (or skip)
                    if playlist[0] == run.lastMixxxPlaylist[1]:
                        # next switchover occured
                        run.currentmod = False
                        logging.info("Auto-DJ correced")

            if run.currentmod:
                # skip this round and return last playlist instead of the modifed
                playlist = run.lastMixxxPlaylist
                playback_status = 'Paused'
            else:
                playback_status = 'Playing'

            # remember the last playlist for the next round to detect modifications or switchover
            run.lastMixxxPlaylist = playlist
            '''

            return playlist, playback_status
        finally:
            sqliteconn.close()
    except Exception as e:
        # logging.error(e, exc_info=True)
        return [], "No database"


# Static for skipping refresh until next normal switch when the playlist got modified by hand
run.currentmod = False
run.lastMixxxPlaylist = None



###############################################################
#
# Full read - Player specific
#
###############################################################

def getplaylist(sqliteconn, maxtandalength):
    new_playlist = []

    # hidden = 1: Auto DJ
    # hidden = 2: History
    playlist_sql = \
        "select" \
        "       case pl.hidden" \
        "         when 2 THEN 1" \
        "         else pt.position+1" \
        "       end" \
        "       pos" \
        "     , li.id, li.artist, li.album, li.title, li.genre, li.comment, li.composer" \
        "     , li.year, li.album_artist, tl.location" \
        "  from Playlists pl" \
        "  join PlaylistTracks pt ON pt.playlist_id = pl.id" \
        "  join library li ON pt.track_id = li.id" \
        "  join track_locations tl ON tl.id = li.location" \
        " where (pl.id = (select max(id) from Playlists where hidden = 2)" \
        "        and pt.position = (select max(position) from PlaylistTracks where playlist_id=pl.id)" \
        "       )" \
        "    or (pl.hidden = 1)" \
        " order by pos" \

    cursor = sqliteconn.cursor()
    try:
        cursor.execute(playlist_sql)

        curr_track_arr = cursor.fetchmany(maxtandalength + 2)
        # if not empty and at least the last one in the history
        if len(curr_track_arr) > 0 and curr_track_arr[0][0] == 1:
            for currTrack in curr_track_arr:
                playlist_song = SongObject()

                playlist_song.Artist = currTrack[2]
                playlist_song.Album = currTrack[3]
                playlist_song.Title = currTrack[4]
                playlist_song.Genre = currTrack[5]
                playlist_song.Comment = currTrack[6]
                playlist_song.Composer = currTrack[7]
                playlist_song.Year = currTrack[8]
                # playlist_song._Singer Defined by beam
                playlist_song.AlbumArtist = currTrack[9]
                # playlist_song.Performer   = "Performer"
                # playlist_song.IsCortina   Defined by beam
                # !!! provisorisch direkt Path übergeben
                playlist_song.FilePath = currTrack[10]
                # playlist_song.FileUrl = "file://" + urllib.request.pathname2url(currTrack[10])

                # for compare of changes
                playlist_song.sanitizeFields()

                new_playlist.append(playlist_song)

    finally:
        cursor.close()

    return new_playlist


