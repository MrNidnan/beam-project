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
from bin.nowplayingdatamodel import *

from bin.dialogs.preferencespanels.basicsettings import BasicSettings
from bin.dialogs.preferencespanels.defaultlayout import DefaultLayout
from bin.dialogs.preferencespanels.moods import Moods
from bin.dialogs.preferencespanels.rules import Rules
from bin.dialogs.preferencespanels.tagspreview import TagsPreview

from bin.dialogs.helpdialog import HelpDialog
from bin.dialogs import aboutdialog
from bin.dialogs.displayframe import DisplayFrame


###################################################################
#                Build main preferences Window                    #
###################################################################

class MainFrame(wx.Frame):
    # def __init__(self, parent, BeamSettings, nowPlayingDataModel):
    def __init__(self, settings=None):
        # Size and position of this main window
        # beamsettings loaded in Beam.py
        wx.Frame.__init__(self, None, title=beamSettings.mainFrameTitle + " V" + beamSettings.beamVersion, pos=(150,150), size=(800,600))
        # Necessary? Flicker?
        self.SetDoubleBuffered(True)

        self.displayFrame = None

        # Start the timer for updateData()
        # ??? redundant see call to updateData() below
        self.DataTimer()

        # Initialize DataObject - the model -
        self.nowPlayingDataModel = NowPlayingDataModel()

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

        # first update from player
        self.currentlyUpdating = False
        self.updateData()

        # Set Icon
        appPath = getApplicationPath()
        iconFilename = os.path.join(appPath,'resources','icons','icon_square','icon_square_256px.png')
        self.favicon = wx.Icon(iconFilename, wx.BITMAP_TYPE_ANY, 256, 256)
        self.SetIcon(self.favicon)

        # faders
        self.TransitionTimer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.transition, self.TransitionTimer)
        self.RotateBackgroundTimer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.rotateBackground, self.RotateBackgroundTimer)

        # Statusbar
        self.statusbar = self.CreateStatusBar(style=0)
        self.SetStatusText('Initializing...')

        # Setting up the menu.
        self.filemenu    = wx.Menu()
        self.menuExit    = self.filemenu.Append(wx.ID_EXIT,"E&xit"," Terminate the program")

        self.Aboutmenu   = wx.Menu()
        # self.menuPreferences = self.filemenu.Append(wx.ID_ANY, "&Preferences\tCtrl-+"," Configuration tool")
        # self.menuFullScreen  = self.filemenu.Append(wx.ID_ANY, "&Fullscreen\tF11", "Set fullscreen")
        self.menuAbout   = self.Aboutmenu.Append(wx.ID_ABOUT, "&About"," Information about this program")
        self.menuHelp    = self.Aboutmenu.Append(wx.ID_ANY, "&Help"," Getting started")

        # Creating the menubar.
        self.menuBar = wx.MenuBar()
        self.menuBar.Append(self.filemenu,"&File")    # Adding the "file menu" to the MenuBar
        self.menuBar.Append(self.Aboutmenu,"&About")  # Adding the "About menu" to the MenuBar
        self.SetMenuBar(self.menuBar)  # Adding the MenuBar to the Frame content.

        # Events.
        # self.Bind(wx.EVT_MENU, self.OnPreferences, self.menuPreferences)
        self.Bind(wx.EVT_MENU, self.onClose, self.menuExit)
        self.Bind(wx.EVT_MENU, self.onAbout, self.menuAbout)
        self.Bind(wx.EVT_MENU, self.onHelp, self.menuHelp)
        # self.Bind(wx.EVT_MENU, self.fullScreen, self.menuFullScreen)
        self.Bind(wx.EVT_CLOSE, self.onClose)
        self.Bind(wx.EVT_LEFT_DCLICK, self.fullScreen)

        # Background
        self.Bind(wx.EVT_SIZE, self.onSize)
        self.Bind(wx.EVT_PAINT, self.onPaint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.onEraseBackground)


        ####################
        # PANEL AND SIZERS #
        ####################
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox = wx.BoxSizer(wx.HORIZONTAL) # For buttons

        #################
        # LISTBOOK MENU #
        #################
        menu = ListBookMenu(panel, beamSettings, self.nowPlayingDataModel)
        
        ###########
        # BUTTONS #
        ###########
        self.button_apply = wx.Button(panel, label="Apply")
        self.button_apply.Bind(wx.EVT_BUTTON, self.onApply)
        hbox.Add(self.button_apply,flag= wx.LEFT | wx.TOP, border=10)

        self.button_display = wx.Button(panel, label="Display")
        self.button_display.Bind(wx.EVT_BUTTON, self.onDisplay)
        hbox.Add(self.button_display, flag= wx.ALL, border=10)

        ###########
        # ARRANGE #
        ###########
        vbox.Add(menu, 1,wx.ALL | wx.EXPAND, 5)
        vbox.Add(hbox, flag=wx.ALIGN_RIGHT)

        ###########
        # DISPLAY #
        ###########
        panel.SetSizer(vbox)
        self.Layout()
        self.Show()
        self.showStatusBar()


        ########################## END FRAME INITIALIZATION #########################



    #
    # Show 'Close dialog
    #
    def onClose(self, event):
        try:
            # ??? parent pointer?
            self.Destroy()
        except Exception as e:
            logging.error(e, exc_info=True)

    #
    # Show 'About Dialog'
    #
    def onAbout(self, event):
        try:
            aboutdialog.ShowAboutDialog(self)
        except Exception as e:
            logging.error(e, exc_info=True)

    #
    # Show 'Help'
    #
    def onHelp(self, event):
        try:
            help_dialog = HelpDialog(self)
            help_dialog.Show()
        except Exception as e:
            logging.error(e, exc_info=True)

    def onApply(self, event):
        # Save settings
        beamSettings.SaveConfig(beamSettings.defaultConfigFileName)
        # Reload settings in main-window
        self.updateSettings()

    def onDisplay(self, event):
        try:
            if self.displayFrame:
                self.displayFrame.Destroy()
                self.displayFrame = None
            else:
                # if not yet existing
                self.displayFrame = DisplayFrame(self, beamSettings, self.nowPlayingDataModel)
                self.displayFrame.Show()
        except Exception as e:
            logging.error(e, exc_info=True)

    def onSize(self, size):
        pass

    def onEraseBackground(self, evt):
        pass

    def onPaint(self, event):
        pass

        # UPDATE INFO FROM PREFERENCES WINDOW
    def updateSettings(self):
        try:
            self.showStatusBar()
            self.processData()
            # Starts and stops rotation if it has changed.
            # To be done
            # if (self.RotateBackgroundTimer.IsRunning() and self.RotateBackground == 'no') or (not self.RotateBackgroundTimer.IsRunning() and not self.RotateBackground == 'no') or (not self.RotateBackgroundTimer.IsRunning() and self.RotateBackground == 'no'):
            #    self.rotateBackground()
        except Exception as e:
            logging.error(e, exc_info=True)
            pass

    #
    # FULLSCREEN
    #
    def fullScreen(self, event):
        try:
            # Needed for Mac
            if platform.system() == 'Darwin':
                self.showStatusBar()
            self.ShowFullScreen(not self.IsFullScreen())
        except Exception as e:
            logging.error(e, exc_info=True)

    #
    # Hide/show statusbar
    #
    def showStatusBar(self):
        try:
            self.triggerResizeBackground = True
            if beamSettings._showStatusbar == 'True':
                self.statusbar.Show()
            else:
                self.statusbar.Hide()
        except Exception as e:
            logging.error(e, exc_info=True)

        # PROCESS INFO FROM MEDIA PLAYER

    def processData(self):
        try:
            # not implemented yet
            nothing=False
            # wx.lib.delayedresult.startWorker(self.updateMood, self.processDataThread)
        except Exception as e:
            logging.error(e, exc_info=True)
            pass

    # not implemented yet
    # PROCESS DATA WORKER
    def processDataThread(self):
        try:
            self.nowPlayingDataModel.processInformation(beamSettings)
        except Exception as e:
            logging.error(e, exc_info=True)
            pass

    #
    # Data timer
    #
    def DataTimer(self):
    # If the configuration have a timer on how often to  the data
        try:
        # There is not timer, so create and start it
            self.timer = wx.Timer(self)
            self.Bind(wx.EVT_TIMER, self.updateData, self.timer)
            self.timer.Start(beamSettings._updateTimer)
        except:
        # There is already a timer restart with new update timing
            self.timer.Stop()
            self.timer.Start(beamSettings._updateTimer)


    ########################################################
    #                                                      #
    #                                                      #
    #                 DATA FUNCTIONS                       #
    #                                                      #
    #                                                      #
    ########################################################

    ########################################################
    # Update data - Executed from top to bottom with exception if preferences changed
    ########################################################

    # READ FROM MEDIA PLAYER
    def updateData(self, event=wx.EVT_TIMER):
        try:
            self.currentDisplayRows = self.nowPlayingDataModel.DisplayRows
            self.currentCoverArtImage = self.nowPlayingDataModel.currentCoverArtImage
            self.currentPlaybackStatus = self.nowPlayingDataModel.StatusMessage
            self.previousPlaybackStatus = self.nowPlayingDataModel.PreviousPlaybackStatus

            if not self.currentlyUpdating:
                self.currentlyUpdating = True
                # asynchronous transmission of data from a worker thread to the main thread
                wx.lib.delayedresult.startWorker(self.getDataFinished, self.extractDataThread)
            self.DataTimer()  # Reset the timer
        except Exception as e:
            logging.error(e, exc_info=True)
            pass

        # MEDIA READER WORKER

    def extractDataThread(self):
        try:
            self.nowPlayingDataModel.ExtractPlaylistInfo(beamSettings)
        except Exception as e:
            logging.error(e, exc_info=True)
            pass

        # INFO FROM MEDIA PLAYER RECIEVED

    def getDataFinished(self, result):
        try:
            self.currentlyUpdating = False
            if self.nowPlayingDataModel.playlistChanged:
                self.processData()  # Only update if playlist has changed
        except Exception as e:
            logging.error(e, exc_info=True)
            pass

        # PROCESS INFO FROM MEDIA PLAYER

    def processData(self):
        try:
            wx.lib.delayedresult.startWorker(self.updateMood, self.processDataThread)
        except Exception as e:
            logging.error(e, exc_info=True)
            pass

        # PROCESS DATA WORKER

    def processDataThread(self):
        try:
            self.nowPlayingDataModel.processInformation(beamSettings)
        except Exception as e:
            logging.error(e, exc_info=True)
            pass

        # AFTER PROCESSING DATA

    def updateMood(self, result):
        try:
            self.currentDisplayRows = self.nowPlayingDataModel.DisplayRows
            self.currentCoverArtImage = self.nowPlayingDataModel.currentCoverArtImage
            self.currentPlaybackStatus = self.nowPlayingDataModel.StatusMessage
            self.previousMood = deepcopy(self.currentMood)
            self.currentMood = self.nowPlayingDataModel.CurrentMood
            self.currentDisplaySettings = self.nowPlayingDataModel.DisplaySettings
            self.RotateBackground = self.nowPlayingDataModel.RotateBackground
            self.RotateTimer = self.nowPlayingDataModel.RotateTimer

            self.SetStatusText("Player: " + self.currentPlaybackStatus + " - Mood: " + self.currentMood)

            if (self.previousMood != self.currentMood):
                self._currentBackgroundPath = self.nowPlayingDataModel.BackgroundImage
                self.startTransition('MoodChange')
            else:
                self.startTransition('SongChange')

            self.refreshDisplay()
        except Exception as e:
            logging.error(e, exc_info=True)
            pass

        # UPDATE INFO FROM PREFERENCES WINDOW

    def updateSettings(self):
        try:
            self.showStatusBar()
            self.processData()
            # Starts and stops rotation if it has changed.
            # if (self.RotateBackgroundTimer.IsRunning() and self.RotateBackground == 'no') or (
            #         not self.RotateBackgroundTimer.IsRunning() and not self.RotateBackground == 'no') or (
            #         not self.RotateBackgroundTimer.IsRunning() and self.RotateBackground == 'no'):
            #     self.rotateBackground()
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
                self.RotateBackgroundTimer.Stop()
            except:
                pass

            # If there is a RotateBackground timer to be set. Initialize it.
            if not self.RotateBackground == 'no':
                try:
                    self.RotateBackgroundTimer = wx.Timer(self)
                    self.Bind(wx.EVT_TIMER, self.rotateBackground, self.RotateBackgroundTimer)
                    self.RotateBackgroundTimer.Start(int(self.RotateTimer) * 1000)
                except:
                    self.RotateBackgroundTimer.Stop()
                    self.RotateBackgroundTimer.Start(self.RotateTimer)
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
            self.TransitionTimer.Start(self.transitionSpeed)
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
                self.TransitionTimer.Start(self.transitionSpeed)

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

                self.TransitionTimer.Start(self.transitionSpeed)
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
        self.refreshDisplay()

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
            self.TransitionTimer.Stop()
            self.RotateBackgroundTrigger = False
        self.refreshDisplay()

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
            self.refreshDisplay()
        else:
            self.red = float(0.0)
            self.green = float(0.0)
            self.blue = float(0.0)
            self.direction = 'in'  # Change fading direction
            self.TransitionTimer.Stop()
            self.refreshDisplay()

            self.FadeDirection = 'In'
            self.currentTransition = 'FadeToBlack'
            self.initiateTransition()

    def FadeBackImage(self):
        self.red += self.delta
        self.green += self.delta
        self.blue += self.delta

        if self.red >= 0 and self.red <= 1:
            self.triggerResizeBackground = True
            self.refreshDisplay()
        else:
            self.red = float(1.0)
            self.green = float(1.0)
            self.blue = float(1.0)
            self.FadeDirection = 'Out'
            self.TransitionTimer.Stop()
            self.refreshDisplay()

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
            self._currentBackgroundPath = self.nowPlayingDataModel.BackgroundImage
            try:
                self.RotateBackgroundTimer.Stop()
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

    def refreshDisplay(self):
        try:
            if self.displayFrame:
                self.displayFrame.Refresh()
        except Exception as e:
            logging.error(e, exc_info=True)



