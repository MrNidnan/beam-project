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
from bin.dialogs.editmooddialog import EditMood

#
# Build main preferences Window
#

class Preferences(wx.Frame):
    def __init__(self, parent):
        self.MainWindowParent = parent
        if self.MainWindowParent.IsFullScreen() or self.MainWindowParent.IsMaximized():
            x,y = wx.GetMousePosition()
            y = 300 # Only way to get it to work on MAC
        else:
            x,y = (self.MainWindowParent.GetPosition()+(50,50))
        
        wx.Frame.__init__(self, parent, title="Preferences", pos=(x,y),
                          style=wx.DEFAULT_FRAME_STYLE & ~ (wx.RESIZE_BORDER | wx.RESIZE_BOX | wx.MAXIMIZE_BOX))

        # Build the panel
        self.panel = wx.Panel(self)
        self.MainSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.panelbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.hbox = wx.BoxSizer(wx.HORIZONTAL)
        
        # Needed for layout style
        listWidth = 180
        listHeight= 200
        self.menu = wx.ListCtrl(self.panel,size=(listWidth,listHeight), style=wx.LC_REPORT | wx.LC_ALIGN_LEFT | wx.LC_SINGLE_SEL| wx.LC_NO_HEADER | wx.NO_BORDER)
        
        self.menu.SetBackgroundColour(self.panel.GetBackgroundColour())
        self.menu.InsertColumn(0, 'Menu', width=-1)
        menulist = ['Basic Settings','Default Layout','Moods','Rules','Tags']
        for item in xrange(len(menulist)):
            self.menu.InsertStringItem(item, menulist[item])
        self.menu.SetColumnWidth(0,listWidth)
        
        self.menu.Select(0)
        self.menu.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onSelectMenu)
        
        self.SettingsTabs = []
        self.SettingsTabs.append(self.BasicSettings())
        self.SettingsTabs.append(self.LayoutSettings())
        self.SettingsTabs.append(self.MoodsSettings())
        self.SettingsTabs.append(self.RulesSettings())
        self.SettingsTabs.append(self.TagsTab())
        for item in self.SettingsTabs:
            self.panelbox.Add(item, flag=wx.EXPAND)
        
        self.button_ok = wx.Button(self.panel, label="Save")
        self.button_cancel = wx.Button(self.panel, label="Close")
        self.button_ok.Bind(wx.EVT_BUTTON, self.onApply)
        self.button_cancel.Bind(wx.EVT_BUTTON, self.onClose)

        self.hbox.Add(self.button_ok,  flag=wx.LEFT | wx.TOP, border=10)
        self.hbox.Add(self.button_cancel, flag=wx.LEFT | wx.TOP | wx.RIGHT, border=10)
        self.vbox.Add(self.menu, flag= wx.LEFT | wx.BOTTOM | wx.TOP | wx.RIGHT, border=10)
        self.vbox.Add((200,-1),1,flag=wx.EXPAND |wx.ALIGN_CENTER)
        self.vbox.Add(self.hbox, flag= wx.BOTTOM, border=5)
        self.MainSizer.Add(self.vbox, flag=wx.EXPAND)
        self.MainSizer.Add(self.panelbox,  flag=wx.GROW)
        
        self.changePanel(0)
        
        self.panel.SetSizerAndFit(self.MainSizer)
        # Fix size (bug)
        self.SetSize((self.MainSizer.GetSize()+(0,35)))



