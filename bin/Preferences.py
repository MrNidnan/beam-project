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
import wx.lib.flatnotebook as fnb
import os

from bin.beamsettings import *
from bin.dialogs.editlayoutdialog import EditLayoutDialog
from bin.dialogs.editruledialog import EditRuleDialog

#
# Build main preferences Window
#

class Preferences(wx.Dialog):
    def __init__(self, parent):
        self.MainWindowParent = parent
        wx.Dialog.__init__(self, parent, title="Preferences", size=(400,400))

        # Build the panel
        self.panel = wx.Panel(self)
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.hbox = wx.BoxSizer(wx.HORIZONTAL)
        notebook  = fnb.FlatNotebook(self.panel, wx.ID_ANY,agwStyle=fnb.FNB_NODRAG|fnb.FNB_VC8|fnb.FNB_NO_NAV_BUTTONS|fnb.FNB_NO_X_BUTTON|fnb.FNB_NO_TAB_FOCUS)

        notebook.AddPage(self.BasicSettings(notebook), "Basic Settings")
        notebook.AddPage(self.LayoutSettings(notebook), "Layout")
        notebook.AddPage(self.RulesSettings(notebook), "Cortinas and Rules")

        self.button_ok = wx.Button(self.panel, label="Apply")
        self.button_cancel = wx.Button(self.panel, label="Close")
        self.button_ok.Bind(wx.EVT_BUTTON, self.onApply)
        self.button_cancel.Bind(wx.EVT_BUTTON, self.onClose)


        self.vbox.Add(notebook, 1, wx.ALL | wx.EXPAND)
        self.hbox.Add((200, -1), 1, flag=wx.EXPAND | wx.ALIGN_RIGHT)
        self.hbox.Add(self.button_ok, flag=wx.LEFT | wx.BOTTOM | wx.TOP, border=10)
        self.hbox.Add(self.button_cancel, flag=wx.LEFT | wx.BOTTOM | wx.TOP | wx.RIGHT, border=10)
        self.vbox.Add(self.hbox)

        self.panel.SetSizerAndFit(self.vbox)


#
# First tab - Basic Settings
#
    def BasicSettings(self, notebook):

        panel = wx.Panel(self)

        # Module dropdown
        Mediaplayer = wx.StaticText(panel, -1, "Mediaplayer", (10,7))
        font = wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        Mediaplayer.SetFont(font)
        wx.StaticText(panel, -1, "Select mediaplayer to display information from", (20,30))
        self.Dropdown = wx.ComboBox(panel,value=beamSettings._moduleSelected, choices=beamSettings._currentModules, pos=(20,50), style=wx.CB_READONLY)

        # Background image
        Background = wx.StaticText(panel, -1, "Background Image", (10,87))
        font = wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        Background.SetFont(font)
        wx.StaticText(panel, -1, "Select background image (1920x1080 recommended)", (20,110))
        self.browse = wx.Button(panel, label="Browse", pos=(20,129))
        self.browse.Bind(wx.EVT_BUTTON, self.browseBackgroundImage)

        # Wait timer
        waittimer = wx.StaticText(panel, -1, "Settings", (10,167))
        font = wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        waittimer.SetFont(font)
        wx.StaticText(panel, -1, "Update timer in mSec (default 4000)", (20,190))
        self.TimerText = wx.TextCtrl(panel, -1, str(beamSettings._updateTimer), (20,210), (140,-1))

        # Tanda Length
        wx.StaticText(panel, -1, "Next tanda preview (number of songs, default 4)", (20,243))
        self.TandaLength = wx.TextCtrl(panel, -1, str(beamSettings._maxTandaLength), (20,263), (140,-1))

        return panel


