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


import wx, wx.html
import os, sys
import wx.lib.delayedresult

from bin.beamsettings import *
from bin.nowplayingdatamodel import *
from bin.Preferences import Preferences
from bin.dialogs.helpdialog import HelpDialog
from bin.dialogs import aboutdialog
from bin.dialogs import closedialog

from copy import deepcopy

##################################################
# MAIN WINDOW - FRAME
##################################################
class beamMainFrame(wx.Frame):
    def __init__(self, settings = None):
    # Size and position of the main window
        wx.Frame.__init__(self, None, title=beamSettings.mainFrameTitle, pos=(150,150), size=(800,600))
        self.SetDoubleBuffered(True)
        
    # Start the timer reading data
        self.DataTimer()
        
    # Initialize DataObject - the model - 
        self.nowPlayingDataModel = NowPlayingDataModel()
    
    # Set Icon
        iconFilename = os.path.join(os.getcwd(),'resources','icons','icon_square','icon_square_256px.png')
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
        self.Aboutmenu   = wx.Menu()
        self.menuPreferences = self.filemenu.Append(wx.ID_ANY, "&Preferences\tCtrl+P"," Configuration tool")
        self.menuFullScreen  = self.filemenu.Append(wx.ID_ANY, "&Fullscreen\tF11", "Set fullscreen")
        self.menuExit    = self.filemenu.Append(wx.ID_EXIT,"E&xit"," Terminate the program")
        self.menuAbout   = self.Aboutmenu.Append(wx.ID_ABOUT, "&About"," Information about this program")
        self.menuHelp    = self.Aboutmenu.Append(wx.ID_ANY, "&Help"," Getting started")

    # Creating the menubar.
        self.menuBar = wx.MenuBar()
        self.menuBar.Append(self.filemenu,"&File")    # Adding the "file menu" to the MenuBar
        self.menuBar.Append(self.Aboutmenu,"&About")  # Adding the "About menu" to the MenuBar
        self.SetMenuBar(self.menuBar)  # Adding the MenuBar to the Frame content.
        
        # Events.
        self.Bind(wx.EVT_MENU, self.OnPreferences, self.menuPreferences)
        self.Bind(wx.EVT_MENU, self.OnClose, self.menuExit)
        self.Bind(wx.EVT_MENU, self.OnAbout, self.menuAbout)
        self.Bind(wx.EVT_MENU, self.OnHelp, self.menuHelp)
        self.Bind(wx.EVT_MENU, self.fullScreen, self.menuFullScreen)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Bind(wx.EVT_LEFT_DCLICK, self.fullScreen)
        
        # Background
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        
        self.backgroundImage = wx.EmptyBitmap(800,600)
        self.SetBackgroundColour(wx.BLACK)
        self._currentBackgroundPath = []
        self.modifiedBitmap = self._currentBackgroundPath
        self.BackgroundImageWidth, self.BackgroundImageHeight = self.backgroundImage.GetSize()

        self.alpha = float(1.0)
        self.red = float(1.0)
        self.blue = float(1.0)
        self.green = float(1.0)
        
        self.currentDisplayRows = []
        self.currentDisplaySettings = []
        self.currentPlaybackStatus = ""
        self.previousMood = ""
        self.currentMood = ""      
        

        #trigger
        self.triggerResizeBackground = True
        self.textsAreVisible = False
        self.FadeDirection = 'In'
        self.RotateBackgroundTrigger = False
        
        #visibility switch
        self.showStatusBar()
        self.currentlyUpdating = False
        self.updateData()



########################## END FRAME INITIALIZATION #########################