#
# First tab - Basic Settings
#
    def BasicSettings(self):

        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Module dropdown
        mediaplayer = wx.StaticText(panel, -1, "Mediaplayer")
        font = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        mediaplayer.SetFont(font)
        mediadescription = wx.StaticText(panel, -1, "Select mediaplayer to display information from")
        self.ModuleSelectorDropdown = wx.ComboBox(panel,value=beamSettings._moduleSelected, choices=beamSettings._currentModules, style=wx.CB_READONLY)
        self.ModuleSelectorDropdown.Bind(wx.EVT_COMBOBOX, self.OnSelectModule)
        vbox.Add(mediaplayer, flag=wx.LEFT | wx.TOP | wx.BOTTOM, border=10)
        vbox.Add(mediadescription, flag=wx.LEFT, border=20)
        vbox.Add(self.ModuleSelectorDropdown, flag=wx.LEFT, border=20)
        
        
        # Settings
        settingslabel = wx.StaticText(panel, -1, "Settings")
        font = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        settingslabel.SetFont(font)
        vbox.Add(settingslabel, flag=wx.LEFT | wx.TOP | wx.BOTTOM, border=10)
        
        # Refresh time
        refreshtime = wx.StaticText(panel, -1, "Refresh time")
        self.RefreshTime = wx.Slider(panel, -1, int(beamSettings._updateTimer), 500, 10000,(0,0), (233,-1), wx.SL_HORIZONTAL)
        self.RefreshTimeLabel = wx.StaticText(panel, -1, "")
        self.RefreshTime.Bind(wx.EVT_SCROLL, self.OnRefreshTimerScroll)
        self.updateRefreshTimerLabel()
        vbox.Add(refreshtime, flag=wx.LEFT, border=20)
        hboxRefresh = wx.BoxSizer(wx.HORIZONTAL)
        hboxRefresh.Add(self.RefreshTime, flag= wx.LEFT | wx.RIGHT | wx.TOP, border=7)
        hboxRefresh.Add(self.RefreshTimeLabel, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=7)
        vbox.Add(hboxRefresh, flag=wx.LEFT, border=20)
        
        # Tanda Length
        tandalength = wx.StaticText(panel, -1, "Tanda Length")
        self.TandaLength = wx.Slider(panel, -1, beamSettings._maxTandaLength, 0, 10,(0,0), (233,-1), wx.SL_HORIZONTAL)
        self.TandaLengthLabel = wx.StaticText(panel, -1, "")
        self.TandaLength.Bind(wx.EVT_SCROLL, self.OnTandaLengthScroll)
        self.maxTandaLengthLabel()
        vbox.Add(tandalength, flag=wx.LEFT, border=20)
        hboxTanda = wx.BoxSizer(wx.HORIZONTAL)
        hboxTanda.Add(self.TandaLength, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=7)
        hboxTanda.Add(self.TandaLengthLabel, flag=wx.LEFT | wx.TOP, border=7)
        vbox.Add(hboxTanda, flag=wx.LEFT, border=20)
        
        # Mood transition
        moodtransition = wx.StaticText(panel, -1, "Mood transition")
        self.TransitionDropdown = wx.ComboBox(panel,value=beamSettings._moodTransition, choices=['No transition', 'Fade directly','Fade to black'], style=wx.CB_READONLY)
        self.TransitionSpeed = wx.Slider(panel, -1, int(beamSettings._moodTransitionSpeed), 500, 5000,(0,0), (233,-1), wx.SL_HORIZONTAL)
        self.TransitionSpeedLabel = wx.StaticText(panel, -1, "")
        self.TransitionDropdown.Bind(wx.EVT_COMBOBOX, self.OnTransitionDropdown)
        self.TransitionSpeed.Bind(wx.EVT_SCROLL, self.OnTransitionSpeedScroll)
        self.updateMoodTransition()
        vbox.Add(moodtransition, flag=wx.LEFT, border=20)
        hboxTransition = wx.BoxSizer(wx.VERTICAL)
        hboxTransition2 = wx.BoxSizer(wx.HORIZONTAL)
        hboxTransition.Add(self.TransitionDropdown, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=7)
        hboxTransition2.Add(self.TransitionSpeed, flag= wx.RIGHT | wx.BOTTOM, border=7)
        hboxTransition2.Add(self.TransitionSpeedLabel, flag=wx.LEFT | wx.TOP | wx.BOTTOM, border=7)
        hboxTransition.Add(hboxTransition2, flag=wx.LEFT | wx.TOP, border=7)
        vbox.Add(hboxTransition, flag=wx.LEFT, border=20)

        # Window decoration
        windowdecoration = wx.StaticText(panel, -1, "Window decoration")
        self.StatusBarCheckBox = wx.CheckBox(panel, label='Show statusbar')
        if beamSettings._showStatusbar == 'True':
            self.StatusBarCheckBox.SetValue(True)
        else:
            self.StatusBarCheckBox.SetValue(False)
        self.StatusBarCheckBox.Bind(wx.EVT_CHECKBOX, self.OnStatusBarCheckBox)
        vbox.Add(windowdecoration, flag=wx.LEFT, border=20)
        hboxDecoration = wx.BoxSizer(wx.HORIZONTAL)
        hboxDecoration.Add(self.StatusBarCheckBox, flag=wx.LEFT | wx.RIGHT | wx.TOP | wx.BOTTOM, border=7)
        vbox.Add(hboxDecoration, flag=wx.LEFT, border=20)

        # Logging
        logging = wx.StaticText(panel, -1, "Logging (require restart)")
        self.LogCheckBox = wx.CheckBox(panel, label='Log to '+beamSettings._logPath)
        if beamSettings._logging == 'True':
            self.LogCheckBox.SetValue(True)
        else:
            self.LogCheckBox.SetValue(False)
        vbox.Add(logging, flag=wx.LEFT, border=20)
        hboxLog = wx.BoxSizer(wx.HORIZONTAL)
        hboxLog.Add(self.LogCheckBox, flag=wx.LEFT | wx.RIGHT | wx.TOP | wx.BOTTOM, border=7)
        vbox.Add(hboxLog, flag=wx.LEFT, border=20)
        
        panel.SetSizer(vbox)
        return panel


