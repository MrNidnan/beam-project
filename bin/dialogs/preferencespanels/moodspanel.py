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

import wx, os
from bin.dialogs.editmoodframe import EditMoodFrame

###################################################################
#                           MOODS                                 #
###################################################################
class MoodsPanel(wx.Panel):
    def __init__(self, parent, BeamSettings):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
        
        #############
        # VARIABLES #
        #############
        self.BeamSettings = BeamSettings
        self.parent = parent
        self.MoodRows = []
        font = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD)

        ###############
        # Description #
        ###############
        description = wx.StaticText(self, -1, "A Mood changes the layout and background for some songs.\nMoods can be activated and deactivated with the check box.")
        description.Wrap(380)
        
        ###################
        # MOOD TRANSITION #
        ###################
        moodtransition = wx.StaticText(self, -1, "Mood transition")
        moodtransition.SetFont(font)
        self.TransitionDropdown = wx.ComboBox(self,value=self.BeamSettings._moodTransition, choices=['No transition', 'Fade directly','Fade to black'], style=wx.CB_READONLY)
        self.TransitionSpeed = wx.Slider(self, -1, int(self.BeamSettings._moodTransitionSpeed), 500, 5000,(0,0), (233,-1), wx.SL_HORIZONTAL)
        self.TransitionSpeedLabel = wx.StaticText(self, -1, "")
        self.TransitionDropdown.Bind(wx.EVT_COMBOBOX, self.OnTransitionDropdown)
        self.TransitionSpeed.Bind(wx.EVT_SCROLL, self.OnTransitionSpeedScroll)
        self.updateMoodTransition()
        hboxTransition = wx.BoxSizer(wx.VERTICAL)
        hboxTransition2 = wx.BoxSizer(wx.HORIZONTAL)
        hboxTransition.Add(self.TransitionDropdown, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=7)
        hboxTransition2.Add(self.TransitionSpeed, flag= wx.RIGHT | wx.BOTTOM, border=7)
        hboxTransition2.Add(self.TransitionSpeedLabel, flag=wx.LEFT | wx.BOTTOM, border=7)
        hboxTransition.Add(hboxTransition2, flag=wx.LEFT | wx.TOP, border=7)
        
        #############
        # MOOD LIST #
        #############
        moodstitle = wx.StaticText(self, -1, "Moods")
        moodstitle.SetFont(font)
        self.MoodList = wx.CheckListBox(self,-1, size=wx.DefaultSize, choices=self.MoodRows, style= wx.LB_NEEDED_SB)
        self.MoodList.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.MoodList.Bind(wx.EVT_LISTBOX_DCLICK, self.OnEditMood)
        self.MoodList.Bind(wx.EVT_CHECKLISTBOX, self.OnCheckMood)
        self.BuildMoodList()
        
        ################
        # MOOD BUTTONS #
        ################
        self.AddMood    = wx.Button(self, label="Add")
        self.DelMood    = wx.Button(self, label="Delete")
        self.EditMood   = wx.Button(self, label="Edit")
        self.AddMood.Bind(wx.EVT_BUTTON, self.OnAddMood)
        self.EditMood.Bind(wx.EVT_BUTTON, self.OnEditMood)
        self.DelMood.Bind(wx.EVT_BUTTON, self.OnDelMood)
        sizerbuttons    = wx.BoxSizer(wx.HORIZONTAL)
        sizerbuttons.Add(self.AddMood, flag=wx.RIGHT | wx.TOP, border=10)
        sizerbuttons.Add(self.DelMood, flag=wx.RIGHT | wx.TOP, border=10)
        sizerbuttons.Add(self.EditMood, flag=wx.RIGHT | wx.TOP, border=10)
    
    
        ##############
        # SET SIZERS #
        ##############
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(description, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        sizer.Add(moodtransition, flag=wx.LEFT| wx.TOP, border=10)
        sizer.Add(hboxTransition, flag=wx.LEFT, border=20)
        sizer.Add(moodstitle, flag=wx.LEFT| wx.TOP, border=10)
        sizer.Add(self.MoodList, proportion=1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        sizer.Add(sizerbuttons, flag=wx.LEFT | wx.BOTTOM, border=10)
        self.SetSizer(sizer)




###################################################################
#                           EVENTS                                #
###################################################################

        ##############
        # TRANSITION #
        ##############
    def OnTransitionSpeedScroll(self, e):
        obj = e.GetEventObject()
        self.BeamSettings._moodTransitionSpeed = obj.GetValue()
        self.updateMoodTransition()

    def OnTransitionDropdown(self, e):
        obj = e.GetEventObject()
        self.BeamSettings._moodTransition = obj.GetValue()
        self.updateMoodTransition()

    def updateMoodTransition(self):
        if self.BeamSettings._moodTransition == "No transition":
            self.TransitionSpeed.Enable(False)
        else:
            self.TransitionSpeed.Enable(True)

        Timervalue = round(float(self.BeamSettings._moodTransitionSpeed)/1000,1)
        if Timervalue < float(1.5):
            # Fast
            self.TransitionSpeedLabel.SetLabel(str(Timervalue) + " sec (Fast)")
        elif Timervalue < float(3):
            # Medium
            self.TransitionSpeedLabel.SetLabel(str(Timervalue) + " sec (Medium)")
        else:
            # Slow
            self.TransitionSpeedLabel.SetLabel(str(Timervalue) + " sec (Slow)")



        ##################
        # LAYOUT BUTTONS #
        ##################
    def OnAddMood(self, event):
        self.EditMood = EditMoodFrame(self, self.MoodList.GetCount() + 1, "Add mood")
        self.EditMood.Show()

    def OnEditMood(self, event):
        RowSelected = self.MoodList.GetSelection()+1
        if RowSelected>-1:
            self.MoodRule = EditMoodFrame(self, RowSelected, "Edit mood")
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
                self.BeamSettings._moods.pop(RowSelected+1)
            self.BuildMoodList()
    
        #####################
        # LAYOUT CHECKBOXES #
        #####################
    def OnCheckMood(self, event):
        for i in range(0, len(self.BeamSettings._moods)-1):
            mood = self.BeamSettings._moods[i+1]
            if self.MoodList.IsChecked(i):
                mood['Active'] = "yes"
            else:
                mood['Active'] = "no"
        self.BuildMoodList()

        ####################
        # BUILD LAYOUTLIST #
        ####################
    def BuildMoodList(self):
        self.MoodRows = []
        for i in range(0, len(self.BeamSettings._moods)-1):
            mood = self.BeamSettings._moods[i+1]
            self.MoodRows.append(str(mood['Name']))
        self.MoodList.Set(self.MoodRows)
        # Check the rules
        for i in range(0, len(self.BeamSettings._moods)-1):
            moods = self.BeamSettings._moods[i+1]
            if moods['Active'] == "yes":
                self.MoodList.Check(i, check=True)
            else:
                self.MoodList.Check(i, check=False)
        # Update Main window