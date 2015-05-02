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

import wx
import os

from bin.beamsettings import *
from bin.dialogs.editlayoutdialog import EditLayoutDialog

#
# Build Mood Layout Window
#

class EditMood(wx.Dialog):
    def __init__(self, parent, RowSelected, mode):
        self.MainWindowParent = parent
        wx.Dialog.__init__(self, parent, title=mode, size=(400,500))
        self.RowSelected = RowSelected
        self.mode = mode
        self.Settings = {}
        
        # Define choices
        self.Fields   = ["%Artist","%Album","%Title","%Genre","%Comment","%Composer","%Year", "%AlbumArtist", "%Performer", "%Singer","%IsCortina"]
        # Get item
        if self.RowSelected<len(beamSettings._moods):
            # Get the properties of the selected item
            self.Settings   = beamSettings._moods[self.RowSelected]
        else:
            # Create a new default setting
            self.Settings   = ({"Active": "yes", "Field3": "something","Field2": "contains","Field1": "%Title",
                               "Type": "Mood", "Name": "My Mood",
                               "Background": "resources/backgrounds/bg1920x1080px_darkGreen.jpg",
                               "PlayState": "Playing",
                               "Display": beamSettings._DefaultDisplaySettings})

        # Build the panel
        self.panel = wx.Panel(self)
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.hbox = wx.BoxSizer(wx.HORIZONTAL)

        # Save/Close-buttons
        self.button_ok = wx.Button(self.panel, label="Save")
        self.button_cancel = wx.Button(self.panel, label="Close")
        self.button_ok.Bind(wx.EVT_BUTTON, self.onSave)
        self.button_cancel.Bind(wx.EVT_BUTTON, self.onClose)
        self.hbox.Add((200, -1), 1, flag=wx.EXPAND | wx.ALIGN_RIGHT)
        self.hbox.Add(self.button_ok, flag=wx.LEFT | wx.BOTTOM | wx.TOP, border=10)
        self.hbox.Add(self.button_cancel, flag=wx.LEFT | wx.BOTTOM | wx.TOP | wx.RIGHT, border=10)
        
        # Description Settings
        PropertiesText = wx.StaticText(self.panel, -1, "Properties")
        font = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        PropertiesText.SetFont(font)
        self.vbox.Add(PropertiesText, flag=wx.LEFT | wx.TOP | wx.BOTTOM, border=10)
        
        # Add settings
        self.vbox.Add(self.MoodSettings(), flag=wx.LEFT, border=20)

        # Description Layout and background
        LayoutText = wx.StaticText(self.panel, -1, "Layout")
        font = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        LayoutText.SetFont(font)
        
        BackgroundText = wx.StaticText(self.panel, -1, "Select background image (1920x1080 recommended)")
        self.MoodBackground = wx.Button(self.panel, label="Browse")
        descriptionSizer = wx.BoxSizer(wx.VERTICAL)
        descriptionSizer.Add(LayoutText, flag= wx.BOTTOM | wx.TOP, border=10)
        descriptionSizer.Add(BackgroundText, flag=wx.LEFT, border=10)
        descriptionSizer.Add(self.MoodBackground, flag=wx.LEFT | wx.TOP, border=10)
        self.vbox.Add(descriptionSizer, flag=wx.LEFT | wx.BOTTOM | wx.TOP, border=10)

        # Add Layout
        self.LayoutSettings()
        self.vbox.Add(self.LayoutList, 1, flag=wx.EXPAND | wx.LEFT | wx.TOP | wx.RIGHT, border=10)
        self.vbox.Add(self.sizerbuttons, flag=wx.LEFT | wx.BOTTOM , border=10)

        # Set sizers
        self.vbox.Add(self.hbox)
        self.panel.SetSizer(self.vbox)
    
    
#
# MOOD MAIN SETTINGS
#
    def MoodSettings(self):

        # Create the fields
        
        self.InputID3Field = wx.ComboBox(self.panel, size=(120,-1), value=self.Settings[u'Field1'], choices=self.Fields, style=wx.CB_READONLY)
        self.IsIsNot       = wx.ComboBox(self.panel,value=self.Settings[u'Field2'], choices=["is", "is not", "contains"], style=wx.CB_READONLY)
        self.MoodOrder     = wx.TextCtrl(self.panel, value=str(self.RowSelected+1))
        self.OutputField   = wx.TextCtrl(self.panel, value=self.Settings[u'Field3'], size=(120,-1))
        self.MoodNameField = wx.TextCtrl(self.panel, value=self.Settings[u'Name'], size=(120,-1))
        self.MoodState     = wx.ComboBox(self.panel,value=self.Settings[u'PlayState'], choices=["Playing", "Not Playing"], size=(120,-1), style=wx.CB_READONLY)

        InfoGrid    =   wx.FlexGridSizer(6, 3, 5, 5)
        InfoGrid.AddMany ( [(wx.StaticText(self.panel, label="Name"), 0, wx.EXPAND),
                        (wx.StaticText(self.panel, label="Mood state"), 0, wx.EXPAND),
                        (wx.StaticText(self.panel, label="Mood order"), 0, wx.EXPAND),
                        (self.MoodNameField, 0, wx.EXPAND),
                        (self.MoodState, 0, wx.EXPAND),
                        (self.MoodOrder, 0, wx.EXPAND),
                        (wx.StaticText(self.panel, label="Input field"), 0, wx.EXPAND),
                        (wx.StaticText(self.panel, label=""), 0, wx.EXPAND),
                        (wx.StaticText(self.panel, label="Output field"), 0, wx.EXPAND),
                        (self.InputID3Field, 0, wx.EXPAND),
                        (self.IsIsNot, 0, wx.EXPAND),
                        (self.OutputField, 0, wx.EXPAND)
                        ])
        
        return InfoGrid

