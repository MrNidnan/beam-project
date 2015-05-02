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
from bin.Moods import Moods

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

    # Initialize DataObject - the model - 
        self.nowPlayingDataModel = NowPlayingDataModel()   # Create the data model object
    
    # Set Icon
        iconFilename = os.path.join(os.getcwd(),'resources','icons','icon_square','icon_square_256px.png')
        
        self.favicon = wx.Icon(iconFilename, wx.BITMAP_TYPE_ANY, 256, 256)
        self.SetIcon(self.favicon)

    # faders
        self.timer1 = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.FadeoutOldImage, self.timer1)

        self.timer2 = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.FadeinNewImage, self.timer2)

    # Statusbar
        self.statusbar = self.CreateStatusBar(style=0)
        self.SetStatusText('Initializing...')

    # Setting up the menu.
        self.filemenu    = wx.Menu()
        self.Aboutmenu   = wx.Menu()
        self.menuPreferences = self.filemenu.Append(wx.ID_ANY, "&Preferences\tCtrl+P"," Configuration tool")
        self.menuMoods       = self.filemenu.Append(wx.ID_ANY, "&Moods\tCtrl+M", "Configure mood")
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
        self.Bind(wx.EVT_MENU, self.OnMoods, self.menuMoods)
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
        self._currentBackgroundPath = []
        self.modifiedBitmap = self._currentBackgroundPath
        self.BackgroundImageWidth, self.BackgroundImageHeight = self.backgroundImage.GetSize()

        self.red = float(1.0)
        self.green = float(1.0)
        self.blue = float(1.0)

        self.currentDisplayRows = []
        self.currentDisplaySettings = []
        self.currentPlaybackStatus = ""
        self.previousMood = ""
        self.currentMood = ""      

        #triggers
        self.triggerAdjustBackgroundRGB = True
        self.triggerResizeBackground = True
        
        #visibility switch
        self.textsAreVisible = True
        
        self.currentlyUpdating = False
        self.applyCurrentSettings()
        self.updateData()



        

########################## END FRAME INITIALIZATION #########################

    def applyCurrentSettings(self):
        self.triggerResizeBackground = True
        self.Refresh()

#
# UPDATE THE DATA
#
    def updateData(self, event = wx.EVT_TIMER):
        self.currentDisplayRows = self.nowPlayingDataModel.DisplayRow
        self.currentPlaybackStatus = self.nowPlayingDataModel.StatusMessage
        self.previousPlaybackStatus = self.nowPlayingDataModel.PreviousPlaybackStatus
                
        if not self.currentlyUpdating:
            self.currentlyUpdating = True
            tmpSettings = deepcopy(beamSettings)
            wx.lib.delayedresult.startWorker(self.getDataFinished, self.nowPlayingDataModel.ExtractPlaylistInfo( tmpSettings ) )

    def getDataFinished(self, result):
        
        self.textsAreVisible = False
        self.currentDisplayRows = self.nowPlayingDataModel.DisplayRow
        self.currentPlaybackStatus = self.nowPlayingDataModel.StatusMessage
        self.currentMood = self.nowPlayingDataModel.CurrentMood
        self.previousMood = self.nowPlayingDataModel.PreviousMood
        self.currentDisplaySettings = self.nowPlayingDataModel.DisplaySettings
        self.currentlyUpdating = False
        
        if self.previousMood != self.currentMood:
            print "New mood: ", self.currentMood
            # If background changed, fade it
            if (self.nowPlayingDataModel.BackgroundImage != self._currentBackgroundPath and
                self.nowPlayingDataModel.BackgroundImage != ""):
                self._currentBackgroundPath = self.nowPlayingDataModel.BackgroundImage
                self.fadeBackground()
            else:
                self.textsAreVisible = True
        else:
            self.textsAreVisible = True

        self.Refresh()
        self.nowPlayingDataModel.PreviousMood = self.currentMood
        self.SetStatusText(self.currentPlaybackStatus) 

