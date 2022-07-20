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

import wx.lib.delayedresult

from bin.beamsettings import *
from bin.beamutils import getBeamHomePath
from bin.nowplayingdata import *
from random import randint

from bin.dialogs.preferencespanels.basicsettingspanel import BasicSettingsPanel
from bin.dialogs.preferencespanels.defaultlayoutpanel import DefaultLayoutPanel
from bin.dialogs.preferencespanels.moodspanel import MoodsPanel
from bin.dialogs.preferencespanels.rulespanel import RulesPanel
from bin.dialogs.preferencespanels.tagspreviewpanel import TagsPreviewPanel

from bin.dialogs.helpdialog import HelpDialog
from bin.dialogs import aboutdialog
# from bin.dialogs.displayframe import DisplayPanel


###################################################################
#                Build main preferences Window                    #
###################################################################

class DisplayData():

    def __init__(self, mainFrame):

        # !!! callback to be removed
        self.mainFrame = mainFrame

        # Data from player
        self.nowPlayingData = NowPlayingData()

        # initially no worker started to get update finished in extract data thread
        self.currentlyUpdating = False

        self.alpha = float(1.0)
        self.red = float(1.0)
        self.blue = float(1.0)
        self.green = float(1.0)

        self.currentDisplayRows = []
        self.currentDisplaySettings = []
        self.currentPlaybackStatus = ""
        self.previousMoodName = ""
        self.currentMoodName = ""

        # self.backgroundImage = wx.EmptyBitmap(800,600)
        self.backgroundImage = wx.Bitmap(800,600)
        # self.SetBackgroundColour(wx.BLACK)
        # self._currentBackgroundPath = []
        self._currentBackgroundPath = None
        self.BackgroundImageWidth, self.BackgroundImageHeight = self.backgroundImage.GetSize()
        # "no", "linear", "random"
        # ??? wird wo gesetzt und gespeichert
        self.RotateBackground = 'no'

        # trigger
        self.triggerResizeBackground = True
        self.textsAreVisible = False
        self.FadeDirection = 'In'
        self.RotateBackgroundTrigger = False

        ########################## END OF INITIALIZATION #########################



    ########################################################
    # Update data - Executed from mainFrame to bottom with exception if preferences changed
    ########################################################

    # Copy display data from nowplayingdata
    # gets continously called by a timer in MainFrame.__init__()
    def updateData(self, event=wx.EVT_TIMER):
        try:
            # copy playing data to current
            # ??? and below again
            self.currentDisplayRows = self.nowPlayingData.DisplayRows
            self.currentCoverArtImage = self.nowPlayingData.currentCoverArtImage
            self.currentPlaybackStatus = self.nowPlayingData.StatusMessage
            self.previousPlaybackStatus = self.nowPlayingData.PreviousPlaybackStatus

            if not self.currentlyUpdating:
                self.currentlyUpdating = True
                # asynchronous transmission of data from a worker thread to the main thread
                # calls readDataThread() in separate thread and then getDataFinished()
                wx.lib.delayedresult.startWorker(self.getDataFinished, self.readDataThread)
            # ??? Why resets updateDate it's own timer
            # It will create a new one, indeed
            # self.updateDataTimer()  # Reset the timer
        except Exception as e:
            logging.error(e, exc_info=True)


    #
    # Read song info from the modules
    # in a thread by updateData()
    #
    def readDataThread(self):
        try:
            self.nowPlayingData.readData(beamSettings)
            # sets playlistChanged
        except Exception as e:
            logging.error(e, exc_info=True)

    #
    # Check if the playlist got changed
    # and in case process that
    # in the MainThread
    #
    def getDataFinished(self, result):
        try:
            self.currentlyUpdating = False
            # playlistChabnged set by NowPlayingData.readData()
            if self.nowPlayingData.playlistChanged:
                # Only update if playlist has changed
                self.processData()

            if (self.nowPlayingData.playlistchangetime > 0) and self.nowPlayingData.isDisplayTimeExpired():
                # erase
                self.mainFrame.refreshDisplay()
                # refresh only once, keeps expired if 0
                self.nowPlayingData.playlistchangetime = 0

        except Exception as e:
            logging.error(e, exc_info=True)

    #
    # called in MainTread
    # starts Thread for processDataThread()
    # and then calls __updateMood()
    #
    def processData(self):
        try:
            wx.lib.delayedresult.startWorker(self.__updateMood, self.processDataThread)
        except Exception as e:
            logging.error(e, exc_info=True)
            pass

    # Process data in own thread
    def processDataThread(self):
        try:
            self.nowPlayingData.processData(beamSettings)
        except Exception as e:
            logging.error(e, exc_info=True)
            pass

    # Running in MainThread
    # After processing data
    # update the mood
    # and refresh the display
    def __updateMood(self, result):
        try:
            # ??? done above yet
            self.currentDisplayRows = self.nowPlayingData.DisplayRows
            self.currentCoverArtImage = self.nowPlayingData.currentCoverArtImage
            self.currentPlaybackStatus = self.nowPlayingData.StatusMessage

            self.previousMoodName = deepcopy(self.currentMoodName)
            self.currentMoodName = self.nowPlayingData.CurrentMoodName
            self.currentDisplaySettings = self.nowPlayingData.DisplaySettings
            # can be "no", "linear", "random"
            ## set in __updateMood()
            self.RotateBackground = self.nowPlayingData.RotateBackground
            # in seconds
            self.rotatebackgroundseconds = self.nowPlayingData.rotatebackgroundseconds

            self.mainFrame.SetStatusText(beamSettings.getSelectedModuleName() + ": " + self.currentPlaybackStatus + " - Mood: " + self.currentMoodName)

            # BackgroundPath can get changed by EditMoodDialog
            self._currentBackgroundPath = self.nowPlayingData.BackgroundPath
            if (self.previousMoodName != self.currentMoodName):
                # self._currentBackgroundPath = self.nowPlayingData.BackgroundPath
                self.startTransition('MoodChange')
            else:
                self.startTransition('SongChange')

            self.mainFrame.refreshDisplay()
        except Exception as e:
            logging.error(e, exc_info=True)
            pass



    ########################################################
    #                                                      #
    #                                                      #
    #                  TRANSITIONS                         #
    #                                                      #
    #                                                      #
    ########################################################
    #
    # TransitionType:
    #    MoodChange -> Change the mood and song (mood transition type)
    #    SongChange -> change text (direct fade or no transition
    def startTransition(self, TransitionType):

        if TransitionType == 'MoodChange':
            # LOAD NEW SETTINGS FOR NEW MOOD
            # Stop RotateBackground timer if it is running
            self.mainFrame.RotateBackgroundTimer.Stop()
            # Select Mood transition and start changing
            if beamSettings.getMoodTransition() == 'Fade directly':
                self.currentTransition = 'FadeDirect'
                self.initiateTransition()
            elif beamSettings.getMoodTransition() == 'Fade to black':
                self.currentTransition = 'FadeToBlack'
                self.initiateTransition()
            else:
                self.currentTransition = ''
                self.initiateTransition()

            if not self.RotateBackground == 'no':
                self.mainFrame.RotateBackgroundTimer.Start(int(self.rotatebackgroundseconds) * 1000)

            return

        if TransitionType == 'SongChange':
            if beamSettings.getMoodTransition() == 'No transition':
                self.currentTransition = ''
                self.initiateTransition()
            else:
                self.currentTransition = 'FadeDirect'
                self.initiateTransition()

            return

    ########################################################
    # INITIATE TRANSITION
    ########################################################
    def initiateTransition(self):

        self.transitionSpeed = int(int(beamSettings.getMoodTransitionSpeed()) / 100)
        self.delta = float(1 / float(self.transitionSpeed))

        # FADE DIRECTLY
        if self.currentTransition == 'FadeDirect':

            self.alpha = float(0.0)
            # Load the background image
            if self._currentBackgroundPath is not None:
                appPath = getBeamHomePath()
                self.backgroundImage = wx.Bitmap(os.path.join(appPath, self._currentBackgroundPath))
                self.modifiedBitmap = self._currentBackgroundPath
                self.BackgroundImageWidth, self.BackgroundImageHeight = self.backgroundImage.GetSize()

            # Set triggers
            self.triggerResizeBackground = True
            self.textsAreVisible = True

            # start the timer for the transition
            self.mainFrame.TransitionTimer.Start(self.transitionSpeed)
            return

        # FADE TO BLACK
        if self.currentTransition == 'FadeToBlack':
            if self.FadeDirection == 'Out':
                self.textsAreVisible = False
                self.red = float(1.0)
                self.green = float(1.0)
                self.blue = float(1.0)
                self.alpha = float(1.0)
                # Fade out
                self.mainFrame.TransitionTimer.Start(self.transitionSpeed)

            else:
                # Load the new background image
                appPath = getBeamHomePath()
                self.backgroundImage = wx.Bitmap(os.path.join(appPath, self._currentBackgroundPath))
                self.modifiedBitmap = self._currentBackgroundPath
                self.BackgroundImageWidth, self.BackgroundImageHeight = self.backgroundImage.GetSize()
                # Set triggers
                self.triggerResizeBackground = True
                self.textsAreVisible = True

                self.red = float(0.0)
                self.green = float(0.0)
                self.blue = float(0.0)
                self.alpha = float(1.0)

                self.mainFrame.TransitionTimer.Start(self.transitionSpeed)
                return

        else:
            self.currentTransition = ''
            self.switchBackground()

    ########################################################
    # No transition
    ########################################################
    def switchBackground(self):

        self.triggerResizeBackground = True
        appPath = getBeamHomePath()
        self.backgroundImage = wx.Bitmap(os.path.join(appPath, self._currentBackgroundPath))
        self.modifiedBitmap = self._currentBackgroundPath
        self.BackgroundImageWidth, self.BackgroundImageHeight = self.backgroundImage.GetSize()
        self.textsAreVisible = True
        self.mainFrame.refreshDisplay()

    ########################################################
    # TIMER - USED for Fade directly and Fade to black
    ########################################################
    def transition(self, event):
        if self.currentTransition == 'FadeDirect':
            self.FadeImage()
            return
        if self.currentTransition == 'FadeToBlack' and self.FadeDirection == 'Out':
            self.FadeToBlackImage()
            return
        if self.currentTransition == 'FadeToBlack' and self.FadeDirection == 'In':
            self.FadeBackImage()
            return

    ########################################################
    # Fade directly
    ########################################################
    def FadeImage(self):
        self.alpha += self.delta
        if self.alpha >= 1:
            self.alpha = 1.0
            self.mainFrame.TransitionTimer.Stop()
            self.RotateBackgroundTrigger = False
        self.mainFrame.refreshDisplay()

    ########################################################
    # Fade To black - 2 functions (IN and OUT)
    ########################################################
    def FadeToBlackImage(self):

        self.red -= 2 * self.delta
        self.green -= 2 * self.delta
        self.blue -= 2 * self.delta

        if self.red >= 0 and self.red <= 1:
            self.triggerResizeBackground = True
            self.textsAreVisible = False
            self.mainFrame.refreshDisplay()
        else:
            self.red = float(0.0)
            self.green = float(0.0)
            self.blue = float(0.0)
            self.direction = 'in'  # Change fading direction
            self.mainFrame.TransitionTimer.Stop()
            self.mainFrame.refreshDisplay()

            self.FadeDirection = 'In'
            self.currentTransition = 'FadeToBlack'
            self.initiateTransition()

    def FadeBackImage(self):
        self.red += self.delta
        self.green += self.delta
        self.blue += self.delta

        if self.red >= 0 and self.red <= 1:
            self.triggerResizeBackground = True
            self.mainFrame.refreshDisplay()
        else:
            self.red = float(1.0)
            self.green = float(1.0)
            self.blue = float(1.0)
            self.FadeDirection = 'Out'
            self.mainFrame.TransitionTimer.Stop()
            self.mainFrame.refreshDisplay()

    #
    # Gets triggered by a timer event in MainFrame
    def rotateBackground(self, event=wx.EVT_TIMER):
        # Starts, stops and executes the rotate-background function.

        if self.RotateBackground == 'linear' or self.RotateBackground == 'random':
            (path, file) = os.path.split(self._currentBackgroundPath)
            backgrounds_tmp = os.listdir(path)
            backgrounds = [s for s in backgrounds_tmp if ".jpg" in s or ".png" in s or ".jpg" in s]
            try:
                position = backgrounds.index(file)
            except:
                position = 0
            # Linear in the folder
            if self.RotateBackground == 'linear':
                try:
                    self._currentBackgroundPath = os.path.join(path, backgrounds[position + 1])
                except:
                    self._currentBackgroundPath = os.path.join(path, backgrounds[0])
            # Random
            else:
                newposition = randint(0, len(backgrounds))
                if newposition == position:
                    try:
                        self._currentBackgroundPath = os.path.join(path, backgrounds[position + 1])
                    except:
                        self._currentBackgroundPath = os.path.join(path, backgrounds[0])
                else:
                    try:
                        self._currentBackgroundPath = os.path.join(path, backgrounds[newposition])
                    except:
                        self._currentBackgroundPath = os.path.join(path, backgrounds[0])
        # Stop the rotation
        if self.RotateBackground == 'no':
            self._currentBackgroundPath = self.nowPlayingData.BackgroundPath
            try:
                self.mainFrame.RotateBackgroundTimer.Stop()
                return
            except:
                pass

        # Start the transition
        if beamSettings.getMoodTransition() == 'No transition':
            self.currentTransition = ''
            self.initiateTransition()
        else:
            self.currentTransition = 'FadeDirect'
            self.initiateTransition()



