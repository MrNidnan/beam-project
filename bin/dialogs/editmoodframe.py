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
from bin.dialogs.editlayoutitemdialog import EditLayoutItemDialog

from copy import deepcopy


#
# Mood layout edit window
#

class EditMoodFrame(wx.Frame):
    def __init__(self, moodsPanel, RowSelected, mode):

        # MoodsPanel
        self.moodsPanel = moodsPanel

        wx.Frame.__init__(self, moodsPanel, title=mode, pos=(self.moodsPanel.GetScreenPosition() + (50, 50)),
                          size=self.moodsPanel.BeamSettings._moodSize,
                          style=wx.DEFAULT_FRAME_STYLE & ~ (wx.RESIZE_BORDER | wx.MAXIMIZE_BOX))
        self.RowSelected = RowSelected
        self.mode = mode
        self.EditMood = {}

        # Define choices
        self.Fields = ["%Artist", "%Album", "%Title", "%Genre", "%Comment", "%Composer", "%Year", "%AlbumArtist",
                       "%Performer", "%Singer", "%IsCortina"]
        # Get item
        if self.RowSelected < len(beamSettings._moods):
            # Get the properties of the selected item
            self.EditMood = beamSettings._moods[self.RowSelected]
        else:
            # Create a new default setting
            DefaultDisplay = deepcopy(beamSettings._moods[0]['Display'])
            self.EditMood = ({"Active": "yes", "Field3": "something", "Field2": "contains", "Field1": "%Title",
                              "Type": "Mood", "Name": "My Mood", "RotateBackground": "no", "RotateTimer": 30,
                              "Background": "resources/backgrounds/bg1920x1080px_darkGreen.jpg",
                              "PlayState": "Playing",
                              "Display": DefaultDisplay})

        # Build the panel
        self.panel = wx.Panel(self)
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.hbox = wx.BoxSizer(wx.HORIZONTAL)
        font = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD)

        # Save/Cancel-buttons
        self.button_ok = wx.Button(self.panel, label="OK")
        # self.button_cancel = wx.Button(self.panel, label="Cancel")
        self.button_ok.Bind(wx.EVT_BUTTON, self.onSave)
        # self.button_cancel.Bind(wx.EVT_BUTTON, self.onCancel)
        self.hbox.Add(self.button_ok, flag=wx.LEFT | wx.BOTTOM | wx.TOP, border=10)
        # self.hbox.Add(self.button_cancel, flag=wx.LEFT | wx.BOTTOM | wx.TOP | wx.RIGHT, border=10)

        # Description Settings
        PropertiesText = wx.StaticText(self.panel, -1, "Properties")
        PropertiesText.SetFont(font)
        self.vbox.Add(PropertiesText, flag=wx.LEFT | wx.TOP | wx.BOTTOM, border=10)

        # Add settings
        self.vbox.Add(self.MoodSettings(), flag=wx.LEFT, border=20)

        # Description Layout and background
        BackgroundText = wx.StaticText(self.panel, -1, "Background")
        BackgroundText.SetFont(font)

        BackgroundDesc = wx.StaticText(self.panel, -1, "Select background image (1920x1080 recommended)")
        self.MoodBackground = wx.Button(self.panel, label="Browse")
        self.currentBackground = wx.StaticText(self.panel, -1, "")

        self.ChangeBackgroundBox = wx.CheckBox(self.panel, label='Change Background: ')
        self.BackgroundTimerBox = wx.ComboBox(self.panel,
                                              choices=['Every 15 seconds', 'Every 30 seconds', 'Every 1 minute',
                                                       'Every 2 minutes', 'Every 3 minutes', 'Every 5 minutes',
                                                       'Every 10 minutes', 'Every 20 minutes'], style=wx.CB_READONLY)
        self.RandomBackgroundBox = wx.CheckBox(self.panel, label='Random order')
        self.ChangeBackgroundBox.Bind(wx.EVT_CHECKBOX, self.OnRotateBackground)
        self.RandomBackgroundBox.Bind(wx.EVT_CHECKBOX, self.OnRotateBackground)
        self.BackgroundTimerBox.Bind(wx.EVT_COMBOBOX, self.OnRotateBackground)
        if self.EditMood['RotateBackground'] == "linear":
            self.ChangeBackgroundBox.SetValue(True)
            self.RandomBackgroundBox.SetValue(False)
        elif self.EditMood['RotateBackground'] == "random":
            self.ChangeBackgroundBox.SetValue(True)
            self.RandomBackgroundBox.SetValue(True)
        else:
            self.ChangeBackgroundBox.SetValue(False)
            self.RandomBackgroundBox.SetValue(False)
            self.RandomBackgroundBox.Disable()
            self.BackgroundTimerBox.Disable()
        self.rotateBackgroundFunction()
        BackgroundSizer = wx.BoxSizer(wx.HORIZONTAL)
        RandomSizer = wx.BoxSizer(wx.HORIZONTAL)
        BackgroundSizer.Add(self.MoodBackground, flag=wx.RIGHT, border=10)
        BackgroundSizer.Add(self.currentBackground)
        RandomSizer.Add(self.ChangeBackgroundBox, flag=wx.RIGHT, border=10)
        RandomSizer.Add(self.BackgroundTimerBox)

        descriptionSizer = wx.BoxSizer(wx.VERTICAL)
        descriptionSizer.Add(BackgroundText, flag=wx.BOTTOM, border=10)
        descriptionSizer.Add(BackgroundDesc, flag=wx.LEFT, border=10)
        descriptionSizer.Add(BackgroundSizer, flag=wx.LEFT | wx.TOP, border=10)
        descriptionSizer.Add(RandomSizer, flag=wx.LEFT | wx.TOP, border=10)
        descriptionSizer.Add(self.RandomBackgroundBox, flag=wx.LEFT, border=10)
        self.vbox.Add(descriptionSizer, flag=wx.LEFT | wx.BOTTOM | wx.TOP, border=10)

        # Add Layout
        LayoutText = wx.StaticText(self.panel, -1, "Layout")
        LayoutText.SetFont(font)
        self.LayoutSettings()
        self.vbox.Add(LayoutText, flag=wx.LEFT | wx.BOTTOM, border=10)
        self.vbox.Add(self.LayoutList, 1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)
        self.vbox.Add(self.sizerbuttons, flag=wx.LEFT | wx.BOTTOM, border=10)

        # Set sizers
        self.vbox.Add(self.hbox, flag=wx.ALIGN_RIGHT)
        self.panel.SetSizer(self.vbox)

    #
    # MOOD MAIN SETTINGS
    #
    def MoodSettings(self):

        # Create the fields

        self.MoodNameField = wx.TextCtrl(self.panel, value=self.EditMood['Name'], size=(120, -1))
        self.MoodStateField = wx.ComboBox(self.panel, value=self.EditMood['PlayState'], choices=["Playing", "Not Playing"],
                                          size=(120, -1), style=wx.CB_READONLY)
        self.MoodOrderField = wx.SpinCtrl(self.panel, value=str(self.RowSelected), min=0, max=99)
        self.InputID3Field = wx.ComboBox(self.panel, size=(120, -1), value=self.EditMood['Field1'],
                                         choices=self.Fields, style=wx.CB_READONLY)
        self.IsIsNotField = wx.ComboBox(self.panel, value=self.EditMood['Field2'], choices=["is", "is not", "contains"],
                                        style=wx.CB_READONLY)
        self.OutputField = wx.TextCtrl(self.panel, value=self.EditMood['Field3'], size=(120, -1))

        moodname = self.EditMood['Name']
        if moodname == 'Default':
            # Default has to keep name 'Default'
            self.MoodNameField.Disable()
            self.MoodStateField.Disable()
            # Default has to keep 0
            self.MoodOrderField.Disable()
            self.InputID3Field.Disable()
            self.IsIsNotField.Disable()
            self.OutputField.Disable()

        InfoGrid = wx.FlexGridSizer(6, 3, 5, 5)
        InfoGrid.AddMany([(wx.StaticText(self.panel, label="Name"), 0, wx.EXPAND),
                          (wx.StaticText(self.panel, label="Mood state"), 0, wx.EXPAND),
                          (wx.StaticText(self.panel, label="Mood order"), 0, wx.EXPAND),
                          (self.MoodNameField, 0, wx.EXPAND),
                          (self.MoodStateField, 0, wx.EXPAND),
                          (self.MoodOrderField, 0, wx.EXPAND),
                          (wx.StaticText(self.panel, label="Input field"), 0, wx.EXPAND),
                          (wx.StaticText(self.panel, label=""), 0, wx.EXPAND),
                          (wx.StaticText(self.panel, label="Output field"), 0, wx.EXPAND),
                          (self.InputID3Field, 0, wx.EXPAND),
                          (self.IsIsNotField, 0, wx.EXPAND),
                          (self.OutputField, 0, wx.EXPAND)
                          ])

        return InfoGrid

    #
    # MOOD LAYOUT LIST
    #
    def LayoutSettings(self):

        self.DisplayRows = []

        self.AddLayout = wx.Button(self.panel, label="Add")
        self.DelLayout = wx.Button(self.panel, label="Delete")
        self.EditLayout = wx.Button(self.panel, label="Edit")

        self.sizerbuttons = wx.BoxSizer(wx.HORIZONTAL)
        self.sizerbuttons.Add(self.AddLayout, flag=wx.RIGHT | wx.TOP, border=10)
        self.sizerbuttons.Add(self.DelLayout, flag=wx.RIGHT | wx.TOP, border=10)
        self.sizerbuttons.Add(self.EditLayout, flag=wx.RIGHT | wx.TOP, border=10)

        self.LayoutList = wx.CheckListBox(self.panel, -1, size=wx.DefaultSize, choices=[], style=wx.LB_NEEDED_SB)
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
        MoodLayout = self.EditMood['Display']
        for i in range(0, len(MoodLayout)):
            Settings = MoodLayout[i]
            self.DisplayRows.append(Settings['Field'])
        self.LayoutList.Set(self.DisplayRows)
        for i in range(0, len(MoodLayout)):
            Settings = MoodLayout[i]
            if Settings['Active'] == "yes":
                self.LayoutList.Check(i, check=True)
            else:
                self.LayoutList.Check(i, check=False)

    def OnCheckLayout(self, event):
        MoodLayout = self.EditMood['Display']
        for i in range(0, len(MoodLayout)):
            layout = MoodLayout[i]
            if self.LayoutList.IsChecked(i):
                layout['Active'] = "yes"
            else:
                layout['Active'] = "no"
        self.BuildLayoutList()

    #
    # ROTATE/RANDOM BACKGROUND
    #
    def OnRotateBackground(self, event):
        if self.ChangeBackgroundBox.IsChecked() and not self.RandomBackgroundBox.IsChecked():
            self.EditMood['RotateBackground'] = "linear"
            self.RandomBackgroundBox.Enable()
            self.BackgroundTimerBox.Enable()
        elif self.ChangeBackgroundBox.IsChecked() and self.RandomBackgroundBox.IsChecked():
            self.EditMood['RotateBackground'] = "random"
            self.RandomBackgroundBox.Enable()
            self.BackgroundTimerBox.Enable()
        else:
            self.EditMood['RotateBackground'] = "no"
            self.RandomBackgroundBox.Disable()
            self.BackgroundTimerBox.Disable()
        timerVector = [15, 30, 60, 120, 180, 300, 600, 1200]
        self.EditMood['RotateTimer'] = timerVector[int(self.BackgroundTimerBox.GetSelection())]
        self.rotateBackgroundFunction()

    def rotateBackgroundFunction(self):
        if int(self.EditMood['RotateTimer']) == 15:
            self.BackgroundTimerBox.SetSelection(0)
        elif int(self.EditMood['RotateTimer']) == 30:
            self.BackgroundTimerBox.SetSelection(1)
        elif int(self.EditMood['RotateTimer']) == 60:
            self.BackgroundTimerBox.SetSelection(2)
        elif int(self.EditMood['RotateTimer']) == 120:
            self.BackgroundTimerBox.SetSelection(3)
        elif int(self.EditMood['RotateTimer']) == 180:
            self.BackgroundTimerBox.SetSelection(4)
        elif int(self.EditMood['RotateTimer']) == 300:
            self.BackgroundTimerBox.SetSelection(5)
        elif int(self.EditMood['RotateTimer']) == 600:
            self.BackgroundTimerBox.SetSelection(6)
        elif int(self.EditMood['RotateTimer']) == 1200:
            self.BackgroundTimerBox.SetSelection(7)
        else:
            self.BackgroundTimerBox.SetSelection(2)

        (path, backgroundfile) = os.path.split(self.EditMood['Background'])
        if self.EditMood['RotateBackground'] == "no":
            self.currentBackground.SetLabel("Image: " + backgroundfile)
        else:
            self.currentBackground.SetLabel("Images from folder: " + os.path.split(path)[1])

    #
    # LAYOUT BUTTONS
    #
    def OnAddLayout(self, event):
        self.EditLayout = EditLayoutItemDialog(self, len(self.DisplayRows), "Add layout item", self.EditMood['Display'])
        self.EditLayout.Show()

    def OnEditLayout(self, event):
        RowSelected = self.LayoutList.GetSelection()
        if RowSelected > -1:
            self.EditLayout = EditLayoutItemDialog(self, RowSelected, "Edit layout item", self.EditMood['Display'])
            self.EditLayout.Show()

    def OnDelLayout(self, event):
        RowSelected = self.LayoutList.GetSelection()
        if RowSelected >= 0:
            LineToDelete = self.LayoutList.GetString(RowSelected)
            dlg = wx.MessageDialog(self,
                                   "Do you really want to delete '" + LineToDelete + "' ?",
                                   "Confirm deletion", wx.OK | wx.CANCEL | wx.ICON_QUESTION)
            result = dlg.ShowModal()
            dlg.Destroy()
            if result == wx.ID_OK:
                self.EditMood['Display'].pop(RowSelected)
                self.BuildLayoutList()

    #
    # Save mood layout
    #
    def onSave(self, e):
        # Get Settings
        self.EditMood['Name'] = self.MoodNameField.GetValue()
        self.EditMood['PlayState'] = self.MoodStateField.GetValue()
        self.EditMood['Field1'] = self.InputID3Field.GetValue()
        self.EditMood['Field2'] = self.IsIsNotField.GetValue()
        self.EditMood['Field3'] = self.OutputField.GetValue()
        moodorder = int(self.MoodOrderField.GetValue())
        # Place settings in moods
        if self.mode == "Add mood":
            if moodorder < self.RowSelected:
                beamSettings._moods.insert(moodorder, self.EditMood)  # Insert in at position
            else:
                beamSettings._moods.append(self.EditMood)  # Append in the end
        else:  # Edit mood
            if moodorder == self.RowSelected:
                beamSettings._moods[moodorder] = self.EditMood  # Overwrite
            else:
                beamSettings._moods.pop(self.RowSelected)  # Move up and down in list
                beamSettings._moods.insert(moodorder, self.EditMood)

        self.moodsPanel.BuildMoodList()
        self.moodsPanel.updateSettings()
        self.Destroy()

    #
    # Cancel mood layout
    #
    # def onCancel(self, e):
    #    self.Destroy()

    #
    # Browse for background
    #
    def BrowseMoodBackground(self, event):
        backgroundPath = self.EditMood['Background']
        openFileDialog = wx.FileDialog(self, "Set new background image for mood",
                                       # os.path.join(os.getcwd(), 'resources', 'backgrounds'),
                                       backgroundPath,
                                       "",
                                       "Image files(*.png,*.jpg)|*.png;*.jpg",
                                       wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        if openFileDialog.ShowModal() == wx.ID_OK:
            backgroundPath = openFileDialog.GetPath()
            # !!! Sanitize for temporary home of execcutable
            relativePath = getRelativePath(backgroundPath)
            self.EditMood['Background'] = relativePath
            (path, backgroundfile) = os.path.split(self.EditMood['Background'])
            self.rotateBackgroundFunction()
            openFileDialog.Destroy()
