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

import wx, platform, os, sys
import time
import datetime

from bin.songclass import SongObject
from copy import deepcopy

###############################################################
#
# LOAD MEDIA PLAYER MODULES
#
###############################################################

if platform.system() == 'Linux':
    from Modules.Lin import audaciousModule, rhythmboxModule, clementineModule, bansheeModule, spotifyLinuxModule
if platform.system() == 'Windows':
    from Modules.Win import itunesWindowsModule, winampWindowsModule, mediamonkeyModule, jrmcWindowsModule, spotifyWindowsModule, foobar2kWindowsModule
if platform.system() == 'Darwin':
    from Modules.Mac import itunesMacModule, decibelModule, spotifyMacModule, voxModule, cogModule

###############################################################
#
# INIT
#
###############################################################

class NowPlayingDataModel:

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
        self.BackgroundImage = ""
        self.DisplayRow = []
        self.DisplaySettings = {}

        self.convDict = dict()
        
    def ExtractPlaylistInfo(self, currentSettings):
        print "Start updating data... ", time.strftime("%H:%M:%S")
        self.PreviousPlaybackStatus = self.PlaybackStatus
        
        # Save previous state
        try:
            LastRead = deepcopy(self.currentPlaylist)
        except:
            LastRead = SongObject()


###############################################################
#
# Extract data using the player module
#
###############################################################
        # WINDOWS
        if platform.system() == 'Windows':
            if currentSettings._moduleSelected == 'iTunes':
                self.currentPlaylist, self.PlaybackStatus = itunesWindowsModule.run(currentSettings._maxTandaLength)
            if currentSettings._moduleSelected == 'MediaMonkey':
                self.currentPlaylist, self.PlaybackStatus = mediamonkeyModule.run(currentSettings._maxTandaLength, self.rawPlaylist)
            if currentSettings._moduleSelected == 'JRiver Media Center':
                self.currentPlaylist, self.PlaybackStatus = jrmcWindowsModule.run(currentSettings._maxTandaLength)
            if currentSettings._moduleSelected == 'Spotify':
                self.currentPlaylist, self.PlaybackStatus =spotifyWindowsModule.run(currentSettings._maxTandaLength)
            if currentSettings._moduleSelected == 'Foobar2000':
                self.currentPlaylist, self.PlaybackStatus =foobar2kWindowsModule.run(currentSettings._maxTandaLength)
            try: #required due to loaded modules
                if currentSettings._moduleSelected == 'Winamp':
                    self.currentPlaylist, self.PlaybackStatus = winampWindowsModule.run(currentSettings._maxTandaLength)
            except:
                pass

        # LINUX
        if platform.system() == 'Linux':
            if currentSettings._moduleSelected == 'Audacious':
                self.currentPlaylist, self.PlaybackStatus = audaciousModule.run(currentSettings._maxTandaLength)
            if currentSettings._moduleSelected == 'Rhythmbox':
                self.currentPlaylist, self.PlaybackStatus = rhythmboxModule.run(currentSettings._maxTandaLength)
            if currentSettings._moduleSelected == 'Clementine':
                self.currentPlaylist, self.PlaybackStatus = clementineModule.run(currentSettings._maxTandaLength)
            if currentSettings._moduleSelected == 'Banshee':
                self.currentPlaylist, self.PlaybackStatus = bansheeModule.run(currentSettings._maxTandaLength)
            if currentSettings._moduleSelected == 'Spotify':
                self.currentPlaylist, self.PlaybackStatus = spotifyLinuxModule.run(currentSettings._maxTandaLength)

        # Mac OS X
        if platform.system() == 'Darwin':
            if currentSettings._moduleSelected == 'iTunes':
                self.currentPlaylist, self.PlaybackStatus  = itunesMacModule.run(currentSettings._maxTandaLength, self.rawPlaylist)
            if currentSettings._moduleSelected == 'Decibel':
                self.currentPlaylist, self.PlaybackStatus  = decibelModule.run(currentSettings._maxTandaLength)
            if currentSettings._moduleSelected == 'Spotify':
                self.currentPlaylist, self.PlaybackStatus  = spotifyMacModule.run(currentSettings._maxTandaLength)
            if currentSettings._moduleSelected == 'Vox':
                    self.currentPlaylist, self.PlaybackStatus  = voxModule.run(currentSettings._maxTandaLength)
            if currentSettings._moduleSelected == 'Cog':
                    self.currentPlaylist, self.PlaybackStatus  = cogModule.run(currentSettings._maxTandaLength)

        #
        # Set status message
        #
        try:
            if not self.currentPlaylist[0].ModuleMessage == "":
                self.StatusMessage = self.PlaybackStatus+", "+self.currentPlaylist[0].ModuleMessage
            else:
                self.StatusMessage = self.PlaybackStatus
        except:
            self.StatusMessage = self.PlaybackStatus
        
        #
        # Save the reading
        #
        if (self.rawPlaylist != self.currentPlaylist):
            self.rawPlaylist = deepcopy(self.currentPlaylist)
            self.playlistChanged  = True
        else:
            self.playlistChanged  = False
            

        print "Data Extracted... ", time.strftime("%H:%M:%S")
        if self.PreviousPlaybackStatus == "":
            self.PreviousPlaybackStatus = self.PlaybackStatus
        #
        # Apply default layout and background, then change it if mood is applied
        #
        self.CurrentMood = 'Default'
        self.DisplaySettings = currentSettings._DefaultDisplaySettings
        self.BackgroundImage = currentSettings._DefaultBackground

        #
        # Apply rules, for every song in list.
        # Rules can change without changing song so run this every time!
        #
        for i in range(0, len(self.currentPlaylist)):
            self.currentPlaylist[i].applySongRules(currentSettings._rules)


