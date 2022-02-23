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
import platform, os, sys
import time

from bin.beamutils import getBeamHomePath
from bin.mutagenutils import readCoverArtImage
from bin.songclass import SongObject
from copy import deepcopy

###############################################################
#
# LOAD MEDIA PLAYER MODULES
#
###############################################################

if platform.system() == 'Linux':
    from bin.modules.lin import audaciousmodule, rhythmboxmodule, clementinemodule, bansheemodule, spotifymodule, mixxxmodule
if platform.system() == 'Windows':
    from bin.modules.win import itunesmodule, winampmodule, mediamonkeymodule, spotifymodule, foobar2kmodule, mixxxmodule
if platform.system() == 'Darwin':
    from bin.modules.mac import itunesmodule, decibelmodule, swinsianmodule, spotifymodule, voxmodule, cogmodule, embracemodule, mixxxmodule
from bin.modules import icecastmodule




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
        
        self.prevPlayedSong = SongObject()
        self.nextTandaSong = SongObject()
        self.prevReading = SongObject()
        
        
        self.SinceLastCortinaCount = 1
        self.TillNextCortinaCount = 0
        
        self.PlaybackStatus = ""
        self.StatusMessage = ""
        self.PreviousPlaybackStatus = ""
        self.CurrentMood =""
        self.PreviousMood = ""
        self.BackgroundPath = ""
        self.RotateBackground = ""
        self.RotateTimer = []
        self.DisplayRows = []
        self.currentCoverArtImage = None
        self.currentCoverArtPath = ""
        self.DisplaySettings = {}

        self.convDict = dict()


    def readData(self, currentSettings):
        logging.debug("Start updating data... " + time.strftime("%H:%M:%S"))
        # Save previous state
        self.PreviousPlaybackStatus = self.PlaybackStatus

        # try:
        if self.currentPlaylist:
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
            if currentSettings._moduleSelected == 'iTunes':
                self.currentPlaylist, self.PlaybackStatus = itunesmodule.run(currentSettings._maxTandaLength)
            if currentSettings._moduleSelected == 'MediaMonkey':
                self.currentPlaylist, self.PlaybackStatus = mediamonkeymodule.run(currentSettings._maxTandaLength, self.rawPlaylist)
            if currentSettings._moduleSelected == 'Spotify':
                self.currentPlaylist, self.PlaybackStatus =spotifymodule.run(currentSettings._maxTandaLength)
            if currentSettings._moduleSelected == 'Foobar2000':
                self.currentPlaylist, self.PlaybackStatus =foobar2kmodule.run(currentSettings._maxTandaLength)
            try: #required due to loaded modules
                if currentSettings._moduleSelected == 'Winamp':
                    self.currentPlaylist, self.PlaybackStatus = winampmodule.run(currentSettings._maxTandaLength)
            except:
                # ???
                pass
            if currentSettings._moduleSelected == 'Mixxx':
                self.currentPlaylist, self.PlaybackStatus = mixxxmodule.run(currentSettings._maxTandaLength, self.rawPlaylist)

        # LINUX
        if platform.system() == 'Linux':
            if currentSettings._moduleSelected == 'Audacious':
                self.currentPlaylist, self.PlaybackStatus = audaciousmodule.run(currentSettings._maxTandaLength)
            if currentSettings._moduleSelected == 'Rhythmbox':
                self.currentPlaylist, self.PlaybackStatus = rhythmboxmodule.run(currentSettings._maxTandaLength)
            if currentSettings._moduleSelected == 'Clementine':
                self.currentPlaylist, self.PlaybackStatus = clementinemodule.run(currentSettings._maxTandaLength)
            if currentSettings._moduleSelected == 'Banshee':
                self.currentPlaylist, self.PlaybackStatus = bansheemodule.run(currentSettings._maxTandaLength)
            if currentSettings._moduleSelected == 'Spotify':
                self.currentPlaylist, self.PlaybackStatus = spotifymodule.run(currentSettings._maxTandaLength)
            if currentSettings._moduleSelected == 'Mixxx':
                self.currentPlaylist, self.PlaybackStatus = mixxxmodule.run(currentSettings._maxTandaLength, self.rawPlaylist)

        # Mac OS X
        if platform.system() == 'Darwin':
            if currentSettings._moduleSelected == 'iTunes':
                self.currentPlaylist, self.PlaybackStatus  = itunesmodule.run(currentSettings._maxTandaLength, self.rawPlaylist)
            if currentSettings._moduleSelected == 'Decibel':
                self.currentPlaylist, self.PlaybackStatus  = decibelmodule.run(currentSettings._maxTandaLength)
            if currentSettings._moduleSelected == 'Swinsian':
                self.currentPlaylist, self.PlaybackStatus  = swinsianmodule.run(currentSettings._maxTandaLength)
            if currentSettings._moduleSelected == 'Spotify':
                self.currentPlaylist, self.PlaybackStatus  = spotifymodule.run(currentSettings._maxTandaLength)
            if currentSettings._moduleSelected == 'Vox':
                    self.currentPlaylist, self.PlaybackStatus  = voxmodule.run(currentSettings._maxTandaLength)
            if currentSettings._moduleSelected == 'Cog':
                    self.currentPlaylist, self.PlaybackStatus  = cogmodule.run(currentSettings._maxTandaLength)
            if currentSettings._moduleSelected == 'Embrace':
                    self.currentPlaylist, self.PlaybackStatus  = embracemodule.run(currentSettings._maxTandaLength, self.rawPlaylist)
            if currentSettings._moduleSelected == 'Mixxx':
                self.currentPlaylist, self.PlaybackStatus = mixxxmodule.run(currentSettings._maxTandaLength, self.rawPlaylist)

        if currentSettings._moduleSelected == 'Icecast':
            self.currentPlaylist, self.PlaybackStatus = icecastmodule.run(currentSettings._maxTandaLength, self.rawPlaylist)

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

        #
        # Save the reading
        #
        if (self.rawPlaylist == self.currentPlaylist) and (self.PreviousPlaybackStatus == self.PlaybackStatus):
            self.playlistChanged  = False
        else:
            self.rawPlaylist = deepcopy(self.currentPlaylist)
            self.playlistChanged  = True

        logging.info("Data extracted from " + currentSettings._moduleSelected  + ": " + self.StatusMessage)
        if self.PreviousPlaybackStatus == "":
            self.PreviousPlaybackStatus = self.PlaybackStatus

        return self

    ###############################################################
    #
    # APPLY RULES
    # Create display strings
    #
    ###############################################################
    def processData(self, currentSettings):
        for i in range(0, len(self.currentPlaylist)):
            self.currentPlaylist[i].applySongRules(currentSettings._rules)

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
        
        #Mood settings play status (Playing, Not Playing)
        if self.PlaybackStatus == 'Playing':
            MoodStatus = "Playing"
        else:
            MoodStatus = "Not Playing"
        
        applyMood = None
        for i in range(1, len(currentSettings._moods)):
            currentRule = currentSettings._moods[i]
            try:
                if currentRule['Type'] == 'Mood' and currentRule['Active'] == 'yes' and str(currentRule['PlayState']) == str(MoodStatus):
                    # Only apply Mood for current song
                    if currentRule['Field2'] == 'is':
                        if eval(str(currentRule['Field1']).replace("%"," currentSong.")).lower() == str(currentRule['Field3']).lower():
                            applyMood = i
                    if currentRule['Field2'] == 'is not':
                        if eval(str(currentRule['Field1']).replace("%"," currentSong.")).lower() not in str("["+currentRule['Field3'].lower()+"]"):
                            applyMood = i
                    if currentRule['Field2'] == 'contains':
                        if str(currentRule['Field3']).lower() in eval(str(currentRule['Field1']).replace("%"," currentSong.")).lower():
                            applyMood = i
            except Exception as e:
                logging.info(e, exc_info=True)

        #
        # Apply mood layout and background or default mood
        #
        if applyMood:
            currentRule = currentSettings._moods[applyMood]
            self.CurrentMood = currentRule['Name']
            self.DisplaySettings = currentRule['Display']
            appPath = getBeamHomePath()
            self.BackgroundPath = os.path.join(appPath, currentRule['Background'])
            self.RotateBackground = currentRule['RotateBackground']
            self.RotateTimer = currentRule['RotateTimer']
        else:
            defaultMood = currentSettings._moods[0]
            self.CurrentMood = defaultMood['Name']
            self.DisplaySettings = defaultMood['Display']
            appPath = getBeamHomePath()
            self.BackgroundPath = os.path.join(appPath, defaultMood['Background'])
            self.RotateBackground = defaultMood['RotateBackground']
            self.RotateTimer = defaultMood['RotateTimer']


        ###############################################################
        #
        # Create Display Strings
        #
        ###############################################################

        # The display lines
        for i in range(0, len(self.DisplaySettings)):
            self.DisplayRows.append('')
        
        #first, update the conversion dictionary
        self.updateConversionDisctionary()

        for j in range(0, len(self.DisplaySettings)):
            MyDisplay = self.DisplaySettings[j]
            displayValue = str(MyDisplay['Field'])
            # for key in self.convDict:
            # in reverse order to avoid issues with %AlbumArtist by %Artist
            for key in sorted(list(self.convDict.keys()), reverse=True):
                displayValue = displayValue.replace(str(key), str(self.convDict[key]))
            if MyDisplay['HideControl']  == "" and MyDisplay['Active'] == "yes":
                self.DisplayRows[j] = displayValue
            else:
                # Hides line if HideControl is empty if there is no next tanda
                hideControlEval = str(MyDisplay['HideControl'])
                # for key in self.convDict:
                # in reverse order to avoid issues with %AlbumArtist by %Artist
                for key in sorted(list(self.convDict.keys()), reverse=True):
                    hideControlEval = hideControlEval.replace(str(key), str(self.convDict[key]))
                if  not hideControlEval == ""  and MyDisplay['Active'] == "yes":
                    self.DisplayRows[j] = displayValue
                else:
                    self.DisplayRows[j] = ""

        for j in range(0, len(self.DisplaySettings)):
            MyDisplay = self.DisplaySettings[j]
            displayValue = str(MyDisplay['Field'])
            if str(displayValue).strip() == "%CoverArt":
                filePath = currentSong.FilePath
                if filePath != self.currentCoverArtPath:
                    self.currentCoverArtPath = filePath
                    # Stored anyhow
                    if filePath == "":
                        self.currentCoverArtImage = None
                    else:
                        self.currentCoverArtImage = readCoverArtImage(filePath)
                    # None if none found
                    break

        logging.info("...data got filtered: ")
    

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
        
        #Track number in a tanda
        self.convDict['%SongsSinceLastCortina'] = self.SinceLastCortinaCount
        self.convDict['%CurrentTandaSongsRemaining'] = self.TillNextCortinaCount - 1
            #current tanda count
        self.convDict['%CurrentTandaLength'] = self.SinceLastCortinaCount + self.TillNextCortinaCount - 1 

        



