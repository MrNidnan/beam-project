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
from bin.dialogs.preferencespanels.displaypanel import DisplayPanel

from bin.dialogs.preferencespanels.basicsettingspanel import BasicSettingsPanel
from bin.dialogs.preferencespanels.moodspanel import MoodsPanel
from bin.dialogs.preferencespanels.rulespanel import RulesPanel
from bin.dialogs.preferencespanels.tagspreviewpanel import TagsPreviewPanel

if platform.system() == 'Linux' or platform.system() == 'Darwin':
    from bin.dialogs.preferencespanels.dmxcontrolspanel import DMXcontrolsPanel

from bin.dialogs.helpdialog import HelpDialog
from bin.dialogs import aboutdialog
from bin.dialogs.displayframe import DisplayFrame
from bin.network import BeamNetworkService


###################################################################
#                Build main preferences Window                    #
###################################################################

class MainFrame(wx.Frame):

    def __init__(self):
        # Size and position of this main window
        # beamsettings loaded in beam.py
        wx.Frame.__init__(self, None, title=beamSettings.getString("mainframetitle") + " V" + beamSettings.getString("version"), pos=(150, 150), size=(800, 600))

        # only required for display
        # self.SetDoubleBuffered(True)

        self.displayData = DisplayData(self)
        self.displayFrame = DisplayFrame(self.displayData)
        self.networkService = BeamNetworkService()
        self.networkService.start()

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
        # pyinstaller TypeError: Timer.Start(): argument 1 has unexpected type 'str'
        self.timer.Start(beamSettings.getUpdtime())  # Refresh time in ms from config, default 6311

        # faders
        self.TransitionTimer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.displayData.transition, self.TransitionTimer)
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
        listBookMenu = ListBookMenu(panel, self, beamSettings)
        #listBookMenu.SetBackgroundColour(wx.Colour(136,136,136))
        self.previewPanel = listBookMenu.pages[0][0]

        
        ###########
        # BUTTONS #
        ###########
        self.saveBtn = wx.Button(panel, label="Save")
        self.saveBtn.Bind(wx.EVT_BUTTON, self.onSave)
        hbox.Add(self.saveBtn, flag=wx.LEFT | wx.TOP, border=10)

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

        logging.info("Beam started")

        ########################## END OF INITIALIZATION #########################


    def rotateBackground(self, event=wx.EVT_TIMER):
        # Starts, stops and executes the rotate-background function.
        self.displayData.rotateBackground(event)

    #
    # Show 'Close dialog
    #
    def onClose(self, event):
        try:
            if self.displayFrame.IsShown():
                closeDialog = dialog = wx.MessageDialog(self, message="Are you sure you want to quit?", caption="Display Frame shown",
                                              style=wx.YES_NO, pos=wx.DefaultPosition)
                response = closeDialog.ShowModal()
                if response != wx.ID_YES:
                    event.StopPropagation()
                else:
                    self.destroyFrame()
            else:
                self.destroyFrame()
        except Exception as e:
            logging.error(e, exc_info=True)


    def destroyFrame(self):
        try:
            self.networkService.stop()
        except Exception as e:
            logging.error(e, exc_info=True)
        self.displayFrame.Hide()
        self.displayFrame.Destroy()
        self.Hide()
        self.Destroy()

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


    def onSave(self, event):
        try:
            # Save settings
            beamSettings.dumpConfig()
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


    '''
    #
    #
    #
    def updateSettings(self):
        try:
            # self.showStatusBar()
            self.processData()
            # Starts and stops rotation if it has changed.
            # To be done
            # if (self.RotateBackgroundTimer.IsRunning() and self.RotateBackground == 'no') or (not self.RotateBackgroundTimer.IsRunning() and not self.RotateBackground == 'no') or (not self.RotateBackgroundTimer.IsRunning() and self.RotateBackground == 'no'):
            #    self.rotateBackground()
        except Exception as e:
            logging.error(e, exc_info=True)
    '''
    #
    # Hide/show statusbar
    #
    def showStatusBar(self):
        try:
            self.triggerResizeBackground = True
            if beamSettings.getShowStatusbar() == 'True':
                self.statusbar.Show()
            else:
                self.statusbar.Hide()
        except Exception as e:
            logging.error(e, exc_info=True)


    # UPDATE INFO FROM PREFERENCES WINDOW
    def updateSettings(self):
        try:
            self.networkService.stop()
            self.networkService.start()
            # self.showStatusBar()
            self.displayData.processData()
            self.networkService.publish_display_state(self.displayData)
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
            self.networkService.publish_display_state(self.displayData)
        except Exception as e:
            logging.error(e, exc_info=True)



###################################################################
#                The ListBookMenu                                 #
###################################################################
class ListBookMenu(wx.Listbook):

    # pages = []

    def __init__(self, parent, mainFrame, beamSettings):
        wx.Listbook.__init__(self, parent, wx.ID_ANY, style = wx.BK_DEFAULT)

        displayData = mainFrame.displayData
        ##########
        # IMAGES #
        ##########
        imagelist = wx.ImageList(32,32)

        # urllist = ["0-DisplayFrame32.png", "1-BasicSettings32.png", "2-DefaultDisplay32.png", "3-Moods32.png", "4-Rules32.png", "5-Tags32.png"]
        # urllist = ["0-DisplayFrame32.png", "1-BasicSettings32.png", "3-Moods32.png", "4-Rules32.png", "5-Tags32.png"]
        urllist = ["2-DefaultDisplay32.png", "1-BasicSettings32.png", "3-Moods32.png", "4-Rules32.png", "5-Tags32.png"]
        if platform.system() == 'Linux' or platform.system() == 'Darwin': urllist.append("6-DMXcontrols32.png")
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
                    (BasicSettingsPanel(self, beamSettings), "Settings"),
                    # (DefaultLayoutPanel(self, beamSettings), "Layout"),
                    (MoodsPanel(self, mainFrame, beamSettings), "Layout"),
                    (RulesPanel(self, mainFrame, beamSettings), "Rules"),
                    (TagsPreviewPanel(self, displayData.nowPlayingData), "Tags")
                 ]
        if platform.system() == 'Linux' or platform.system() == 'Darwin': self.pages.append((DMXcontrolsPanel(self, beamSettings), "DMX"))
        ImId=0
        for page, label in self.pages:
            self.AddPage(page,label,imageId=ImId)
            ImId +=1