#
# Previous song analysis
#
        try:
            if LastRead[0] == self.currentPlaylist[0]:
                #print "Same song, do nothing"
                pass 
            else:
                #
                # Calculate the number of songs that were payed since last cortina
                #
                if self.currentPlaylist[0].IsCortina == "yes":                   
                    self.SinceLastCortinaCount = 0
                else:
                    self.SinceLastCortinaCount = self.SinceLastCortinaCount + 1

                self.prevPlayedSong = LastRead[0]
                #print "Different song, copy"
        except:
            #print "Empty"
            pass
#
# MOOD RULES - apply only to current song
#
        try:
            currentSong = self.currentPlaylist[0]
        except:
            currentSong = SongObject()
        
        #Mood settings play status (Playing, Not Playing
        if self.PlaybackStatus == 'Playing':
            MoodStatus = "Playing"
        else:
            MoodStatus = "Not Playing"
        
        for i in range(0, len(currentSettings._moods)):
            currentRule = currentSettings._moods[i]
            if currentRule[u'Type'] == 'Mood' and currentRule[u'Active'] == 'yes' and str(currentRule[u'PlayState']) == str(MoodStatus):
                # Only apply Mood for current song
                if currentRule[u'Field2'] == 'is':
                    if eval(str(currentRule[u'Field1']).replace("%"," currentSong.")).lower() == str(currentRule[u'Field3']).lower():
                        self.CurrentMood = currentRule[u'Name']
                        self.DisplaySettings = currentRule[u'Display']
                        self.BackgroundImage = currentRule[u'Background']
                if currentRule[u'Field2'] == 'is not':
                    if eval(str(currentRule[u'Field1']).replace("%"," currentSong.")).lower() not in str("["+currentRule[u'Field3'].lower()+"]"):
                        self.CurrentMood = currentRule[u'Name']
                        self.DisplaySettings = currentRule[u'Display']
                        self.BackgroundImage = currentRule[u'Background']                              
                if currentRule[u'Field2'] == 'contains':
                    if str(currentRule[u'Field3']).lower() in eval(str(currentRule[u'Field1']).replace("%"," currentSong.")).lower():
                        self.CurrentMood = currentRule[u'Name']
                        self.DisplaySettings = currentRule[u'Display']
                        self.BackgroundImage = currentRule[u'Background']

#
# Create NextTanda
#
        self.nextTandaSong = None
        self.TillNextCortinaCount = 0
        
        for i in range(0, len(self.currentPlaylist)-1):
            # Check if song is cortina
            if self.currentPlaylist[i].IsCortina == "yes" and not self.currentPlaylist[i+1].IsCortina == "yes":
                self.nextTandaSong = deepcopy(self.currentPlaylist[i+1])
                break
            else:
                self.TillNextCortinaCount = self.TillNextCortinaCount + 1