#
# Second tab - Display
#

    def LayoutSettings(self, notebook):

        panel = wx.Panel(self)
        self.DisplayRows = []

        self.AddLayout  = wx.Button(panel, label="Add")
        self.DelLayout  = wx.Button(panel, label="Delete")
        self.EditLayout = wx.Button(panel, label="Edit")
        sizerbuttons    = wx.BoxSizer(wx.HORIZONTAL)
        sizerbuttons.Add(self.AddLayout, flag=wx.RIGHT | wx.TOP, border=10)
        sizerbuttons.Add(self.DelLayout, flag=wx.RIGHT | wx.TOP, border=10)
        sizerbuttons.Add(self.EditLayout, flag=wx.RIGHT | wx.TOP, border=10)


        self.LayoutList = wx.CheckListBox(panel,-1, size=wx.DefaultSize, choices=[], style= wx.LB_NEEDED_SB)
        self.LayoutList.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.LayoutList.Bind(wx.EVT_LISTBOX_DCLICK, self.OnEditLayout)
        self.LayoutList.Bind(wx.EVT_CHECKLISTBOX, self.OnCheckLayout)

        # Load data into table
        self.BuildLayoutList()

        self.AddLayout.Bind(wx.EVT_BUTTON, self.OnAddLayout)
        self.EditLayout.Bind(wx.EVT_BUTTON, self.OnEditLayout)
        self.DelLayout.Bind(wx.EVT_BUTTON, self.OnDelLayout)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.LayoutList, proportion=1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        sizer.Add(sizerbuttons, flag=wx.LEFT | wx.BOTTOM | wx.TOP, border=10)
        panel.SetSizer(sizer)

        return panel
    

    def BuildLayoutList(self):
        self.DisplayRows = []
        for i in range(0, len(beamSettings._DefaultDisplaySettings)):
            Settings = beamSettings._DefaultDisplaySettings[i]
            self.DisplayRows.append(Settings[u'Field'])
        self.LayoutList.Set(self.DisplayRows)
        for i in range(0, len(beamSettings._DefaultDisplaySettings)):
            Settings = beamSettings._DefaultDisplaySettings[i]
            if Settings['Active'] == "yes":
                self.LayoutList.Check(i, check=True)
            else:
                self.LayoutList.Check(i, check=False)
#
# Third tab - Rules
#

    def RulesSettings(self, notebook):

        panel = wx.Panel(self)

        self.RuleRows = []

        # Add buttons
        self.AddRule    = wx.Button(panel, label="Add")
        self.DelRule    = wx.Button(panel, label="Delete")
        self.EditRule   = wx.Button(panel, label="Edit")
        sizerbuttons    = wx.BoxSizer(wx.HORIZONTAL)
        sizerbuttons.Add(self.AddRule, flag=wx.RIGHT | wx.TOP, border=10)
        sizerbuttons.Add(self.DelRule, flag=wx.RIGHT | wx.TOP, border=10)
        sizerbuttons.Add(self.EditRule, flag=wx.RIGHT | wx.TOP, border=10)

        self.AddRule.Bind(wx.EVT_BUTTON, self.OnAddRule)
        self.EditRule.Bind(wx.EVT_BUTTON, self.OnEditRule)
        self.DelRule.Bind(wx.EVT_BUTTON, self.OnDelRule)

        self.RuleList = wx.CheckListBox(panel,-1, size=wx.DefaultSize, choices=self.RuleRows, style= wx.LB_NEEDED_SB)
        self.RuleList.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.RuleList.Bind(wx.EVT_LISTBOX_DCLICK, self.OnEditRule)
        self.RuleList.Bind(wx.EVT_CHECKLISTBOX, self.OnCheckRule)

        # Load data into table
        self.BuildRuleList()

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.RuleList, proportion=1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        sizer.Add(sizerbuttons, flag=wx.LEFT | wx.BOTTOM | wx.TOP, border=10)
        panel.SetSizer(sizer)

        return panel


    def BuildRuleList(self):
        self.RuleRows = []
        for i in range(0, len(beamSettings._rules)):
            rule = beamSettings._rules[i]
            if rule[u'Type'] == "Copy":
                self.RuleRows.append(str('Copy '+rule[u'Field1']+' to '+rule[u'Field2']))
            if rule[u'Type'] == "Cortina":
                if rule[u'Field2'] =="is":
                    self.RuleRows.append(str("It's a Cortina when: "+rule[u'Field1']+' is '+rule[u'Field3']))
                if rule[u'Field2'] =="is not":
                    self.RuleRows.append(str("It's a Cortina when: "+rule[u'Field1']+' is not '+rule[u'Field3']))
                if rule[u'Field2'] =="contains":
                    self.RuleRows.append(str("It's a Cortina when: "+rule[u'Field1']+' contains '+rule[u'Field3']))
            if rule[u'Type'] == "Parse":
                self.RuleRows.append(str('Parse/split '+rule[u'Field1']+' containing '+rule[u'Field2']+' into '+rule[u'Field3']+' and '+rule[u'Field4']))
        self.RuleList.Set(self.RuleRows)
        # Check the rules
        for i in range(0, len(beamSettings._rules)):
            rule = beamSettings._rules[i]
            if rule[u'Active'] == "yes":
                self.RuleList.Check(i, check=True)
            else:
                self.RuleList.Check(i, check=False)