#
# Second tab - Default Layout
#

    def LayoutSettings(self):

        panel = wx.Panel(self)
        self.DisplayRows = []

        # Layout buttons
        self.AddLayout  = wx.Button(panel, label="Add")
        self.DelLayout  = wx.Button(panel, label="Delete")
        self.EditLayout = wx.Button(panel, label="Edit")
        sizerbuttons    = wx.BoxSizer(wx.HORIZONTAL)
        sizerbuttons.Add(self.AddLayout, flag=wx.RIGHT, border=10)
        sizerbuttons.Add(self.DelLayout, flag=wx.RIGHT, border=10)
        sizerbuttons.Add(self.EditLayout, flag=wx.RIGHT, border=10)

        description = wx.StaticText(panel, -1, "The Default Layout is the layout configuration which will be shown when Beam is playing.")
        description.Wrap(380)
        
        # Background image
        background = wx.StaticText(panel, -1, "Default Background Image")
        font = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        background.SetFont(font)
        backdescription = wx.StaticText(panel, -1, "Select background image (1920x1080 recommended)")
        self.browse = wx.Button(panel, label="Browse")
        self.browse.Bind(wx.EVT_BUTTON, self.browseBackgroundImage)
        (path,backgroundfile) = os.path.split(beamSettings._moods[0][u'Background'])
        self.currentBackground = wx.StaticText(panel, -1, backgroundfile)
        hboxBackground = wx.BoxSizer(wx.HORIZONTAL)
        hboxBackground.Add(self.browse, flag=wx.RIGHT | wx.TOP, border=5)
        hboxBackground.Add(self.currentBackground, flag=wx.LEFT | wx.TOP, border=5)
        self.ChangeBackgroundBox = wx.CheckBox(panel, label='Change Background: ')
        self.BackgroundTimerBox = wx.ComboBox(panel, choices=['Every 30 seconds', 'Every 1 minute', 'Every 2 minutes', 'Every 3 minutes', 'Every 5 minutes','Every 10 minutes','Every 20 minutes'], style=wx.CB_READONLY)
        self.RandomBackgroundBox = wx.CheckBox(panel, label='Random order')
        self.ChangeBackgroundBox.Bind(wx.EVT_CHECKBOX, self.OnRotateBackground)
        self.RandomBackgroundBox.Bind(wx.EVT_CHECKBOX, self.OnRotateBackground)
        self.BackgroundTimerBox.Bind(wx.EVT_COMBOBOX, self.OnRotateBackground)
        if beamSettings._moods[0][u'RotateBackground'] == "linear":
            self.ChangeBackgroundBox.SetValue(True)
            self.RandomBackgroundBox.SetValue(False)
        elif beamSettings._moods[0][u'RotateBackground'] == "random":
            self.ChangeBackgroundBox.SetValue(True)
            self.RandomBackgroundBox.SetValue(True)
        else:
            self.ChangeBackgroundBox.SetValue(False)
            self.RandomBackgroundBox.SetValue(False)
            self.RandomBackgroundBox.Disable()
            self.BackgroundTimerBox.Disable()
        self.rotateBackgroundFunction()
        RandomSizer = wx.BoxSizer(wx.HORIZONTAL)
        RandomSizer.Add(self.ChangeBackgroundBox, flag=wx.RIGHT | wx.LEFT, border=10)
        RandomSizer.Add(self.BackgroundTimerBox)
        
        
        # Layout list
        self.LayoutList = wx.CheckListBox(panel,-1, choices=[], style= wx.LB_NEEDED_SB)
        self.LayoutList.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.LayoutList.Bind(wx.EVT_LISTBOX_DCLICK, self.OnEditLayout)
        self.LayoutList.Bind(wx.EVT_CHECKLISTBOX, self.OnCheckLayout)

        # Load data into table
        self.BuildLayoutList()

        self.AddLayout.Bind(wx.EVT_BUTTON, self.OnAddLayout)
        self.EditLayout.Bind(wx.EVT_BUTTON, self.OnEditLayout)
        self.DelLayout.Bind(wx.EVT_BUTTON, self.OnDelLayout)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(description, flag=wx.ALIGN_TOP | wx.ALL, border=10)
        sizer.Add(background, flag=wx.LEFT | wx.TOP | wx.BOTTOM, border=10)
        sizer.Add(backdescription, flag=wx.LEFT, border=20)
        sizer.Add(hboxBackground, flag=wx.LEFT, border=20)
        sizer.Add(RandomSizer, flag=wx.LEFT | wx.TOP, border=10)
        sizer.Add(self.RandomBackgroundBox, flag=wx.LEFT, border=20)
        sizer.Add(self.LayoutList, flag= wx.EXPAND| wx.ALL, border=10 )
        sizer.Add(sizerbuttons, flag=wx.ALIGN_BOTTOM | wx.ALL, border=10)
        panel.SetSizerAndFit(sizer)

        return panel
    