#
# Create Display Strings
#

        # The display lines
        for i in range(0, len(self.DisplaySettings)): self.DisplayRow.append('')
        
        #first, update the conversion dictionary
        self.updateConversionDisctionary()
        
        for j in range(0, len(self.DisplaySettings)):
            MyDisplay = self.DisplaySettings[j]
            try:
                displayValue = str(MyDisplay['Field'])
            except:
                displayValue = unicode(MyDisplay['Field'])
            for key in self.convDict:
                try:
                    displayValue = displayValue.replace(str(key), str(self.convDict[key]))
                except:
                    try:
                        displayValue = displayValue.replace(key.decode('utf-8'), self.convDict[key].decode('utf-8'))
                    except:
                        displayValue = displayValue.replace(key.decode('latin-1'), self.convDict[key].decode('latin-1'))              
            if MyDisplay['HideControl']  == "" and MyDisplay['Active'] == "yes":
                self.DisplayRow[j] = displayValue
            else:
                # Hides line if HideControl is empty if there is no next tanda
                hideControlEval = str(MyDisplay['HideControl'])
                for key in self.convDict:
                    hideControlEval = hideControlEval.replace(str(key), str(self.convDict[key]))
                        
                if  not hideControlEval == ""  and MyDisplay['Active'] == "yes":
                    self.DisplayRow[j] = displayValue
                else:
                    self.DisplayRow[j] = ""
        print "...data filtered: ", time.strftime("%H:%M:%S")
        return
            
###############################################################
#
# Conversion dictionary
#
###############################################################

    def updateConversionDisctionary(self):
        self.convDict = dict()
        #CurrentSong
        try:
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
        except:
            self.convDict['%Artist']        = u""
            self.convDict['%Album']         = u""
            self.convDict['%Title']         = u""
            self.convDict['%Genre']         = u""
            self.convDict['%Comment']       = u""
            self.convDict['%Composer']      = u""
            self.convDict['%Year']          = u""
            self.convDict['%Singer']        = u""
            self.convDict['%AlbumArtist']   = u""
            self.convDict['%Performer']     = u""            
            self.convDict['%IsCortina']     = u""
            
        #PreviousSong
        try:
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
            
            
        except:
            self.convDict['%PreviousArtist']        = u""
            self.convDict['%PreviousAlbum']         = u""
            self.convDict['%PreviousTitle']         = u""
            self.convDict['%PreviousGenre']         = u""
            self.convDict['%PreviousComment']       = u""
            self.convDict['%PreviousComposer']      = u""
            self.convDict['%PreviousYear']          = u""
            self.convDict['%PreviousSinger']        = u""
            self.convDict['%PreviousAlbumArtist']   = u""
            self.convDict['%PreviousPerformer']     = u""
            self.convDict['%PreviousIsCortina']     = u""
            
        #NextSong
        try:
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
        except:
            self.convDict['%NextArtist']        = u""
            self.convDict['%NextAlbum']         = u""
            self.convDict['%NextTitle']         = u""
            self.convDict['%NextGenre']         = u""
            self.convDict['%NextComment']       = u""
            self.convDict['%NextComposer']      = u""
            self.convDict['%NextYear']          = u""
            self.convDict['%NextSinger']        = u""
            self.convDict['%NextAlbumArtist']   = u""
            self.convDict['%NextPerformer']     = u""
            self.convDict['%NextIsCortina']     = u""
        
        #NextTanda
        try:
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
        except:
            self.convDict['%NextTandaArtist']        = u""
            self.convDict['%NextTandaAlbum']         = u""
            self.convDict['%NextTandaTitle']         = u""
            self.convDict['%NextTandaGenre']         = u""
            self.convDict['%NextTandaComment']       = u""
            self.convDict['%NextTandaComposer']      = u""
            self.convDict['%NextTandaYear']          = u""
            self.convDict['%NextTandaSinger']        = u""
            self.convDict['%NextTandaAlbumArtist']   = u""
            self.convDict['%NextTandaPerformer']     = u""
            self.convDict['%NextTandaIsCortina']     = u""        

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

        