#
# MOOD LAYOUT LIST
#
    def LayoutSettings(self):

        self.DisplayRows = []

        self.AddLayout  = wx.Button(self.panel, label="Add")
        self.DelLayout  = wx.Button(self.panel, label="Delete")
        self.EditLayout = wx.Button(self.panel, label="Edit")

        self.sizerbuttons    = wx.BoxSizer(wx.HORIZONTAL)
        self.sizerbuttons.Add(self.AddLayout, flag=wx.RIGHT | wx.TOP, border=10)
        self.sizerbuttons.Add(self.DelLayout, flag=wx.RIGHT | wx.TOP, border=10)
        self.sizerbuttons.Add(self.EditLayout, flag=wx.RIGHT | wx.TOP, border=10)

        self.LayoutList = wx.CheckListBox(self.panel,-1, size=wx.DefaultSize, choices=[], style= wx.LB_NEEDED_SB)
        self.LayoutList.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.LayoutList.Bind(wx.EVT_LISTBOX_DCLICK, self.OnEditLayout)
        self.LayoutList.Bind(wx.EVT_CHECKLISTBOX, self.OnCheckLayout)

        # Load data into table
        self.BuildLayoutList()

        self.AddLayout.Bind(wx.EVT_BUTTON, self.OnAddLayout)
        self.EditLayout.Bind(wx.EVT_BUTTON, self.OnEditLayout)
        self.DelLayout.Bind(wx.EVT_BUTTON, self.OnDelLayout)
        self.MoodBackground.Bind(wx.EVT_BUTTON, self.BrowseMoodBackground)

        return

#
# BUILD LIST AND CHECK
#
    def BuildLayoutList(self):
        self.DisplayRows = []
        MoodLayout = self.Settings[u'Display']
        for i in range(0, len(MoodLayout)):
            Settings = MoodLayout[i]
            self.DisplayRows.append(Settings[u'Field'])
        self.LayoutList.Set(self.DisplayRows)
        for i in range(0, len(MoodLayout)):
            Settings = MoodLayout[i]
            if Settings['Active'] == "yes":
                self.LayoutList.Check(i, check=True)
            else:
                self.LayoutList.Check(i, check=False)

    def OnCheckLayout(self, event):
        MoodLayout = self.Settings[u'Display']
        for i in range(0, len(MoodLayout)):
            layout = MoodLayout[i]
            if self.LayoutList.IsChecked(i):
                layout[u'Active'] = "yes"
            else:
                layout[u'Active'] = "no"
        self.BuildLayoutList()

#
# LAYOUT BUTTONS
#
    def OnAddLayout(self, event):
        self.EditLayout = EditLayoutDialog(self, len(self.DisplayRows), "Add layout item", self.Settings[u'Display'])
        self.EditLayout.Show()

    def OnEditLayout(self, event):
        RowSelected = self.LayoutList.GetSelection()
        if RowSelected>-1:
            self.EditLayout = EditLayoutDialog(self, RowSelected, "Edit layout item", self.Settings[u'Display'])
            self.EditLayout.Show()

    def OnDelLayout(self, event):
        RowSelected = self.LayoutList.GetSelection()
        if RowSelected>-1:
            LineToDelete = self.LayoutList.GetString(RowSelected)
            dlg = wx.MessageDialog(self,
            "Do you really want to delete '"+LineToDelete+"' ?",
            "Confirm deletion", wx.OK|wx.CANCEL|wx.ICON_QUESTION)
            result = dlg.ShowModal()
            dlg.Destroy()
            if result == wx.ID_OK:
                self.Settings[u'Display'].pop(RowSelected)
                self.BuildLayoutList()

#
# Save mood layout
#
    def onSave(self, e):
        # Get Settings
        self.Settings[u'Name'] = self.MoodNameField.GetValue()
        self.Settings[u'PlayState'] = self.MoodState.GetValue()
        self.Settings[u'Field1'] = self.InputID3Field.GetValue()
        self.Settings[u'Field2'] = self.IsIsNot.GetValue()
        self.Settings[u'Field3'] = self.OutputField.GetValue()
        MoodOrderBox = int(self.MoodOrder.GetValue())-1
        # Place settings in moods
        if self.mode == "Add mood":
            if MoodOrderBox < self.RowSelected:
                beamSettings._moods.insert(MoodOrderBox, self.Settings) #Insert in at position
            else:
                beamSettings._moods.append(self.Settings) # Append in the end
        else: #Edit mood
            if MoodOrderBox == self.RowSelected:
                beamSettings._moods[MoodOrderBox] = self.Settings # Overwrite
            else:
                beamSettings._moods.pop(self.RowSelected) #Move up and down in list
                beamSettings._moods.insert(MoodOrderBox, self.Settings)
        self.MainWindowParent.BuildMoodList()
        self.Destroy()

#
# Cancel mood layout
#
    def onClose(self, e):
        self.Destroy()

    def BrowseMoodBackground(self, event):
        openFileDialog = wx.FileDialog(self, "Set new background image for mood",
                                       os.path.join(os.getcwd(), 'resources', 'backgrounds'), "",
                                       "Image files(*.png,*.jpg)|*.png;*.jpg",
                                       wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        if openFileDialog.ShowModal() == wx.ID_OK:
            print self.Settings[u'Background']
            self.Settings[u'Background'] = openFileDialog.GetPath()
            print self.Settings[u'Background']
            openFileDialog.Destroy()