#
# Apply preferences
#
    def onApply(self, e):
        # Get Settings
        beamSettings._moduleSelected     = self.Dropdown.GetValue()
        beamSettings._updateTimer        = int(self.TimerText.GetValue())
        beamSettings._maxTandaLength     =  int(self.TandaLength.GetValue())
        beamSettings.SaveConfig(beamSettings.defaultConfigFileName)



#
# Cancel preferences
#
    def onClose(self, e):
        self.Destroy()

    def browseBackgroundImage(self, event):
        openFileDialog = wx.FileDialog(self, "Set new background image", 
                                       os.path.join(os.getcwd(), 'resources', 'backgrounds'), "",
                                       "Image files(*.png,*.jpg)|*.png;*.jpg",
                                       wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        if openFileDialog.ShowModal() == wx.ID_OK:
            beamSettings._DefaultBackground = openFileDialog.GetPath()
            # change current background
            self.MainWindowParent._currentBackgroundPath = beamSettings._DefaultBackground
            self.MainWindowParent.fadeBackground()
            openFileDialog.Destroy()



#
# LAYOUT BUTTONS
#
#
    def OnAddLayout(self, event):
        self.EditLayout = EditLayoutDialog(self, len(self.DisplayRows), "Add layout item", beamSettings._DefaultDisplaySettings)
        self.EditLayout.Show()

    def OnEditLayout(self, event):
        RowSelected = self.LayoutList.GetSelection()
        if RowSelected>-1:
            self.EditLayout = EditLayoutDialog(self, RowSelected, "Edit layout item", beamSettings._DefaultDisplaySettings)
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
                beamSettings._DefaultDisplaySettings.pop(RowSelected)
                self.BuildLayoutList()
    def OnCheckLayout(self, event):
        for i in range(0, len(beamSettings._DefaultDisplaySettings)):
            layout = beamSettings._DefaultDisplaySettings[i]
            if self.LayoutList.IsChecked(i):
                layout[u'Active'] = "yes"
            else:
                layout[u'Active'] = "no"
        self.BuildLayoutList()
#
# RULE BUTTONS
#
    def OnAddRule(self, event):
        self.EditRule = EditRuleDialog(self, self.RuleList.GetCount(), "Add rule")
        self.EditRule.Show()

    def OnEditRule(self, event):
        RowSelected = self.RuleList.GetSelection()
        if RowSelected>-1:
            self.EditRule = EditRuleDialog(self, RowSelected, "Edit rule")
            self.EditRule.Show()

    def OnDelRule(self, event):
        RowSelected = self.RuleList.GetSelection()
        if RowSelected>-1:
            LineToDelete = self.RuleList.GetString(RowSelected)
            dlg = wx.MessageDialog(self,
            "Do you really want to delete '"+LineToDelete+"' ?",
            "Confirm deletion", wx.OK|wx.CANCEL|wx.ICON_QUESTION)
            result = dlg.ShowModal()
            dlg.Destroy()
            if result == wx.ID_OK:
                beamSettings._rules.pop(RowSelected)
                self.BuildRuleList()

    def OnCheckRule(self, event):
        for i in range(0, len(beamSettings._rules)):
            rule = beamSettings._rules[i]
            if self.RuleList.IsChecked(i):
                rule[u'Active'] = "yes"
            else:
                rule[u'Active'] = "no"
        self.BuildRuleList()