#
# Third tab - Moods
#

    def MoodsSettings(self):
    
        panel = wx.Panel(self)
        self.MoodRows = []
        
        # Mood buttons
        self.AddMood    = wx.Button(panel, label="Add")
        self.DelMood    = wx.Button(panel, label="Delete")
        self.EditMood   = wx.Button(panel, label="Edit")
        sizerbuttons    = wx.BoxSizer(wx.HORIZONTAL)
        sizerbuttons.Add(self.AddMood, flag=wx.RIGHT | wx.TOP, border=10)
        sizerbuttons.Add(self.DelMood, flag=wx.RIGHT | wx.TOP, border=10)
        sizerbuttons.Add(self.EditMood, flag=wx.RIGHT | wx.TOP, border=10)
        
        self.AddMood.Bind(wx.EVT_BUTTON, self.OnAddMood)
        self.EditMood.Bind(wx.EVT_BUTTON, self.OnEditMood)
        self.DelMood.Bind(wx.EVT_BUTTON, self.OnDelMood)

        description = wx.StaticText(panel, -1, "A Mood changes the layout and background for some songs.\nMoods can be activated and deactivated with the check box.")
        description.Wrap(380)
        
        self.MoodList = wx.CheckListBox(panel,-1, size=wx.DefaultSize, choices=self.MoodRows, style= wx.LB_NEEDED_SB)
        self.MoodList.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.MoodList.Bind(wx.EVT_LISTBOX_DCLICK, self.OnEditMood)
        self.MoodList.Bind(wx.EVT_CHECKLISTBOX, self.OnCheckMood)
        
        # Load data in table
        self.BuildMoodList()
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(description, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        sizer.Add(self.MoodList, proportion=1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        sizer.Add(sizerbuttons, flag=wx.LEFT | wx.BOTTOM | wx.TOP, border=10)
        panel.SetSizer(sizer)
        
        return panel
    
    
    
#
# Forth tab - Cortinas and Rules
#

    def RulesSettings(self):

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

        description = wx.StaticText(panel, -1, "Rules are used to:\n - Copy information from one tag to another.\n - Define Cortinas.\n - Split tags, such tags with both artist and title.\n - Ignore songs completely, such as silent tracks.\n\nRules can be activated and deactivated with the check box.")
        description.Wrap(380)
        
        self.RuleList = wx.CheckListBox(panel,-1, size=wx.DefaultSize, choices=self.RuleRows, style= wx.LB_NEEDED_SB)
        self.RuleList.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.RuleList.Bind(wx.EVT_LISTBOX_DCLICK, self.OnEditRule)
        self.RuleList.Bind(wx.EVT_CHECKLISTBOX, self.OnCheckRule)

        # Load data into table
        self.BuildRuleList()

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(description, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        sizer.Add(self.RuleList, proportion=1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        sizer.Add(sizerbuttons, flag=wx.LEFT | wx.BOTTOM | wx.TOP, border=10)
        panel.SetSizer(sizer)

        return panel
    
    
#
# Fifth tab - Basic Settings
#
    def TagsTab(self):
        
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # Description
        tagpreview = wx.StaticText(panel, -1, "Tags preview")
        font = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        tagpreview.SetFont(font)
        description = wx.StaticText(panel, -1, "Here are all available tags and their values displayed for")
        
        # Tag dropdown
        self.TagDropdown = wx.ComboBox(panel,value="Current Song", choices=["Current Song","Previous Song","Next Song","Next Tanda", "Misc"], style=wx.CB_READONLY)
        self.TagDropdown.Bind(wx.EVT_COMBOBOX, self.onTagDropdown)
        
        vbox.Add(tagpreview, flag=wx.LEFT | wx.TOP | wx.BOTTOM, border=10)
        vbox.Add(description, flag=wx.LEFT, border=20)
        vbox.Add(self.TagDropdown, flag=wx.LEFT, border=20)
        
        panel.SetSizer(vbox)
        return panel
    
    
################################################
#
# FUNCTIONS
#
################################################

    def BuildLayoutList(self):
        self.DisplayRows = []
        for i in range(0, len(beamSettings._moods[0][u'Display'])):
            Settings = beamSettings._moods[0][u'Display'][i]
            self.DisplayRows.append(Settings[u'Field'])
        self.LayoutList.Set(self.DisplayRows)
        for i in range(0, len(beamSettings._moods[0][u'Display'])):
            Settings = beamSettings._moods[0][u'Display'][i]
            if Settings['Active'] == "yes":
                self.LayoutList.Check(i, check=True)
            else:
                self.LayoutList.Check(i, check=False)
        # Update Main window
        self.MainWindowParent.processData()
#
# Build Cortinas and Rules
#

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
            
            if rule[u'Type'] == "Ignore":
                if rule[u'Field2'] =="is":
                    self.RuleRows.append(str("Ignore song if "+rule[u'Field1']+' is '+rule[u'Field3']))
                if rule[u'Field2'] =="is not":
                    self.RuleRows.append(str("Ignore song if "+rule[u'Field1']+' is not '+rule[u'Field3']))
                if rule[u'Field2'] =="contains":
                    self.RuleRows.append(str("Ignore song if "+rule[u'Field1']+' contains '+rule[u'Field3']))
        self.RuleList.Set(self.RuleRows)
        # Check the rules
        for i in range(0, len(beamSettings._rules)):
            rule = beamSettings._rules[i]
            if rule[u'Active'] == "yes":
                self.RuleList.Check(i, check=True)
            else:
                self.RuleList.Check(i, check=False)
        # Update Main window
        self.MainWindowParent.processData()

#
# BUILD MOODS
#
    def BuildMoodList(self):
        self.MoodRows = []
        for i in range(0, len(beamSettings._moods)-1):
            mood = beamSettings._moods[i+1]
            self.MoodRows.append(str(mood[u'Name']))
        self.MoodList.Set(self.MoodRows)
        # Check the rules
        for i in range(0, len(beamSettings._moods)-1):
            moods = beamSettings._moods[i+1]
            if moods[u'Active'] == "yes":
                self.MoodList.Check(i, check=True)
            else:
                self.MoodList.Check(i, check=False)
        # Update Main window
        self.MainWindowParent.processData()

#
# CHANGE PANEL
#
    def changePanel(self, selectedPanel):
        for item in self.SettingsTabs:
            item.Hide()
        self.SettingsTabs[selectedPanel].Show()
        self.panel.Layout()

################################################
#
# EVENTS
#
################################################

    def onSelectMenu(self, e):
        # Change panel
       self.changePanel(self.menu.GetFirstSelected(self))


############
# ALL TABS #
############
#
# Apply preferences
#
    def onApply(self, e):
        # Get Settings
        beamSettings._moduleSelected        = self.ModuleSelectorDropdown.GetValue()
        beamSettings._maxTandaLength        = int(self.TandaLength.GetValue())
        beamSettings._logging               = str(self.LogCheckBox.GetValue())
        beamSettings.SaveConfig(beamSettings.defaultConfigFileName)
        self.MainWindowParent.rotateBackground()



#
# Cancel preferences
#
    def onClose(self, e):
        self.Destroy()

############
#  TAB 1   #
############
#
# Browse Background
#

    def OnSelectModule(self, event):
        beamSettings._moduleSelected        = self.ModuleSelectorDropdown.GetValue()
    
    def browseBackgroundImage(self, event):
        openFileDialog = wx.FileDialog(self, "Set new background image", 
                                       os.path.join(os.getcwd(), 'resources', 'backgrounds'), "",
                                       "Image files(*.png,*.jpg)|*.png;*.jpg",
                                       wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        if openFileDialog.ShowModal() == wx.ID_OK:
            beamSettings._moods[0][u'Background'] = openFileDialog.GetPath()
            # change current background
            self.MainWindowParent._currentBackgroundPath = beamSettings._moods[0][u'Background']
            (path,backgroundfile) = os.path.split(beamSettings._moods[0][u'Background'])
            self.currentBackground.SetLabel(backgroundfile)
            self.MainWindowParent.changeBackground()
            openFileDialog.Destroy()

#
# Refresh time slider
#
    def OnRefreshTimerScroll(self, e):
        obj = e.GetEventObject()
        beamSettings._updateTimer = obj.GetValue()
        self.updateRefreshTimerLabel()
    
    def updateRefreshTimerLabel(self):
        Timervalue = round(float(beamSettings._updateTimer)/1000,1)
        if beamSettings._updateTimer < 2000:
            # Fast
            self.RefreshTimeLabel.SetLabel(str(Timervalue) + " sec (Fast)")
        elif beamSettings._updateTimer < 5000:
            # Medium
            self.RefreshTimeLabel.SetLabel(str(Timervalue) + " sec (Medium)")
        else:
            # Slow
            self.RefreshTimeLabel.SetLabel(str(Timervalue) + " sec (Slow)")


    def OnStatusBarCheckBox(self, e):
        beamSettings._showStatusbar = str(self.StatusBarCheckBox.GetValue())
        self.MainWindowParent.showStatusBar()
        self.MainWindowParent.Refresh()
#
# Tanda length slider
#
    def OnTandaLengthScroll(self, e):
        obj = e.GetEventObject()
        beamSettings._maxTandaLength = obj.GetValue()
        self.maxTandaLengthLabel()
    
    def maxTandaLengthLabel(self):
        if beamSettings._maxTandaLength > 0:
            self.TandaLengthLabel.SetLabel(str(beamSettings._maxTandaLength) + " songs")
        else:
            self.TandaLengthLabel.SetLabel("No preview")
#
# Mood transition dropdown and slider
#


    def OnTransitionSpeedScroll(self, e):
        obj = e.GetEventObject()
        beamSettings._moodTransitionSpeed = obj.GetValue()
        self.updateMoodTransition()
    
    def OnTransitionDropdown(self, e):
        obj = e.GetEventObject()
        beamSettings._moodTransition = obj.GetValue()
        self.updateMoodTransition()

    def updateMoodTransition(self):
        if beamSettings._moodTransition == "No transition":
            self.TransitionSpeed.Enable(False)
        else:
            self.TransitionSpeed.Enable(True)
        
        Timervalue = round(float(beamSettings._moodTransitionSpeed)/1000,1)
        if beamSettings._moodTransitionSpeed < 1000:
            # Fast
            self.TransitionSpeedLabel.SetLabel(str(Timervalue) + " sec (Fast)")
        elif beamSettings._moodTransitionSpeed < 3000:
            # Medium
            self.TransitionSpeedLabel.SetLabel(str(Timervalue) + " sec (Medium)")
        else:
            # Slow
            self.TransitionSpeedLabel.SetLabel(str(Timervalue) + " sec (Slow)")

#
# Logging checkbox
#

############
#  TAB 2   #
############
#
# LAYOUT BUTTONS
#
#
    def OnAddLayout(self, event):
        self.EditLayout = EditLayoutDialog(self, len(self.DisplayRows), "Add layout item", beamSettings._moods[0][u'Display'])
        self.EditLayout.Show()

    def OnEditLayout(self, event):
        RowSelected = self.LayoutList.GetSelection()
        if RowSelected>-1:
            self.EditLayout = EditLayoutDialog(self, RowSelected, "Edit layout item", beamSettings._moods[0][u'Display'])
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
                beamSettings._moods[0][u'Display'].pop(RowSelected)
                self.BuildLayoutList()

    def OnCheckLayout(self, event):
        for i in range(0, len(beamSettings._moods[0][u'Display'])):
            layout = beamSettings._moods[0][u'Display'][i]
            if self.LayoutList.IsChecked(i):
                layout[u'Active'] = "yes"
            else:
                layout[u'Active'] = "no"
        self.BuildLayoutList()
#
# ROTATE/RANDOM BACKGROUND
#
    def OnRotateBackground(self, event):
        if self.ChangeBackgroundBox.IsChecked() and not self.RandomBackgroundBox.IsChecked():
            beamSettings._moods[0][u'RotateBackground'] = "linear"
            self.RandomBackgroundBox.Enable()
            self.BackgroundTimerBox.Enable()
        elif self.ChangeBackgroundBox.IsChecked() and self.RandomBackgroundBox.IsChecked():
            beamSettings._moods[0][u'RotateBackground'] = "random"
            self.RandomBackgroundBox.Enable()
            self.BackgroundTimerBox.Enable()
        else:
            beamSettings._moods[0][u'RotateBackground'] = "no"
            self.RandomBackgroundBox.Disable()
            self.BackgroundTimerBox.Disable()
        timerVector = [30, 60, 120, 180, 300, 600, 1200]
        beamSettings._moods[0][u'RotateTimer'] = timerVector[int(self.BackgroundTimerBox.GetSelection())]
        self.rotateBackgroundFunction()
    
    
    def rotateBackgroundFunction(self):
        if int(beamSettings._moods[0][u'RotateTimer']) == 30:
            self.BackgroundTimerBox.SetSelection(0)
        elif int(beamSettings._moods[0][u'RotateTimer']) == 60:
            self.BackgroundTimerBox.SetSelection(1)
        elif int(beamSettings._moods[0][u'RotateTimer']) == 120:
            self.BackgroundTimerBox.SetSelection(2)
        elif int(beamSettings._moods[0][u'RotateTimer']) == 180:
            self.BackgroundTimerBox.SetSelection(3)
        elif int(beamSettings._moods[0][u'RotateTimer']) == 300:
            self.BackgroundTimerBox.SetSelection(4)
        elif int(beamSettings._moods[0][u'RotateTimer']) == 600:
            self.BackgroundTimerBox.SetSelection(5)
        elif int(beamSettings._moods[0][u'RotateTimer']) == 1200:
            self.BackgroundTimerBox.SetSelection(6)
        else:
            self.BackgroundTimerBox.SetSelection(2)
        
        (path,backgroundfile) = os.path.split(beamSettings._moods[0][u'Background'])
        if beamSettings._moods[0][u'RotateBackground'] == "no":
            self.currentBackground.SetLabel("Image: " + backgroundfile)
        else:
            self.currentBackground.SetLabel("Images from folder: " + os.path.dirname(path))

############
#  TAB 4   #
############
#
# MOODS BUTTONS
#
    def OnAddMood(self, event):
        self.EditMood = EditMood(self, self.MoodList.GetCount()+1, "Add mood")
        self.EditMood.Show()

    def OnEditMood(self, event):
        RowSelected = self.MoodList.GetSelection()+1
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
                beamSettings._moods.pop(RowSelected+1)
            self.BuildMoodList()

    def OnCheckMood(self, event):
        for i in range(0, len(beamSettings._moods)-1):
            mood = beamSettings._moods[i+1]
            if self.MoodList.IsChecked(i):
                mood[u'Active'] = "yes"
            else:
                mood[u'Active'] = "no"
        self.BuildMoodList()


############
#  TAB 5   #
############
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

############
#  TAB 6   #
############

    def onTagDropdown(self, event):
        selected = self.TagDropdown.GetValue()
        print selected
