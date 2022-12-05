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

class EditMoodDialog(wx.Dialog):
    def __init__(self, moodsPanel, RowSelected, mode):
        xpos,ypos = moodsPanel.GetScreenPosition()
        wx.Dialog.__init__(self, moodsPanel, title=mode, pos=(xpos + 50, ypos + 50), size=moodsPanel.BeamSettings._moodSize, style=wx.RESIZE_BORDER)
#        wx.Frame.__init__(self, moodsPanel, title=mode, pos=(xpos + 50, ypos + 50),
#                          size=self.moodsPanel.BeamSettings._moodSize,
#                          style=wx.DEFAULT_FRAME_STYLE & ~ (wx.RESIZE_BORDER | wx.MAXIMIZE_BOX))

        # MoodsPanel
        self.moodsPanel = moodsPanel
        self.RowSelected = RowSelected
        self.mode = mode
        self.EditMood = {}

        # Define choices
        self.Fields = ["%Artist", "%Album", "%Title", "%Genre", "%Comment", "%Composer", "%Year", "%AlbumArtist",
                       "%Performer", "%Singer", "%IsCortina"]

        # Create a new default setting
        '''
        defLayoutItems = deepcopy(beamSettings._moods[0]['Display']) # LayoutItems[]
        defaultMood = ({
                        "Name": "My Mood",
                        "Type": "Mood",
                        "Active": "yes",
                        "Field1": "%Title",
                        "Field2": "contains",
                        "Field3": "something",
                        "Background": "resources/backgrounds/bg1920x1080px_darkGreen.jpg",
                        "RotateBackground": "no",
                        "RotateTimer": 30,
                        "DisplayTimer": 0,
                        "PlayState": "Playing",
                        "Display": defLayoutItems
                      })
        '''

        # Get item
        if self.RowSelected < len(beamSettings.getMoods()):
            # Get the properties of the selected item
            # DefaultDisplay is a list and does not get erged
            self.EditMood = beamSettings.getMoods()[self.RowSelected]
        else:
            self.EditMood = deepcopy(beamSettings.getMoods()[0])
            self.EditMood["Name"] = "New Mood"

        # Build the panel
        self.panel = wx.Panel(self)
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.hbox = wx.BoxSizer(wx.HORIZONTAL)
        font = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD)

        # Save/Cancel-buttons
        self.OkButton = wx.Button(self.panel, label="OK")
        # self.button_cancel = wx.Button(self.panel, label="Cancel")
        self.OkButton.Bind(wx.EVT_BUTTON, self.OnOk)
        # self.button_cancel.Bind(wx.EVT_BUTTON, self.onCancel)
        self.hbox.Add(self.OkButton, flag=wx.LEFT | wx.BOTTOM | wx.TOP, border=10)
        # self.hbox.Add(self.button_cancel, flag=wx.LEFT | wx.BOTTOM | wx.TOP | wx.RIGHT, border=10)

        # Description Settings
        PropertiesText = wx.StaticText(self.panel, -1, "Properties")
        PropertiesText.SetFont(font)
        self.vbox.Add(PropertiesText, flag=wx.LEFT | wx.TOP | wx.BOTTOM, border=10)

        # Add settings
        propertiesGrid = self.CreatePropertiesGrid()
        self.vbox.Add(propertiesGrid, flag=wx.LEFT, border=20)

        # Background
        BackgroundText = wx.StaticText(self.panel, -1, "Background")
        BackgroundText.SetFont(font)

        BackgroundDesc = wx.StaticText(self.panel, -1, "Select background image (1920x1080 recommended)")
        self.BrowseBackgroundButton = wx.Button(self.panel, label="Browse")
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
        BackgroundSizer.Add(self.BrowseBackgroundButton, flag=wx.RIGHT, border=10)
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

        # Layout
        self.LayoutSettings()
        layoutText = wx.StaticText(self.panel, -1, "Layout")
        layoutText.SetFont(font)
        self.vbox.Add(layoutText, flag=wx.LEFT | wx.BOTTOM, border=10)

        displayTimerText = wx.StaticText(self.panel, -1, "Display Timer")
        self.vbox.Add(displayTimerText, flag=wx.LEFT | wx.BOTTOM, border=10)
        self.vbox.Add(self.DisplayTimerField, flag=wx.LEFT | wx.BOTTOM, border=10)

        self.vbox.Add(self.LayoutList, 1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)
        self.vbox.Add(self.sizerbuttons, flag=wx.LEFT | wx.BOTTOM, border=10)

        # Set sizers
        self.vbox.Add(self.hbox, flag=wx.ALIGN_RIGHT)
        self.panel.SetSizer(self.vbox)

    #
    # Crates fields and sets values
    #
    def CreatePropertiesGrid(self):

        # Create the fields

        self.MoodNameField = wx.TextCtrl(self.panel, value=self.EditMood['Name'], size=(120, -1))
        self.MoodStateField = wx.ComboBox(self.panel, value=self.EditMood['PlayState'], choices=["Playing", "Not Playing"],
                                          size=(120, -1), style=wx.CB_READONLY)
        # min > 0 not to push away the default mood
        self.MoodOrderField = wx.SpinCtrl(self.panel, value=str(self.RowSelected), min=1, max=99)
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

        propertiesGrid = wx.FlexGridSizer(6, 3, 5, 5)
        propertiesGrid.AddMany([(wx.StaticText(self.panel, label="Name"), 0, wx.EXPAND),
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

        return propertiesGrid

    #
    # MOOD LAYOUT LIST
    #
    def LayoutSettings(self):

        self.DisplayRows = []

        self.AddLayoutItemButton = wx.Button(self.panel, label="Add")
        self.DelLayoutItemButton = wx.Button(self.panel, label="Delete")
        self.EditLayoutItemButton = wx.Button(self.panel, label="Edit")

        self.sizerbuttons = wx.BoxSizer(wx.HORIZONTAL)
        self.sizerbuttons.Add(self.AddLayoutItemButton, flag=wx.RIGHT | wx.TOP, border=10)
        self.sizerbuttons.Add(self.DelLayoutItemButton, flag=wx.RIGHT | wx.TOP, border=10)
        self.sizerbuttons.Add(self.EditLayoutItemButton, flag=wx.RIGHT | wx.TOP, border=10)

        displaytimer= int(self.EditMood['DisplayTimer'])
        self.DisplayTimerField = wx.SpinCtrl(self.panel, value=str(displaytimer), min=0)

        self.LayoutList = wx.CheckListBox(self.panel, -1, size=wx.DefaultSize, choices=[], style=wx.LB_NEEDED_SB)
        self.LayoutList.SetBackgroundColour(wx.Colour(128, 128, 128))
        self.LayoutList.Bind(wx.EVT_LISTBOX_DCLICK, self.OnEditLayoutItem)
        self.LayoutList.Bind(wx.EVT_CHECKLISTBOX, self.OnCheckLayout)

        # Load data into table
        self.BuildLayoutList()

        self.AddLayoutItemButton.Bind(wx.EVT_BUTTON, self.OnAddLayoutItem)
        self.EditLayoutItemButton.Bind(wx.EVT_BUTTON, self.OnEditLayoutItem)
        self.DelLayoutItemButton.Bind(wx.EVT_BUTTON, self.OnDelLayoutItem)
        self.BrowseBackgroundButton.Bind(wx.EVT_BUTTON, self.OnBrowseBackground)

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
    def OnAddLayoutItem(self, event):
        self.EditLayoutItemButton = EditLayoutItemDialog(self, len(self.DisplayRows), "Add layout item", self.EditMood['Display'])
        self.EditLayoutItemButton.Show()

    def OnEditLayoutItem(self, event):
        RowSelected = self.LayoutList.GetSelection()
        if RowSelected > -1:
            self.EditLayoutItemButton = EditLayoutItemDialog(self, RowSelected, "Edit layout item", self.EditMood['Display'])
            self.EditLayoutItemButton.Show()

    def OnDelLayoutItem(self, event):
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
    def OnOk(self, e):
        # Get Settings
        self.EditMood['Name'] = self.MoodNameField.GetValue()
        self.EditMood['PlayState'] = self.MoodStateField.GetValue()
        self.EditMood['Field1'] = self.InputID3Field.GetValue()
        self.EditMood['Field2'] = self.IsIsNotField.GetValue()
        self.EditMood['Field3'] = self.OutputField.GetValue()
        self.EditMood['DisplayTimer'] = self.DisplayTimerField.GetValue()

        moodorder = int(self.MoodOrderField.GetValue())
        if self.EditMood['Name'] == 'Default':
            # Got set to 1 as in of spin button
            moodorder = 0

        # Place settings in moods
        if self.mode == "Add mood":
            if moodorder < self.RowSelected:
                beamSettings.getMoods().insert(moodorder, self.EditMood)  # Insert in at position
            else:
                beamSettings.getMoods().append(self.EditMood)  # Append in the end
        else:  # Edit mood
            if moodorder == self.RowSelected:
                beamSettings.getMoods()[moodorder] = self.EditMood  # Overwrite
            else:
                beamSettings.getMoods().pop(self.RowSelected)  # Move up and down in list
                beamSettings.getMoods().insert(moodorder, self.EditMood)

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
    def OnBrowseBackground(self, event):
        backgroundPath = self.EditMood['Background']
        openFileDialog = wx.FileDialog(self, "Set new background image for mood",
                                       # os.path.join(os.getcwd(), 'resources', 'backgrounds'),
                                       backgroundPath,
                                       "",
                                       "Image files(*.png,*.jpg)|*.png;*.jpg",
                                       wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        if openFileDialog.ShowModal() == wx.ID_OK:
            backgroundPath = openFileDialog.GetPath()
            # Sanitize for temporary home of execcutable
            relativePath = getRelativePath(backgroundPath)
            self.EditMood['Background'] = relativePath
            (path, backgroundfile) = os.path.split(self.EditMood['Background'])
            self.rotateBackgroundFunction()
            openFileDialog.Destroy()
