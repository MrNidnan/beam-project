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
#    XX/XX/2014 Version 1.0
#       - Initial release
#
# This Python file uses the following encoding: utf-8
import logging
import platform
import time
from copy import deepcopy

from bin.backgroundassets import resolve_background_reference
from bin.beamsettings import beamSettings
from bin.mutagenutils import readCoverArtImage
from bin.songclass import SongObject, rule_matches

###############################################################
#
# LOAD MEDIA PLAYER MODULES
#
###############################################################

if platform.system() == 'Linux':
    from bin.modules.lin import audaciousmodule, rhythmboxmodule, clementinemodule, bansheemodule, spotifymodule, mixxxmodule, strawberrymodule
if platform.system() == 'Windows':
    from bin.modules.win import itunesmodule, winampmodule, mediamonkeymodule, spotifymodule, foobar2kmodule, mixxxmodule, jrivermodule
if platform.system() == 'Darwin':
    from bin.modules.mac import itunesmodule, decibelmodule, swinsianmodule, spotifymodule, voxmodule, cogmodule, embracemodule, mixxxmodule, jrivermodule, virtualdjmodule as macvirtualdjmodule

###############################################################
#
# LOAD DMX MODULES
#
###############################################################

if platform.system() == 'Linux' or platform.system() == 'Darwin':
    from bin.DMX import olamodule, dmxmodule
# if platform.system() == 'Windows':



###############################################################
#
# INIT
#
###############################################################