########################################################
# Update data - Executed from top to bottom with exception if preferences changed
########################################################
    def updateData(self, event = wx.EVT_TIMER):
        self.currentDisplayRows = self.nowPlayingDataModel.DisplayRow
        self.currentPlaybackStatus = self.nowPlayingDataModel.StatusMessage
        self.previousPlaybackStatus = self.nowPlayingDataModel.PreviousPlaybackStatus
        
        if not self.currentlyUpdating:
            self.currentlyUpdating = True
            tmpSettings = deepcopy(beamSettings)
            wx.lib.delayedresult.startWorker(self.getDataFinished, self.nowPlayingDataModel.ExtractPlaylistInfo( tmpSettings ) )
    
        self.DataTimer() # Reset the timer

    def getDataFinished(self, result):
        self.currentlyUpdating = False
        
        if self.nowPlayingDataModel.playlistChanged:
            self.processData() #Only update if playlist has changed

    def processData(self):
        self.nowPlayingDataModel.applyRules(beamSettings)
        self.nowPlayingDataModel.applyMood(beamSettings)
        self.nowPlayingDataModel.buildDisplayLines(beamSettings)
        self.updateMood()

    def updateMood(self):
        self.textsAreVisible = False
        self.currentDisplayRows = self.nowPlayingDataModel.DisplayRow
        self.currentPlaybackStatus = self.nowPlayingDataModel.StatusMessage
        self.currentMood = self.nowPlayingDataModel.CurrentMood
        self.previousMood = self.nowPlayingDataModel.PreviousMood
        self.currentDisplaySettings = self.nowPlayingDataModel.DisplaySettings
        self.RotateBackground = self.nowPlayingDataModel.RotateBackground
        self.RotateTimer = self.nowPlayingDataModel.RotateTimer
        
        if self.previousMood != self.currentMood:
            print "New mood: ", self.currentMood
            # If background changed, fade it
            if (self.nowPlayingDataModel.BackgroundImage != self._currentBackgroundPath and
                self.nowPlayingDataModel.BackgroundImage != ""):
                self._currentBackgroundPath = self.nowPlayingDataModel.BackgroundImage
                self.rotateBackground()
            else:
                self.textsAreVisible = True
        else:
            self.textsAreVisible = True
    
        self.nowPlayingDataModel.PreviousMood = self.currentMood
        self.SetStatusText(self.currentPlaybackStatus)
        self.Refresh()

########################################################
# Painter
########################################################
    def OnSize(self, size):
        self.triggerResizeBackground = True
        self.Refresh()
    def OnEraseBackground(self, evt):
        pass
    def OnPaint(self, event):
        pdc = wx.BufferedPaintDC(self)
        try:
            dc = wx.GCDC(pdc)
        except:
            dc = pdc
        self.Draw(dc)

########################################################
# Draw background
########################################################
    def drawBackgroundBitmap(self, dc):
        cliWidth, cliHeight = self.GetClientSize()
        if not cliWidth or not cliHeight:
            return

        try:
            Image = wx.ImageFromBitmap(self.backgroundImage)
            #resize current background picture - currently used at main frame resizing

            aspectRatioWindow = float(cliHeight) / float(cliWidth)
            aspectRatioBackground = float(self.BackgroundImageHeight) / float(self.BackgroundImageWidth)
            if aspectRatioWindow >= aspectRatioBackground:
                # Window is too tall, scale to height
                Image = Image.Scale(cliHeight*self.BackgroundImageWidth / self.BackgroundImageHeight, cliHeight, wx.IMAGE_QUALITY_NORMAL)
            else:
                # Window is too wide, scale to width
                Image = Image.Scale(cliWidth, cliWidth*self.BackgroundImageHeight / self.BackgroundImageWidth, wx.IMAGE_QUALITY_NORMAL)
            # Fader
            if self.alpha <1 or self.red <1 or self.blue <1 or self.green <1:
                Image = Image.AdjustChannels(self.red, self.green, self.blue, self.alpha)
            
            self.triggerResizeBackground = False
            self.modifiedBitmap = wx.BitmapFromImage(Image)
        except:
            self.modifiedBitmap = self.backgroundImage

            
        # Position the image and draw it
        resizedWidth, resizedHeight = self.modifiedBitmap.GetSize()
        self.xPosResized = (cliWidth - resizedWidth)/2
        self.yPosResized = (cliHeight - resizedHeight)/2
        dc.DrawBitmap(self.modifiedBitmap, self.xPosResized, self.yPosResized, True)

########################################################
# DRAW TEXT
########################################################
    def drawTexts(self, dc):
        
        if self.textsAreVisible == False:
            return

        cliWidth, cliHeight = self.GetClientSize()
        if not cliWidth or not cliHeight:
            return

        for j in range(0, len(self.currentDisplaySettings)):

            #Text and settings
            text = self.currentDisplayRows[j]
            Settings = self.currentDisplaySettings[j]

            # Get size and position
            Size = Settings['Size']*cliHeight/100
            HeightPosition = int(Settings['Position'][0]*cliHeight/100)

            # Set font from settings
            face = Settings['Font']
            
            try:
                dc.SetFont(wx.Font(Size, 
                               wx.ROMAN, 
                               beamSettings.FontStyleDictionary[Settings['Style']],
                               beamSettings.FontWeightDictionary[Settings['Weight']],
                               False, 
                               face))
            except:
                dc.SetFont(wx.Font(Size, 
                               wx.ROMAN, 
                               beamSettings.FontStyleDictionary[Settings['Style']], 
                               beamSettings.FontWeightDictionary[Settings['Weight']], 
                               False, 
                               "Liberation Sans"))

            # Set font color, in the future, drawing a shadow ofsetted with the same text first might make a shadow!
            dc.SetTextForeground(eval(Settings['FontColor']))

            # Check if the text fits, cut it and add ...
            if platform.system() == 'Darwin':
                try:
                    text = text.decode('utf-8')
                except:
                    pass
            TextWidth, TextHeight   = dc.GetTextExtent(text)

