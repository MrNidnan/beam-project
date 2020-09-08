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

from bin.beamsettings import *
from bin.beamutils import getApplicationPath

from bin.dialogs.preferencespanels.basicsettings import BasicSettings
from bin.dialogs.preferencespanels.defaultlayout import DefaultLayout
from bin.dialogs.preferencespanels.moods import Moods
from bin.dialogs.preferencespanels.rules import Rules
from bin.dialogs.preferencespanels.tagspreview import TagsPreview


###################################################################
#                Build main preferences Window                    #
###################################################################

class Preferences(wx.Frame):
    def __init__(self, parent, BeamSettings, nowPlayingDataModel):
        
        ###################
        # CLASS VARIABLES #
        ###################
        self.BeamSettings = BeamSettings
        # Do not use parent for threading
        self.MainWindowParent = parent
        self.nowPlayingDataModel = nowPlayingDataModel
        
        ###############
        # SETPOSITION #
        ###############
        if self.MainWindowParent.IsFullScreen() or self.MainWindowParent.IsMaximized():
            x,y = wx.GetMousePosition()
            y = 300 # Only way to get it to work on MAC
        else:
            x,y = (self.MainWindowParent.GetPosition()+(50,50))
        
        wx.Frame.__init__(self, parent, title="Preferences", pos=(x,y), size=BeamSettings._preferencesSize,
                          style=wx.DEFAULT_FRAME_STYLE & ~ (wx.RESIZE_BORDER | wx.MAXIMIZE_BOX))

        ####################
        # PANEL AND SIZERS #
        ####################
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox = wx.BoxSizer(wx.HORIZONTAL) # For buttons

        #################
        # LISTBOOK MENU #
        #################
        menu = ListBookMenu(panel, self.BeamSettings, self.nowPlayingDataModel)
        
        ###########
        # BUTTONS #
        ###########
        self.button_apply = wx.Button(panel, label="Apply")
        self.button_close = wx.Button(panel, label="Close")
        self.button_apply.Bind(wx.EVT_BUTTON, self.onApply)
        self.button_close.Bind(wx.EVT_BUTTON, self.onClose)

        ###########
        # ARRANGE #
        ###########
        hbox.Add(self.button_apply,flag= wx.LEFT | wx.TOP, border=10)
        hbox.Add(self.button_close, flag= wx.ALL, border=10)
        
        vbox.Add(menu, 1,wx.ALL | wx.EXPAND, 5)
        vbox.Add(hbox, flag=wx.ALIGN_RIGHT)
        
        ###########
        # DISPLAY #
        ###########
        panel.SetSizer(vbox)
        self.Layout()
        self.Show()

#----------------------------------------------------------------------
    def onApply(self, event):
        # Save settings
        beamSettings.SaveConfig(beamSettings.defaultConfigFileName)
        # Reload settings in main-window
        self.settingsUpdated()

    def onClose(self, event):
        self.Destroy()

    def settingsUpdated(self):
        self.MainWindowParent.updateSettings()



###################################################################
#                The ListBookMenu                                 #
###################################################################

class ListBookMenu(wx.Listbook):
    def __init__(self, parent, BeamSettings, nowPlayingDataModel):
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
        pages = [(BasicSettings(self, BeamSettings), "Settings"),
                 (DefaultLayout(self, BeamSettings), "Layout"),
                 (Moods(self, BeamSettings), "Moods"),
                 (Rules(self, BeamSettings), "Rules"),
                 (TagsPreview(self, BeamSettings, nowPlayingDataModel), "Tags")]
        ImId=0
        for page, label in pages:
            self.AddPage(page,label,imageId=ImId)
            ImId +=1