###################################################################
#                The ListBookMenu                                 #
###################################################################

class ListBookMenu(wx.Listbook):
    def __init__(self, parent, beamSettings, nowPlayingDataModel):
        wx.Listbook.__init__(self, parent, wx.ID_ANY, style = wx.BK_DEFAULT)
        
        ##########
        # IMAGES #
        ##########
        imagelist = wx.ImageList(32,32)
        urllist = ["1-BasicSettings32.png", "2-DefaultDisplay32.png", "3-Moods32.png", "4-Rules32.png", "5-Tags32.png"]
        for urls in urllist:
            appPath = getApplicationPath()
            bmp = wx.Bitmap(os.path.join(appPath, 'resources', 'icons', 'preferences', urls), wx.BITMAP_TYPE_PNG)
            imagelist.Add(bmp)
        
        self.AssignImageList(imagelist)
        
        ###########
        # CONTENT #
        ###########
        pages = [(BasicSettings(self, beamSettings), "Settings"),
                 (DefaultLayout(self, beamSettings), "Layout"),
                 (Moods(self, beamSettings), "Moods"),
                 (Rules(self, beamSettings), "Rules"),
                 (TagsPreview(self, beamSettings, nowPlayingDataModel), "Tags")]
        ImId=0
        for page, label in pages:
            self.AddPage(page,label,imageId=ImId)
            ImId +=1