#
# Find length and position of text
#
            if Settings['Alignment'] == 'Center':
                TextSpaceAvailable = cliWidth
            else:
                TextSpaceAvailable = int((100-Settings['Position'][1])*cliWidth)

#
# TEXT FLOW = CUT
#
            if Settings['TextFlow'] == 'Cut':
                while TextWidth > TextSpaceAvailable:
                    try:
                        text = text[:-1]
                        TextWidth, TextHeight = dc.GetTextExtent(text)
                    except:
                        text = text[:-2]
                        TextWidth, TextHeight = dc.GetTextExtent(text)
                    if TextWidth < TextSpaceAvailable:
                        try:
                            text = text[:-2]
                            TextWidth, TextHeight = dc.GetTextExtent(text)
                        except:
                            text = text[:-3]
                            TextWidth, TextHeight = dc.GetTextExtent(text)
                        text = text + '...'
                TextWidth, TextHeight = dc.GetTextExtent(text)
#
# TEXT FLOW = SCALE
#

            if Settings['TextFlow'] == 'Scale':
                while TextWidth > int(TextSpaceAvailable*0.95):
                    # 10% Scaling each time
                    Size = int(Size*0.9)
                    try:
                       dc.SetFont(wx.Font(Size,
                                    wx.ROMAN,
                                    beamSettings.FontStyleDictionary[Settings['Style']],
                                    beamSettings.FontWeightDictionary[Settings['Weight']],
                                    False,
                                    face))
                    except:
                        dc.SetFont(wx.Font(Size,
                               wx.ROMAN,
                               beamSettings.FontStyleDictionary[Settings['Style']],
                               beamSettings.FontWeightDictionary[Settings['Weight']],
                               False,
                               "Liberation Sans"))
                    TextWidth, TextHeight = dc.GetTextExtent(text)

# Alignment position
            if Settings['Alignment'] == 'Left':
                WidthPosition = int(Settings['Position'][1]*cliWidth/100)
            elif Settings['Alignment'] == 'Right':
                WidthPosition = cliWidth - (int(Settings['Position'][1]*cliWidth/100)+TextWidth)
            elif Settings['Alignment'] == 'Center':
                WidthPosition = (cliWidth-TextWidth)/2
            else:
                return
                        
            # Draw the text
            dc.DrawText(text, WidthPosition,  HeightPosition)

########################################################
# DRAW
########################################################
    def Draw(self, dc):
    # Get width and height of window
        cliWidth, cliHeight = self.GetClientSize()
        if not cliWidth or not cliHeight:
            return
        dc.Clear()
        self.drawBackgroundBitmap(dc)
        self.drawTexts(dc)


########################################################
# Buttons and menues
########################################################
    def OnPreferences(self, event):
        try:
            self.PreferencesDialog.Raise()
        except:
            self.PreferencesDialog = Preferences(self)
            self.PreferencesDialog.Show()


#
# FULLSCREEN
#
    def fullScreen(self, event):
        # Needed for Mac
        if platform.system() == 'Darwin':
            self.showStatusBar()
        self.ShowFullScreen(not self.IsFullScreen())

#
# Hide/show statusbar
#
    def showStatusBar(self):
        self.triggerResizeBackground = True
        if beamSettings._showStatusbar == 'True':
            self.statusbar.Show()
        else:
            self.statusbar.Hide()

#
# Show 'Close dialog
#
    def OnClose(self, event):
        closedialog.ShowCloseDialog(self)
#
# Show 'About Dialog'
#
    def OnAbout(self, event):
        aboutdialog.ShowAboutDialog(self)
#
# Show 'Help'
#
    def OnHelp(self, event):
        help_dialog = HelpDialog(self)
        help_dialog.Show()


########################################################
# Change background
########################################################
    def changeBackground(self):
        
        self.transitionSpeed = int(int(beamSettings._moodTransitionSpeed) / 100)
        self.delta = float(1/float(self.transitionSpeed))

        #####################
        # Choose transition #
        #####################
        
        # Fade directly
        if beamSettings._moodTransition == 'Fade directly' or self.RotateBackgroundTrigger == True:

            self.alpha = float(0.0)
            
            # Load the new background image
            self.backgroundImage = wx.Bitmap(os.path.join(os.getcwd(), self._currentBackgroundPath))
            self.modifiedBitmap = self._currentBackgroundPath
            
            # Set triggers
            self.triggerResizeBackground = True
            self.textsAreVisible = True
            
            # start the timer for the transition
            self.TransitionTimer.Start(self.transitionSpeed)
            return
        
        
        # Fade to black
        if  beamSettings._moodTransition == 'Fade to black':
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
                self.backgroundImage = wx.Bitmap(os.path.join(os.getcwd(), self._currentBackgroundPath))
                self.modifiedBitmap = self._currentBackgroundPath
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
        # Change background without any transition
            self.switchBackground()