class NowPlayingData:

    def __init__(self):
        
        self.currentPlaylist = []
        self.rawPlaylist = []
        self.playlistChanged = False
        self.playlistchangetime = 0
        
        self.prevPlayedSong = SongObject()
        self.nextTandaSong = SongObject()
        self.prevReading = SongObject()

        self.SinceLastCortinaCount = 1
        self.TillNextCortinaCount = 0
        
        self.PlaybackStatus = ""
        self.StatusMessage = ""
        self.ModuleStatusMessage = ""
        self.PreviousPlaybackStatus = ""
        self.currentMood = None
        self.CurrentMoodName = ""
        self.PreviousMoodName = ""
        self.BackgroundPath = ""
        self.BackgroundLayers = {
            'base': {},
            'overlay': {},
        }
        self.RotateBackground = None
        # in processData() set to currentRule['RotateBackground'] or defaultMood['RotateBackground']
        self.rotatebackgroundseconds = None
        self.DisplayRows = []
        self.currentCoverArtImage = None
        self.currentCoverArtPath = ""
        self.DisplaySettings = {}

        self.convDict = dict()

    def _get_song_field_value(self, currentSong, field_name):
        attribute_name = str(field_name or '').replace('%', '').strip()
        if attribute_name in ('', '-'):
            return ''

        return str(getattr(currentSong, attribute_name, ''))

    def _build_background_layer(self, background_reference, rotate_background='no', rotate_timer=0, **extra_values):
        resolved_background = resolve_background_reference(background_reference)
        layer = {
            'available': bool(resolved_background['exists']),
            'kind': resolved_background['kind'],
            'scope': resolved_background['scope'],
            'reference': resolved_background['reference'],
            'canonicalReference': resolved_background['canonicalReference'],
            'relativePath': resolved_background['relativePath'],
            'sourcePath': resolved_background['absolutePath'],
            'rotate': rotate_background,
            'rotateTimer': rotate_timer,
        }
        layer.update(extra_values)
        return layer

    def _empty_background_layer(self):
        return self._build_background_layer('', 'no', 0)

    def _resolve_artist_background_layer(self, currentSettings, currentSong):
        if not currentSettings.getArtistBackgroundsEnabled():
            return self._empty_background_layer()

        artist_backgrounds = currentSettings.getArtistBackgrounds()
        default_field = artist_backgrounds.get('MatchField', '%AlbumArtist')
        fallback_field = artist_backgrounds.get('FallbackField', '%Artist')
        default_mode = str(artist_backgrounds.get('DefaultMode', 'blend')).strip().lower() or 'blend'
        default_opacity = int(artist_backgrounds.get('DefaultOpacity', 35))

        for mapping in currentSettings.getArtistBackgroundMappings():
            if str(mapping.get('Active', 'yes')).lower() != 'yes':
                continue

            field_name = mapping.get('Field', default_field)
            operator = mapping.get('Operator', mapping.get('Field2', 'is'))
            comparison_value = mapping.get('Value', mapping.get('Field3', ''))
            field_value = self._get_song_field_value(currentSong, field_name)
            matched_field = field_name

            if field_value == '' and fallback_field and fallback_field != field_name:
                field_value = self._get_song_field_value(currentSong, fallback_field)
                matched_field = fallback_field

            if not rule_matches(field_value, operator, comparison_value):
                continue

            mode = str(mapping.get('Mode', default_mode)).strip().lower() or default_mode
            if mode not in ('blend', 'replace', 'off'):
                mode = default_mode

            overlay_layer = self._build_background_layer(
                mapping.get('Background', ''),
                mapping.get('RotateBackground', 'no'),
                mapping.get('RotateTimer', 120),
                name=mapping.get('Name', ''),
                mode=mode,
                opacity=int(mapping.get('Opacity', default_opacity)),
                field=field_name,
                matchedField=matched_field,
                operator=operator,
                value=comparison_value,
            )

            if overlay_layer['available'] and mode != 'off':
                logging.debug(
                    "Artist background matched '%s' using %s='%s'",
                    overlay_layer.get('name', ''),
                    matched_field,
                    field_value,
                )
                return overlay_layer

            return self._empty_background_layer()

        return self._empty_background_layer()

    def _get_current_song_for_display(self):
        if self.currentPlaylist and len(self.currentPlaylist) >= 1:
            return self.currentPlaylist[0]
        return SongObject()

    def _build_display_rows_for_settings(self, display_settings):
        display_rows = []
        for i in range(0, len(display_settings)):
            display_rows.append('')

        for j in range(0, len(display_settings)):
            my_display = display_settings[j]
            display_value = str(my_display['Field'])
            for key in sorted(list(self.convDict.keys()), reverse=True):
                display_value = display_value.replace(str(key), str(self.convDict[key]))
            if my_display['HideControl'] == "" and my_display['Active'] == "yes":
                display_rows[j] = display_value
            else:
                hide_control_eval = str(my_display['HideControl'])
                for key in sorted(list(self.convDict.keys()), reverse=True):
                    hide_control_eval = hide_control_eval.replace(str(key), str(self.convDict[key]))
                if not hide_control_eval == "" and my_display['Active'] == "yes":
                    display_rows[j] = display_value
                else:
                    display_rows[j] = ""

        return display_rows

    def _resolve_cover_art_state_for_settings(self, display_settings, display_rows, current_song):
        cover_art_path = ""
        cover_art_image = None
        for j in range(0, len(display_settings)):
            my_display = display_settings[j]
            display_value = str(my_display['Field'])
            if str(display_value).strip() == "%CoverArt" and display_rows[j] != "":
                cover_art_path = current_song.FilePath
                if cover_art_path != "":
                    cover_art_image = readCoverArtImage(cover_art_path)
                break

        return cover_art_path, cover_art_image

    def build_display_state_for_mood(self, currentSettings, mood, current_song=None):
        if current_song is None:
            current_song = self._get_current_song_for_display()

        display_settings = mood['Display']
        base_background_layer = self._build_background_layer(
            mood.get('Background', ''),
            mood.get('RotateBackground', 'no'),
            mood.get('RotateTimer', 120),
            mode='base',
            name=mood['Name'],
        )
        overlay_background_layer = self._resolve_artist_background_layer(currentSettings, current_song)
        background_layers = {
            'base': base_background_layer,
            'overlay': overlay_background_layer,
        }

        active_background_layer = base_background_layer
        if overlay_background_layer.get('available') and overlay_background_layer.get('mode') == 'replace':
            active_background_layer = overlay_background_layer

        display_rows = self._build_display_rows_for_settings(display_settings)
        cover_art_path, cover_art_image = self._resolve_cover_art_state_for_settings(display_settings, display_rows, current_song)

        return {
            'currentMood': mood,
            'currentMoodName': mood['Name'],
            'displaySettings': display_settings,
            'displayRows': display_rows,
            'backgroundLayers': background_layers,
            'backgroundPath': active_background_layer.get('sourcePath', ''),
            'rotateBackground': active_background_layer.get('rotate', 'no'),
            'rotateBackgroundSeconds': active_background_layer.get('rotateTimer', 0),
            'coverArtPath': cover_art_path,
            'coverArtImage': cover_art_image,
        }

    #
    # Dispatches to the selected module run()
    # gets called by DisplayData.readDataThread()
    # started by DisplayData.updateData() by startWorker()
    #
    def readData(self, currentSettings):
        logging.debug("Start updating data... " + time.strftime("%H:%M:%S"))
        # Save previous state
        self.PreviousPlaybackStatus = self.PlaybackStatus
        self.ModuleStatusMessage = ""
        previous_playlist = []

        # try:
        if self.currentPlaylist:
            previous_playlist = deepcopy(self.currentPlaylist)
            self.LastRead = deepcopy(self.currentPlaylist)
        else:
            self.currentPlaylist = []
            self.LastRead = SongObject()
        # except Exception as e:
        #     logging.warning("NowPlayingData.ExtractPlaylistInfo(deepcopy):")
        #     logging.warning(e)
        #     self.LastRead = SongObject()

        ###############################################################
        #
        # Extract data using the player module
        #
        ###############################################################
        # WINDOWS
        if platform.system() == 'Windows':
            if currentSettings.getSelectedModuleName() == 'iTunes':
                self.currentPlaylist, self.PlaybackStatus = itunesmodule.run(currentSettings.getMaxTandaLength())
            if currentSettings.getSelectedModuleName() == 'MediaMonkey':
                self.currentPlaylist, self.PlaybackStatus = mediamonkeymodule.run(currentSettings.getMaxTandaLength(), self.rawPlaylist)
            if currentSettings.getSelectedModuleName() == 'Spotify':
                self.currentPlaylist, self.PlaybackStatus =spotifymodule.run(currentSettings.getMaxTandaLength())
            if currentSettings.getSelectedModuleName() == 'Foobar2000':
                self.currentPlaylist, self.PlaybackStatus =foobar2kmodule.run(currentSettings.getMaxTandaLength())
            try: #required due to loaded modules
                if currentSettings.getSelectedModuleName() == 'Winamp/AIMP':
                    self.currentPlaylist, self.PlaybackStatus = winampmodule.run(currentSettings.getMaxTandaLength())
            except Exception as e:
                logging.error(e, exc_info=True)                # ???
                pass
            if currentSettings.getSelectedModuleName()== 'Mixxx':
                self.currentPlaylist, self.PlaybackStatus, mixxx_details = mixxxmodule.run_with_details(currentSettings.getMaxTandaLength(), self.rawPlaylist)
                self._apply_mixxx_details(mixxx_details)
            if currentSettings.getSelectedModuleName() == 'JRiver':
                self.currentPlaylist, self.PlaybackStatus = jrivermodule.run(currentSettings.getMaxTandaLength())


        # LINUX
        if platform.system() == 'Linux':
            if currentSettings.getSelectedModuleName() == 'Audacious':
                self.currentPlaylist, self.PlaybackStatus = audaciousmodule.run(currentSettings.getMaxTandaLength())
            if currentSettings.getSelectedModuleName() == 'Rhythmbox':
                self.currentPlaylist, self.PlaybackStatus = rhythmboxmodule.run(currentSettings.getMaxTandaLength())
            if currentSettings.getSelectedModuleName() == 'Clementine':
                self.currentPlaylist, self.PlaybackStatus = clementinemodule.run(currentSettings.getMaxTandaLength())
            if currentSettings.getSelectedModuleName() == 'Banshee':
                self.currentPlaylist, self.PlaybackStatus = bansheemodule.run(currentSettings.getMaxTandaLength())
            if currentSettings.getSelectedModuleName() == 'Spotify':
                self.currentPlaylist, self.PlaybackStatus = spotifymodule.run(currentSettings.getMaxTandaLength())
            if currentSettings.getSelectedModuleName() == 'Mixxx':
                self.currentPlaylist, self.PlaybackStatus, mixxx_details = mixxxmodule.run_with_details(currentSettings.getMaxTandaLength(), self.rawPlaylist)
                self._apply_mixxx_details(mixxx_details)
            if currentSettings.getSelectedModuleName() == 'Strawberry':
                self.currentPlaylist, self.PlaybackStatus = strawberrymodule.run(currentSettings.getMaxTandaLength())


        # Mac OS X
        if platform.system() == 'Darwin':
            if currentSettings.getSelectedModuleName() == 'iTunes':
                self.currentPlaylist, self.PlaybackStatus  = itunesmodule.run(currentSettings.getMaxTandaLength(), self.rawPlaylist)
            if currentSettings.getSelectedModuleName() == 'Decibel':
                self.currentPlaylist, self.PlaybackStatus  = decibelmodule.run(currentSettings.getMaxTandaLength())
            if currentSettings.getSelectedModuleName() == 'Swinsian':
                self.currentPlaylist, self.PlaybackStatus  = swinsianmodule.run(currentSettings.getMaxTandaLength())
            if currentSettings.getSelectedModuleName() == 'Spotify':
                self.currentPlaylist, self.PlaybackStatus  = spotifymodule.run(currentSettings.getMaxTandaLength())
            if currentSettings.getSelectedModuleName() == 'Vox':
                    self.currentPlaylist, self.PlaybackStatus  = voxmodule.run(currentSettings.getMaxTandaLength())
            if currentSettings.getSelectedModuleName() == 'Cog':
                    self.currentPlaylist, self.PlaybackStatus  = cogmodule.run(currentSettings.getMaxTandaLength())
            if currentSettings.getSelectedModuleName() == 'Embrace':
                    self.currentPlaylist, self.PlaybackStatus  = embracemodule.run(currentSettings.getMaxTandaLength(), self.rawPlaylist)
            if currentSettings.getSelectedModuleName() == 'Mixxx':
                self.currentPlaylist, self.PlaybackStatus, mixxx_details = mixxxmodule.run_with_details(currentSettings.getMaxTandaLength(), self.rawPlaylist)
                self._apply_mixxx_details(mixxx_details)
            if currentSettings.getSelectedModuleName() == 'JRiver':
                self.currentPlaylist, self.PlaybackStatus = jrivermodule.run(currentSettings.getMaxTandaLength())
            if currentSettings.getSelectedModuleName() == 'VirtualDJ':
                self.currentPlaylist, self.PlaybackStatus = macvirtualdjmodule.run(currentSettings.getMaxTandaLength(), self.rawPlaylist)

        # for all platforms
        if currentSettings.getSelectedModuleName() == 'VirtualDJ' and platform.system() == 'Windows':
            from bin.modules import virtualdjmodule
            self.currentPlaylist, self.PlaybackStatus = virtualdjmodule.run(currentSettings.getMaxTandaLength(), self.rawPlaylist)

        if currentSettings.getSelectedModuleName() == 'Icecast':
            from bin.modules import icecastmodule
            self.currentPlaylist, self.PlaybackStatus = icecastmodule.run(currentSettings.getMaxTandaLength(), self.rawPlaylist)

        if (not self.currentPlaylist) and self.PlaybackStatus == 'Paused' and previous_playlist:
            self.currentPlaylist = deepcopy(previous_playlist)

        # sanitizeFields()
        for song in self.currentPlaylist[:]:
            song.sanitizeFields()

        #
        # Set status message
        #
        self.StatusMessage = self.PlaybackStatus
        if self.currentPlaylist and len(self.currentPlaylist) >= 1 and self.currentPlaylist[0].ModuleMessage != "":
            # append ModulMessage
            self.StatusMessage = self.StatusMessage + ", " + self.currentPlaylist[0].ModuleMessage
        elif self.ModuleStatusMessage != "":
            self.StatusMessage = self.StatusMessage + ", " + self.ModuleStatusMessage

        #
        # Save the reading
        #
        if (self.rawPlaylist == self.currentPlaylist) and (self.PreviousPlaybackStatus == self.PlaybackStatus):
            self.playlistChanged  = False
        else:
            self.rawPlaylist = deepcopy(self.currentPlaylist)
            self.playlistChanged  = True
            self.playlistchangetime = time.time()

        logging.debug("Data extracted from " + currentSettings.getSelectedModuleName() + ": " + self.StatusMessage)

        if self.PreviousPlaybackStatus == "":
            self.PreviousPlaybackStatus = self.PlaybackStatus

        return self

    def _apply_mixxx_details(self, mixxx_details):
        if not mixxx_details:
            self.ModuleStatusMessage = ""
            return

        self.ModuleStatusMessage = mixxxmodule.mixxxutils.describe_mixxx_status_message(mixxx_details)

    ###############################################################
    #
    # Dispatches to the selected module run()
    # gets called by DisplayData.processDataThread()
    # started by DisplayData.processData() by startWorker()
    #
    # Apply rules and moods
    # Create display strings
    #
    ###############################################################
    def processData(self, currentSettings):
        for i in range(0, len(self.currentPlaylist)):
            self.currentPlaylist[i].applySongRules(currentSettings.getRules())

        ########################################################
        # IGNORE SONGS, remove ignored songs
        ########################################################
        for item in self.currentPlaylist[:]:
            if item.IgnoreSong == "yes":
                self.currentPlaylist.remove(item)

        ########################################################
        # PREVIOUS SONG ANALYSIS
        ########################################################
        try:
            if self.LastRead[0] == self.currentPlaylist[0]:
                pass
            else:
                # Calculate the number of songs that were payed since last cortina
                if self.currentPlaylist[0].IsCortina == "yes":
                    self.SinceLastCortinaCount = 0
                else:
                    self.SinceLastCortinaCount = self.SinceLastCortinaCount + 1

                self.prevPlayedSong = self.LastRead[0]
        except:
            pass
        
        ########################################################
        # Create NextTanda
        ########################################################
        self.nextTandaSong = None
        self.TillNextCortinaCount = 0
        
        for i in range(0, len(self.currentPlaylist)-1):
            # Check if song is cortina
            if self.currentPlaylist[i].IsCortina == "yes" and not self.currentPlaylist[i+1].IsCortina == "yes":
                self.nextTandaSong = deepcopy(self.currentPlaylist[i+1])
                self.nextTandaSong.applySongRules(currentSettings.getRules())
                break
            else:
                self.TillNextCortinaCount = self.TillNextCortinaCount + 1


        ###############################################################
        #
        # MOOD RULES - apply only to current song
        #
        ###############################################################
        if self.currentPlaylist and len(self.currentPlaylist) >= 1:
            currentSong = self.currentPlaylist[0]
        else:
            currentSong = SongObject()
        
        preserved_song_context = (
            self.PlaybackStatus == 'Paused'
            and self.currentPlaylist and isinstance(self.LastRead, list) and self.LastRead
            and self.currentPlaylist[0] == self.LastRead[0]
        )

        # Keep the active song mood until a new song replaces it.
        if self.PlaybackStatus == 'Playing' or preserved_song_context:
            MoodStatus = "Playing"
        else:
            MoodStatus = "Not Playing"
        
        applyidx = 0 # index default mood
        for i in range(1, len(currentSettings.getMoods())):
            currentMood = currentSettings.getMoods()[i]
            try:
                if currentMood['Type'] == 'Mood' and currentMood['Active'] == 'yes' and str(currentMood['PlayState']) == str(MoodStatus):
                    # Only apply Mood for current song
                    if currentMood['Field2'] == 'is':
                        if eval(str(currentMood['Field1']).replace("%"," currentSong.")).lower() == str(currentMood['Field3']).lower():
                            applyidx = i
                    if currentMood['Field2'] == 'is not':
                        if eval(str(currentMood['Field1']).replace("%"," currentSong.")).lower() not in str("["+currentMood['Field3'].lower()+"]"):
                            applyidx = i
                    if currentMood['Field2'] == 'contains':
                        if str(currentMood['Field3']).lower() in eval(str(currentMood['Field1']).replace("%"," currentSong.")).lower():
                            applyidx = i
            except Exception as e:
                logging.info(e, exc_info=True)

        #
        # Apply mood layout and background or default mood
        #
        # By EditMoodDialog
        mood_display_state = self.build_display_state_for_mood(currentSettings, currentSettings.getMoods()[applyidx], currentSong)
        self.currentMood = mood_display_state['currentMood']
        self.CurrentMoodName = mood_display_state['currentMoodName']
        self.DisplaySettings = mood_display_state['displaySettings']
        self.DisplayRows = mood_display_state['displayRows']
        self.BackgroundLayers = mood_display_state['backgroundLayers']
        self.BackgroundPath = mood_display_state['backgroundPath']
        self.RotateBackground = mood_display_state['rotateBackground']
        self.rotatebackgroundseconds = mood_display_state['rotateBackgroundSeconds']
        self.currentCoverArtPath = mood_display_state['coverArtPath']
        self.currentCoverArtImage = mood_display_state['coverArtImage']
        self.currentU1DMXcolour = self.currentMood['U1DMXcolour']
        self.currentU2DMXcolour = self.currentMood['U2DMXcolour']
        u1 = beamSettings._Universe1
        colourlist = []
        try:
            colourlist = self.currentMood['U1DMXcolours']
        except:
            colourlist.append(self.currentMood['U1DMXcolour'])
        finally:
            u1.setAllFixtureColours(colourlist)

        u2 = beamSettings._Universe2
        colourlist = []
        try:
            colourlist = self.currentMood['U2DMXcolours']
        except:
            colourlist.append(self.currentMood['U2DMXcolour'])
        finally:
            u2.setAllFixtureColours(colourlist)

        #first, update the conversion dictionary
        self.updateConversionDisctionary()
        mood_display_state = self.build_display_state_for_mood(currentSettings, self.currentMood, currentSong)
        self.DisplaySettings = mood_display_state['displaySettings']
        self.DisplayRows = mood_display_state['displayRows']
        self.BackgroundLayers = mood_display_state['backgroundLayers']
        self.BackgroundPath = mood_display_state['backgroundPath']
        self.RotateBackground = mood_display_state['rotateBackground']
        self.rotatebackgroundseconds = mood_display_state['rotateBackgroundSeconds']
        self.currentCoverArtPath = mood_display_state['coverArtPath']
        self.currentCoverArtImage = mood_display_state['coverArtImage']

        logging.debug("...data got filtered: ")
    
        #######################################
        # Run DMX command
        #######################################
        device = None
        currentU1DMXcolour = self.currentU1DMXcolour
        currentU2DMXcolour = self.currentU2DMXcolour
        if platform.system() == 'Linux' or platform.system() == 'Darwin':
            if beamSettings._oladIsRunning :
                colourpattern = u1.FixturePatterns()
                if (0 < len(colourpattern)): olamodule.sendDMXrequest(1, colourpattern)
                logging.debug("... U1 DMX colour: " + str(colourpattern))
                colourpattern =  u2.FixturePatterns()
                if (0 < len(colourpattern)): olamodule.sendDMXrequest(2, colourpattern)
                logging.debug("... U2 DMX colour: " + str(colourpattern))

        if platform.system() == 'Windows':
            pass


