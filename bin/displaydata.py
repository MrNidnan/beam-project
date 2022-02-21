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
from bin.beamutils import getApplicationPath
from bin.nowplayingdata import *

from bin.dialogs.preferencespanels.basicsettings import BasicSettings
from bin.dialogs.preferencespanels.defaultlayout import DefaultLayout
from bin.dialogs.preferencespanels.moods import Moods
from bin.dialogs.preferencespanels.rules import Rules
from bin.dialogs.preferencespanels.tagspreview import TagsPreview

from bin.dialogs.helpdialog import HelpDialog
from bin.dialogs import aboutdialog
# from bin.dialogs.displayframe import DisplayFrame


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
        self.previousMood = ""
        self.currentMood = ""

        # self.backgroundImage = wx.EmptyBitmap(800,600)
        self.backgroundImage = wx.Bitmap(800,600)
        # self.SetBackgroundColour(wx.BLACK)
        # self._currentBackgroundPath = []
        self._currentBackgroundPath = None
        self.BackgroundImageWidth, self.BackgroundImageHeight = self.backgroundImage.GetSize()

        # trigger
        self.triggerResizeBackground = True
        self.textsAreVisible = False
        self.FadeDirection = 'In'
        self.RotateBackgroundTrigger = False

        ########################## END OF INITIALIZATION #########################



    ########################################################
    # Update data - Executed from mainFrame to bottom with exception if preferences changed
    ########################################################

    # Copy display data from nowplayingdatamodel
    # gets continously called by a timer in main loop
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
                # call extractDataThread() and then getDataFinished()
                wx.lib.delayedresult.startWorker(self.getDataFinished, self.readDataThread)
            # ??? Why resets updateDate it's own timer
            # It will create a new one, indeed
            # self.updateDataTimer()  # Reset the timer
        except Exception as e:
            logging.error(e, exc_info=True)
            pass


    # Thread by startWorker()
    def readDataThread(self):
        try:
            self.nowPlayingData.readData(beamSettings)
        except Exception as e:
            logging.error(e, exc_info=True)


    # New data read into nowPlayingData
    def getDataFinished(self, result):
        try:
            self.currentlyUpdating = False
            if self.nowPlayingData.playlistChanged:
                # Only update if playlist has changed
                self.processData()
        except Exception as e:
            logging.error(e, exc_info=True)

    # Read data from media player
    # in an own thread
    # runtime so long?
    def processData(self):
        try:
            wx.lib.delayedresult.startWorker(self.updateMood, self.processDataThread)
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

    # After processing data
    # update the mood in main loop
    # and refresh the display
    def updateMood(self, result):
        try:
            # ??? done above yet
            self.currentDisplayRows = self.nowPlayingData.DisplayRows
            self.currentCoverArtImage = self.nowPlayingData.currentCoverArtImage
            self.currentPlaybackStatus = self.nowPlayingData.StatusMessage

            self.previousMood = deepcopy(self.currentMood)
            self.currentMood = self.nowPlayingData.CurrentMood
            self.currentDisplaySettings = self.nowPlayingData.DisplaySettings
            self.RotateBackground = self.nowPlayingData.RotateBackground
            self.RotateTimer = self.nowPlayingData.RotateTimer

            self.mainFrame.SetStatusText("Player: " + self.currentPlaybackStatus + " - Mood: " + self.currentMood)

            if (self.previousMood != self.currentMood):
                self._currentBackgroundPath = self.nowPlayingData.BackgroundPath
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
            try:
                self.mainFrame.RotateBackgroundTimer.Stop()
            except:
                pass

            # !!! move to mainFrame
            # If there is a RotateBackground timer to be set. Initialize it.
            if not self.RotateBackground == 'no':
                try:
                    self.mainFrame.RotateBackgroundTimer = wx.Timer(self)
                    self.mainFrame.Bind(wx.EVT_TIMER, self.rotateBackground, self.mainFrame.RotateBackgroundTimer)
                    self.mainFrame.RotateBackgroundTimer.Start(int(self.RotateTimer) * 1000)
                except:
                    self.mainFrame.RotateBackgroundTimer.Stop()
                    self.mainFrame.RotateBackgroundTimer.Start(self.RotateTimer)
                    # Select Mood transition and start changing

            if beamSettings._moodTransition == 'Fade directly':
                self.currentTransition = 'FadeDirect'
                self.initiateTransition()
            elif beamSettings._moodTransition == 'Fade to black':
                self.currentTransition = 'FadeToBlack'
                self.initiateTransition()
            else:
                self.currentTransition = ''
                self.initiateTransition()

            return

        if TransitionType == 'SongChange':
            if beamSettings._moodTransition == 'No transition':
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

        self.transitionSpeed = int(int(beamSettings._moodTransitionSpeed) / 100)
        self.delta = float(1 / float(self.transitionSpeed))

        # FADE DIRECTLY
        if self.currentTransition == 'FadeDirect':

            self.alpha = float(0.0)
            # Load the background image
            if self._currentBackgroundPath is not None:
                appPath = getApplicationPath()
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
                appPath = getApplicationPath()
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
        appPath = getApplicationPath()
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

    ########################################################
    # Rotate Background
    ########################################################
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
        if beamSettings._moodTransition == 'No transition':
            self.currentTransition = ''
            self.initiateTransition()
        else:
            self.currentTransition = 'FadeDirect'
            self.initiateTransition()