########################################################
# No transition
########################################################
    def switchBackground(self):
        
        self.triggerResizeBackground = True
        self.backgroundImage = wx.Bitmap(os.path.join(os.getcwd(), self._currentBackgroundPath))
        self.modifiedBitmap = self._currentBackgroundPath
        self.BackgroundImageWidth, self.BackgroundImageHeight = self.backgroundImage.GetSize()
        self.textsAreVisible = True
        self.Refresh()

########################################################
# TIMER - USED for Fade directly and Fade to black
########################################################
    def transition(self, event):
        if beamSettings._moodTransition == 'Fade directly' or self.RotateBackgroundTrigger == True:
            self.FadeImage()
            return
        if beamSettings._moodTransition == 'Fade to black' and self.FadeDirection == 'Out':
            self.FadeToBlackImage()
            return
        if beamSettings._moodTransition == 'Fade to black'and self.FadeDirection == 'In':
            self.FadeBackImage()
            return


########################################################
# Fade directly
########################################################
    def FadeImage(self):
        self.alpha += self.delta
        if self.alpha >=1:
            self.alpha = 1.0
            self.TransitionTimer.Stop()
        self.Refresh()

########################################################
# Fade To black - 2 functions (IN and OUT)
########################################################
    def FadeToBlackImage(self):
    
        self.red -= 2* self.delta
        self.green -= 2* self.delta
        self.blue -= 2* self.delta
        
        if self.red >=0 and self.red <=1:
            self.triggerResizeBackground = True
            self.textsAreVisible = False
            self.Refresh()
        else:
            self.red = float(0.0)
            self.green = float(0.0)
            self.blue = float(0.0)
            self.direction = 'in' # Change fading direction
            self.TransitionTimer.Stop()
            self.Refresh()

            self.FadeDirection = 'In'
            self.changeBackground()
    
    def FadeBackImage(self):
        self.red +=  self.delta
        self.green +=  self.delta
        self.blue +=  self.delta
        
        if self.red >=0 and self.red <=1:
            self.triggerResizeBackground = True
            self.Refresh()
        else:
            self.red = float(1.0)
            self.green = float(1.0)
            self.blue = float(1.0)
            self.FadeDirection = 'Out'
            self.TransitionTimer.Stop()
            self.Refresh()

########################################################
# Rotate Background
########################################################
    def rotateBackground(self , event = wx.EVT_TIMER):
        # Starts, stops and executes the rotate-background function.

        # Start the rotation
        if self.RotateBackground == 'linear' or self.RotateBackground == 'random':
            # Start the timer
            try:
                self.RotateBackgroundTimer = wx.Timer(self)
                self.Bind(wx.EVT_TIMER, self.rotateBackground, self.RotateBackgroundTimer)
                self.RotateBackgroundTimer.Start(int(self.RotateTimer)*1000)
            except:
                self.RotateBackgroundTimer.Stop()
                self.RotateBackgroundTimer.Start(self.RotateTimer)
            # Find the files
            (path, file) = os.path.split(self._currentBackgroundPath)
            backgrounds = os.listdir(path)
            # Find our index
            position = backgrounds.index(file)
            
            # Linear in the folder
            if self.RotateBackground == 'linear':
                try:
                    self._currentBackgroundPath = os.path.join(path,backgrounds[position+1])
                except:
                    self._currentBackgroundPath = os.path.join(path,backgrounds[0])
                self.RotateBackgroundTrigger = True
            # Random
            else:
                self.RotateBackgroundTrigger = True

        # Stop the rotation
        if self.RotateBackground == 'no':
            self._currentBackgroundPath = self.nowPlayingDataModel.BackgroundImage
            self.RotateBackgroundTrigger = False
            try:
                self.RotateBackgroundTimer.Stop()
            except:
                pass


        # Update the background
        self.changeBackground()
    


########################################################
# Data timer
########################################################
    def DataTimer(self):
    # If the configuration have a timer on how often to update the data
        try:
        # There is not timer, so create and start it
            self.timer = wx.Timer(self)
            self.Bind(wx.EVT_TIMER, self.updateData, self.timer)
            self.timer.Start(beamSettings._updateTimer)
        except:
        # There is already a timer restart with new update timing
            self.timer.Stop()
            self.timer.Start(beamSettings._updateTimer)

