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
import os

from bin.beamsettings import *
from bin.dialogs.editmooddialog import EditMood

#
# Build main preferences Window
#

class Moods(wx.Dialog):
    def __init__(self, parent):
        self.MainWindowParent = parent
        wx.Dialog.__init__(self, parent, title="Moods", size=(400,400))

        # Build the panel
        self.panel = wx.Panel(self)
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.hbox = wx.BoxSizer(wx.HORIZONTAL)
        
        # Save/Cancel buttons
        self.button_ok = wx.Button(self.panel, label="Apply")
        self.button_cancel = wx.Button(self.panel, label="Close")
        self.button_ok.Bind(wx.EVT_BUTTON, self.onApply)
        self.button_cancel.Bind(wx.EVT_BUTTON, self.onClose)

        self.MoodRows = []

        # Mood buttons
        self.AddMood    = wx.Button(self.panel, label="Add")
        self.DelMood    = wx.Button(self.panel, label="Delete")
        self.EditMood   = wx.Button(self.panel, label="Edit")
        sizerbuttons    = wx.BoxSizer(wx.HORIZONTAL)
        sizerbuttons.Add(self.AddMood, flag=wx.RIGHT | wx.TOP, border=10)
        sizerbuttons.Add(self.DelMood, flag=wx.RIGHT | wx.TOP, border=10)
        sizerbuttons.Add(self.EditMood, flag=wx.RIGHT | wx.TOP, border=10)

        self.AddMood.Bind(wx.EVT_BUTTON, self.OnAddMood)
        self.EditMood.Bind(wx.EVT_BUTTON, self.OnEditMood)
        self.DelMood.Bind(wx.EVT_BUTTON, self.OnDelMood)

        self.MoodList = wx.CheckListBox(self.panel,-1, size=wx.DefaultSize, choices=self.MoodRows, style= wx.LB_NEEDED_SB)
        self.MoodList.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.MoodList.Bind(wx.EVT_LISTBOX_DCLICK, self.OnEditMood)
        self.MoodList.Bind(wx.EVT_CHECKLISTBOX, self.OnCheckMood)

        self.vbox.Add(self.MoodList, 1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        self.vbox.Add(sizerbuttons, flag=wx.LEFT | wx.BOTTOM | wx.TOP, border=10)

        self.hbox.Add((200, -1), 1, flag=wx.EXPAND | wx.ALIGN_RIGHT)
        self.hbox.Add(self.button_ok, flag=wx.LEFT | wx.BOTTOM | wx.TOP, border=10)
        self.hbox.Add(self.button_cancel, flag=wx.LEFT | wx.BOTTOM | wx.TOP | wx.RIGHT, border=10)
        self.vbox.Add(self.hbox)

        #self.panel.SetSizerAndFit(self.vbox) #Makes my screen flicker
        self.panel.SetSizer(self.vbox)
        
        # Load data in table
        self.BuildMoodList()

#
# BUILD LIST
#
    def BuildMoodList(self):
        self.MoodRows = []
        for i in range(0, len(beamSettings._moods)):
            mood = beamSettings._moods[i]
            if mood[u'Type'] == "Mood":
                self.MoodRows.append(str(mood[u'Name']))
        self.MoodList.Set(self.MoodRows)
        # Check the rules
        for i in range(0, len(beamSettings._moods)):
            moods = beamSettings._moods[i]
            if moods[u'Active'] == "yes":
                self.MoodList.Check(i, check=True)
            else:
                self.MoodList.Check(i, check=False)

#
# CHECK BOXES
#
    def OnCheckMood(self, event):
        for i in range(0, len(beamSettings._moods)):
            mood = beamSettings._moods[i]
            if self.MoodList.IsChecked(i):
                mood[u'Active'] = "yes"
            else:
                mood[u'Active'] = "no"
        self.BuildMoodList()
#
# Apply preferences
#
    def onApply(self, e):
        # Get Settings
        beamSettings.SaveConfig(beamSettings.defaultConfigFileName)

#
# Cancel preferences
#
    def onClose(self, e):
        self.Destroy()

#
# MOODS BUTTONS
#
    def OnAddMood(self, event):
        self.EditMood = EditMood(self, self.MoodList.GetCount(), "Add mood")
        self.EditMood.Show()

    def OnEditMood(self, event):
        RowSelected = self.MoodList.GetSelection()
        if RowSelected>-1:
            self.MoodRule = EditMood(self, RowSelected, "Edit mood")
            self.MoodRule.Show()

    def OnDelMood(self, event):
        RowSelected = self.MoodList.GetSelection()
        if RowSelected>-1:
            LineToDelete = self.MoodList.GetString(RowSelected)
            dlg = wx.MessageDialog(self,
            "Do you really want to delete '"+LineToDelete+"' ?",
            "Confirm deletion", wx.OK|wx.CANCEL|wx.ICON_QUESTION)
            result = dlg.ShowModal()
            dlg.Destroy()
            if result == wx.ID_OK:
                beamSettings._moods.pop(RowSelected)
            self.BuildMoodList()