########################################################
# Conversion dictionary
########################################################

    def updateConversionDisctionary(self):
        self.convDict = dict()

        #CurrentSong
        if self.currentPlaylist and len(self.currentPlaylist) >= 1:
            self.convDict['%Artist']        = self.currentPlaylist[0].Artist
            self.convDict['%Album']         = self.currentPlaylist[0].Album
            self.convDict['%Title']         = self.currentPlaylist[0].Title
            self.convDict['%Genre']         = self.currentPlaylist[0].Genre
            self.convDict['%Comment']       = self.currentPlaylist[0].Comment
            self.convDict['%Composer']      = self.currentPlaylist[0].Composer
            self.convDict['%Year']          = self.currentPlaylist[0].Year
            self.convDict['%Singer']        = self.currentPlaylist[0].Singer
            self.convDict['%AlbumArtist']   = self.currentPlaylist[0].AlbumArtist
            self.convDict['%Performer']     = self.currentPlaylist[0].Performer
            self.convDict['%IsCortina']     = self.currentPlaylist[0].IsCortina
            self.convDict['%FilePath']      = self.currentPlaylist[0].FilePath
            self.convDict['%CoverArt']      = self.currentPlaylist[0].FilePath
        else:
            self.convDict['%Artist']        = ""
            self.convDict['%Album']         = ""
            self.convDict['%Title']         = ""
            self.convDict['%Genre']         = ""
            self.convDict['%Comment']       = ""
            self.convDict['%Composer']      = ""
            self.convDict['%Year']          = ""
            self.convDict['%Singer']        = ""
            self.convDict['%AlbumArtist']   = ""
            self.convDict['%Performer']     = ""            
            self.convDict['%IsCortina']     = ""
            self.convDict['%FilePath']      = ""
            self.convDict['%CoverArt']      = ""


        #PreviousSong
        if self.prevPlayedSong:
            self.convDict['%PreviousArtist']        = self.prevPlayedSong.Artist
            self.convDict['%PreviousAlbum']         = self.prevPlayedSong.Album
            self.convDict['%PreviousTitle']         = self.prevPlayedSong.Title
            self.convDict['%PreviousGenre']         = self.prevPlayedSong.Genre
            self.convDict['%PreviousComment']       = self.prevPlayedSong.Comment
            self.convDict['%PreviousComposer']      = self.prevPlayedSong.Composer
            self.convDict['%PreviousYear']          = self.prevPlayedSong.Year
            self.convDict['%PreviousSinger']        = self.prevPlayedSong.Singer
            self.convDict['%PreviousAlbumArtist']   = self.prevPlayedSong.AlbumArtist
            self.convDict['%PreviousPerformer']     = self.prevPlayedSong.Performer
            self.convDict['%PreviousIsCortina']     = self.prevPlayedSong.IsCortina
        else:
            self.convDict['%PreviousArtist']        = ""
            self.convDict['%PreviousAlbum']         = ""
            self.convDict['%PreviousTitle']         = ""
            self.convDict['%PreviousGenre']         = ""
            self.convDict['%PreviousComment']       = ""
            self.convDict['%PreviousComposer']      = ""
            self.convDict['%PreviousYear']          = ""
            self.convDict['%PreviousSinger']        = ""
            self.convDict['%PreviousAlbumArtist']   = ""
            self.convDict['%PreviousPerformer']     = ""
            self.convDict['%PreviousIsCortina']     = ""
            
        #NextSong
        if self.currentPlaylist and len(self.currentPlaylist) >= 2:
            self.convDict['%NextArtist']        = self.currentPlaylist[1].Artist
            self.convDict['%NextAlbum']         = self.currentPlaylist[1].Album
            self.convDict['%NextTitle']         = self.currentPlaylist[1].Title
            self.convDict['%NextGenre']         = self.currentPlaylist[1].Genre
            self.convDict['%NextComment']       = self.currentPlaylist[1].Comment
            self.convDict['%NextComposer']      = self.currentPlaylist[1].Composer
            self.convDict['%NextYear']          = self.currentPlaylist[1].Year
            self.convDict['%NextSinger']        = self.currentPlaylist[1].Singer
            self.convDict['%NextAlbumArtist']   = self.currentPlaylist[1].AlbumArtist
            self.convDict['%NextPerformer']     = self.currentPlaylist[1].Performer
            self.convDict['%NextIsCortina']     = self.currentPlaylist[1].IsCortina
        else:
            self.convDict['%NextArtist']        = ""
            self.convDict['%NextAlbum']         = ""
            self.convDict['%NextTitle']         = ""
            self.convDict['%NextGenre']         = ""
            self.convDict['%NextComment']       = ""
            self.convDict['%NextComposer']      = ""
            self.convDict['%NextYear']          = ""
            self.convDict['%NextSinger']        = ""
            self.convDict['%NextAlbumArtist']   = ""
            self.convDict['%NextPerformer']     = ""
            self.convDict['%NextIsCortina']     = ""
        
        #NextTanda
        if self.nextTandaSong:
            self.convDict['%NextTandaArtist']        = self.nextTandaSong.Artist
            self.convDict['%NextTandaAlbum']         = self.nextTandaSong.Album
            self.convDict['%NextTandaTitle']         = self.nextTandaSong.Title
            self.convDict['%NextTandaGenre']         = self.nextTandaSong.Genre
            self.convDict['%NextTandaComment']       = self.nextTandaSong.Comment
            self.convDict['%NextTandaComposer']      = self.nextTandaSong.Composer
            self.convDict['%NextTandaYear']          = self.nextTandaSong.Year
            self.convDict['%NextTandaSinger']        = self.nextTandaSong.Singer
            self.convDict['%NextTandaAlbumArtist']   = self.nextTandaSong.AlbumArtist
            self.convDict['%NextTandaPerformer']     = self.nextTandaSong.Performer
            self.convDict['%NextTandaIsCortina']     = self.nextTandaSong.IsCortina        
        else:
            self.convDict['%NextTandaArtist']        = ""
            self.convDict['%NextTandaAlbum']         = ""
            self.convDict['%NextTandaTitle']         = ""
            self.convDict['%NextTandaGenre']         = ""
            self.convDict['%NextTandaComment']       = ""
            self.convDict['%NextTandaComposer']      = ""
            self.convDict['%NextTandaYear']          = ""
            self.convDict['%NextTandaSinger']        = ""
            self.convDict['%NextTandaAlbumArtist']   = ""
            self.convDict['%NextTandaPerformer']     = ""
            self.convDict['%NextTandaIsCortina']     = ""        

        #date and time
        
        self.convDict['%Hour']      = time.strftime("%H")
        self.convDict['%Min']       = time.strftime("%M")
        try:
            self.convDict['%DateDay']       = time.strftime("%e") # Does not work on Windows
        except:
            self.convDict['%DateDay']       = time.strftime("%d")

        self.convDict['%DateMonth']     = time.strftime("%m")
        self.convDict['%DateYear']      = time.strftime("%Y")
        self.convDict['%LongDate']  = time.strftime("%d %B %Y")
        self.convDict['%ShortDate'] = time.strftime("%Y.%m.%d")

        #Track number in a tanda
        self.convDict['%SongsSinceLastCortina'] = self.SinceLastCortinaCount
        self.convDict['%CurrentTandaSongsRemaining'] = self.TillNextCortinaCount - 1
            #current tanda count
        self.convDict['%CurrentTandaLength'] = self.SinceLastCortinaCount + self.TillNextCortinaCount - 1 

    def isDisplayTimeExpired(self):
        timenow = time.time()
        timechanged = self.playlistchangetime
        displaytimer = 0;
        if self.currentMood:
            displaytimer = int(self.currentMood['DisplayTimer'])

        if displaytimer <= 0 or timechanged <= 0:
            return False

        isexpired = timenow > (timechanged + displaytimer)

        return isexpired



