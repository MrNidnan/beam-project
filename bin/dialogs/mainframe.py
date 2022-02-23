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
from bin.displaydata import DisplayData
from bin.dialogs.displaypanel import DisplayPanel

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

    def __init__(self):
        # Size and position of this main window
        # beamsettings loaded in beam.py
        wx.Frame.__init__(self, None, title=beamSettings.mainframetitle + " V" + beamSettings.beamVersion, pos=(150, 150), size=(800, 600))

        # only required for display
        # self.SetDoubleBuffered(True)

        # self reference to be removed later
        self.displayData = DisplayData(self)

        # self reference to be removed later
        self.displayFrame = DisplayFrame(self.displayData)

        # Set Icon
        appPath = getBeamHomePath()
        iconFilename = os.path.join(appPath,'resources','icons','icon_square','icon_square_256px.png')
        self.favicon = wx.Icon(iconFilename, wx.BITMAP_TYPE_ANY, 256, 256)
        self.SetIcon(self.favicon)


        # start first update (worker) instantly
        self.displayData.updateData()
        # Initialize and start the timer for further updateData() in main loop
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.displayData.updateData, self.timer)
        self.timer.Start(beamSettings._updateTimer)  # Refresh time in ms from config, default 6311

        # faders
        self.TransitionTimer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.displayData.transition, self.TransitionTimer)
        self.RotateBackgroundTimer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.displayData.rotateBackground, self.RotateBackgroundTimer)

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
        # self.Bind(wx.EVT_LEFT_DCLICK, self.fullScreen)


        ####################
        # PANEL AND SIZERS #
        ####################
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox = wx.BoxSizer(wx.HORIZONTAL) # For buttons

        #################
        # LISTBOOK MENU #
        #################
        listBookMenu = ListBookMenu(panel, beamSettings, self.displayData)
        self.previewPanel = listBookMenu.pages[0][0];

        
        ###########
        # BUTTONS #
        ###########
        self.applyBtn = wx.Button(panel, label="Apply")
        self.applyBtn.Bind(wx.EVT_BUTTON, self.onApply)
        hbox.Add(self.applyBtn, flag=wx.LEFT | wx.TOP, border=10)

        self.displayBtn = wx.Button(panel, label="Display")
        self.displayBtn.Bind(wx.EVT_BUTTON, self.onDisplay)
        hbox.Add(self.displayBtn, flag= wx.ALL, border=10)

        ###########
        # ARRANGE #
        ###########
        vbox.Add(listBookMenu, 1, wx.ALL | wx.EXPAND, 5)
        vbox.Add(hbox, flag=wx.ALIGN_RIGHT)

        ###########
        # DISPLAY #
        ###########
        panel.SetSizer(vbox)
        self.Layout()
        self.Show()
        self.showStatusBar()

        logging.info("Beam started")

        ########################## END OF INITIALIZATION #########################


    #
    # Show 'Close dialog
    #
    def onClose(self, event):
        try:
            self.displayFrame.Hide()
            self.Hide()
            self.Destroy()
            logging.info("Beam ended")
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
        try:
            # Save settings
            beamSettings.saveConfig(beamSettings.configfilename)
            # Reload settings in main-window
            self.updateSettings()
        except Exception as e:
            logging.error(e, exc_info=True)


    def onDisplay(self, event):
        try:
            if self.displayFrame.IsShown():
                self.displayFrame.Hide()
                # self.displayBtn.SetLabel("Display")
            else:
                self.displayFrame.Show()
                # self.displayBtn.SetLabel("Hide")
        except Exception as e:
            logging.error(e, exc_info=True)



    #
    #
    #
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



    # UPDATE INFO FROM PREFERENCES WINDOW
    def updateSettings(self):
        try:
            self.showStatusBar()
            self.displayData.processData()
            # Starts and stops rotation if it has changed.
            # if (self.RotateBackgroundTimer.IsRunning() and self.RotateBackground == 'no') or (
            #         not self.RotateBackgroundTimer.IsRunning() and not self.RotateBackground == 'no') or (
            #         not self.RotateBackgroundTimer.IsRunning() and self.RotateBackground == 'no'):
            #     self.rotateBackground()
        except Exception as e:
            logging.error(e, exc_info=True)
            pass


    def refreshDisplay(self):
        try:
            self.displayFrame.Refresh()
            self.previewPanel.Refresh()
        except Exception as e:
            logging.error(e, exc_info=True)



###################################################################
#                The ListBookMenu                                 #
###################################################################
class ListBookMenu(wx.Listbook):

    # pages = []

    def __init__(self, parent, beamSettings, displayData):
        wx.Listbook.__init__(self, parent, wx.ID_ANY, style = wx.BK_DEFAULT)
        
        ##########
        # IMAGES #
        ##########
        imagelist = wx.ImageList(32,32)
        urllist = ["0-DisplayFrame32.png", "1-BasicSettings32.png", "2-DefaultDisplay32.png", "3-Moods32.png", "4-Rules32.png", "5-Tags32.png"]
        for urls in urllist:
            appPath = getBeamHomePath()
            # /resources/icons/preferences
            bmp = wx.Bitmap(os.path.join(appPath, 'resources', 'icons', 'preferences', urls), wx.BITMAP_TYPE_PNG)
            imagelist.Add(bmp)
        
        self.AssignImageList(imagelist)
        
        ###########
        # CONTENT #
        ###########
        self.pages = [
                    # preview must be first in array
                    (DisplayPanel(self, displayData), "Preview"),
                    (BasicSettings(self, beamSettings), "Settings"),
                    (DefaultLayout(self, beamSettings), "Layout"),
                    (Moods(self, beamSettings), "Moods"),
                    (Rules(self, beamSettings), "Rules"),
                    (TagsPreview(self, beamSettings, displayData.nowPlayingData), "Tags")
                 ]
        ImId=0
        for page, label in self.pages:
            self.AddPage(page,label,imageId=ImId)
            ImId +=1