#####################################################
# BACKGROUND resize and repaint
#
    def OnSize(self, size):
        self.triggerResizeBackground = True
        self.Refresh()
    def OnEraseBackground(self, evt):
        pass
    def OnPaint(self, event):
        dc = wx.BufferedPaintDC(self)
        self.Draw(dc)

    def drawBackgroundBitmap(self, dc):
        cliWidth, cliHeight = self.GetClientSize()
        if not cliWidth or not cliHeight:
            return

        if self.triggerResizeBackground or self.triggerAdjustBackgroundRGB:
            try:
                Image = wx.ImageFromBitmap(self.backgroundImage)
                #adjust BackgroundChannels - currently used for fading effect
                if self.triggerAdjustBackgroundRGB:
                    Image = Image.AdjustChannels(self.red, self.green, self.blue, 1.0)
                    self.triggerAdjustBackgroundRGB = False
                #resize current background picture - currently used at main frame resizing    
                if self.triggerResizeBackground:
                    # Figure out how to scale the background image and position it
                    aspectRatioWindow = float(cliHeight) / float(cliWidth)
                    aspectRatioBackground = float(self.BackgroundImageHeight) / float(self.BackgroundImageWidth)
                    if aspectRatioWindow >= aspectRatioBackground:
                        # Window is too tall, scale to height
                        Image = Image.Scale(cliHeight*self.BackgroundImageWidth / self.BackgroundImageHeight, cliHeight, wx.IMAGE_QUALITY_NORMAL)
                    else:
                        # Window is too wide, scale to width
                        Image = Image.Scale(cliWidth, cliWidth*self.BackgroundImageHeight / self.BackgroundImageWidth, wx.IMAGE_QUALITY_NORMAL)
                        Image = Image.AdjustChannels(self.red, self.green, self.blue, 1.0)
                    self.triggerResizeBackground = False
                #
                self.modifiedBitmap = wx.BitmapFromImage(Image)
            except:
                self.modifiedBitmap = self.backgroundImage

            
        # Position the image and draw it
        resizedWidth, resizedHeight = self.modifiedBitmap.GetSize()
        self.xPosResized = (cliWidth - resizedWidth)/2
        self.yPosResized = (cliHeight - resizedHeight)/2
        dc.DrawBitmap(self.modifiedBitmap, self.xPosResized, self.yPosResized)

    # DRAW TEXT
    #
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

            # Find length and position of text


            # Centered
            if Settings['Alignment'] == 'Center':
                while TextWidth > cliWidth:
                    try:
                        text = text[:-1]
                        TextWidth, TextHeight = dc.GetTextExtent(text)
                    except:
                        text = text[:-2]
                        TextWidth, TextHeight = dc.GetTextExtent(text)
                    if TextWidth < cliWidth:
                        try:
                            text = text[:-2]
                            TextWidth, TextHeight = dc.GetTextExtent(text)
                        except:
                            text = text[:-3]
                            TextWidth, TextHeight = dc.GetTextExtent(text)
                        text = text + '...'
                TextWidth, TextHeight = dc.GetTextExtent(text)
            # Position
                WidthPosition = (cliWidth-TextWidth)/2

            # Left and Right alignment
            else:
                TextSpaceAvailable = int((100-Settings['Position'][1])*cliWidth)
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
                # Alignment
                if Settings['Alignment'] == 'Left':
                    WidthPosition = int(Settings['Position'][1]*cliWidth/100)
                elif Settings['Alignment'] == 'Right':
                    WidthPosition = cliWidth - (int(Settings['Position'][1]*cliWidth/100)+TextWidth)
                else:
                    return
                        
            # Draw the text
            dc.DrawText(text, WidthPosition,  HeightPosition)

#
# This is where the scaling of the image takes place
#
    def Draw(self, dc):
    # Get width and height of window
        cliWidth, cliHeight = self.GetClientSize()
        if not cliWidth or not cliHeight:
            return
        dc.Clear()

        self.drawBackgroundBitmap(dc)
        
        self.drawTexts(dc)


#####################################################
#
# OPEN/IMPORT SETTINGS
#
    def OnPreferences(self, event):
        PreferencesDialog = Preferences(self)
        PreferencesDialog.Show()

#
# MOODS SETTINGS
#
    def OnMoods(self, event):
        MoodsDialog = Moods(self)
        MoodsDialog.Show()


#
# FULLSCREEN
#
    def fullScreen(self, event):
        # Needed for Mac
        if platform.system() == 'Darwin':
            if self.IsFullScreen():
                self.statusbar.Show()
            else:
                self.statusbar.Hide()
        self.ShowFullScreen(not self.IsFullScreen())

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

####################################################
#
# FADE BACKGROND
#

    def fadeBackground(self, fadeSpeed = 5):
        #print "FadeNewBackground"
        self.red = float(1.0)
        self.green = float(1.0)
        self.blue = float(1.0)
        self.delta = float(0.10)
        self.fadeSpeed = fadeSpeed


        # start the timer for the fade-out
        self.timer1.Start(self.fadeSpeed)

    def FadeoutOldImage(self, event):
        self.textsAreVisible = False
        self.red -= 2 * self.delta
        self.green -= 2 * self.delta
        self.blue -= 2 * self.delta
        if self.red >= 0 and self.red <= 1:
            # re-fire the OnPaint event using self.Refresh
            self.triggerAdjustBackgroundRGB = True
            self.triggerResizeBackground = True
            self.Refresh()
        else:
            #stop the fade-out timer
            self.timer1.Stop()

            #load the new background image
            self.backgroundImage = wx.Bitmap(os.path.join(os.getcwd(), self._currentBackgroundPath))
            self.modifiedBitmap = self._currentBackgroundPath
            self.BackgroundImageWidth, self.BackgroundImageHeight = self.backgroundImage.GetSize()
            self.triggerResizeBackground = True
            
            #start fading it in
            self.textsAreVisible = True

            self.red = float(0.0)
            self.green = float(0.0)
            self.blue = float(0.0)
            self.timer2.Start(self.fadeSpeed)


# -----------------------------------------------------------------------------------
    def FadeinNewImage(self, event):

        self.red += self.delta
        self.green += self.delta
        self.blue += self.delta

        if self.red >= 0 and self.red <= 1:
            self.triggerAdjustBackgroundRGB = True
            self.triggerResizeBackground = True
        else:
            self.timer2.Stop()
        
        self.Refresh()

