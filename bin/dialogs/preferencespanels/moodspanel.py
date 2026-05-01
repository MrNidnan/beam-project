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
import logging
import numpy
from bin.dialogs.editmooddialog import EditMoodDialog

#
# Panel for mood parameter and
# to list the moods inside the main frame
# with BuildMoodList
#

class MoodsPanel(wx.Panel):
    def __init__(self, parent, mainFrame, BeamSettings):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
        
        #############
        # VARIABLES #
        #############
        self.BeamSettings = BeamSettings
        self.mainFrame = mainFrame
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
        moodtransition = wx.StaticText(self, -1, "Mood_transition                     ")
        moodtransition.SetFont(font)
        self.TransitionDropdown = wx.ComboBox(self,value=self.BeamSettings.getMoodTransition(), choices=['No transition', 'Fade directly','Fade to black'], style=wx.CB_READONLY)
        self.TransitionSpeed = wx.Slider(self, -1, int(self.BeamSettings.getMoodTransitionSpeed()), 500, 5000,(0,0), (233,-1), wx.SL_HORIZONTAL)
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
        bgcolour = self.MoodList.GetBackgroundColour()
        logging.debug("... bgcolour: " + str(bgcolour))
        fgcolour = tuple(numpy.subtract((255,255,255,510),bgcolour))
        logging.debug("... fgcolour: " + str(fgcolour))
        self.MoodList.SetForegroundColour(fgcolour)
        self.MoodList.Bind(wx.EVT_LISTBOX_DCLICK, self.OnEditMood)
        self.MoodList.Bind(wx.EVT_CHECKLISTBOX, self.OnCheckMood)
        # List all configured moods
        self.BuildMoodList()
        
        ################
        # MOOD BUTTONS #
        ################
        self.AddMoodButton    = wx.Button(self, label="Add")
        self.DelMoodButton    = wx.Button(self, label="Delete")
        self.EditMoodButton   = wx.Button(self, label="Edit")
        self.AddMoodButton.Bind(wx.EVT_BUTTON, self.OnAddMood)
        self.EditMoodButton.Bind(wx.EVT_BUTTON, self.OnEditMood)
        self.DelMoodButton.Bind(wx.EVT_BUTTON, self.OnDelMood)
        sizerbuttons    = wx.BoxSizer(wx.HORIZONTAL)
        sizerbuttons.Add(self.AddMoodButton, flag=wx.RIGHT | wx.TOP, border=10)
        sizerbuttons.Add(self.DelMoodButton, flag=wx.RIGHT | wx.TOP, border=10)
        sizerbuttons.Add(self.EditMoodButton, flag=wx.RIGHT | wx.TOP, border=10)
    
    
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



    def updateSettings(self):
        self.mainFrame.updateSettings();

    def reloadFromSettings(self):
        self.TransitionDropdown.SetValue(self.BeamSettings.getMoodTransition())
        self.TransitionSpeed.SetValue(int(self.BeamSettings.getMoodTransitionSpeed()))
        self.updateMoodTransition()
        self.BuildMoodList()

###################################################################
#                           EVENTS                                #
###################################################################

        ##############
        # TRANSITION #
        ##############
    def OnTransitionSpeedScroll(self, e):
        obj = e.GetEventObject()
        self.BeamSettings.setMoodTransitionSpeed(obj.GetValue())
        self.updateMoodTransition()

    def OnTransitionDropdown(self, e):
        obj = e.GetEventObject()
        self.BeamSettings.setMoodTransition(obj.GetValue())
        self.updateMoodTransition()

    def updateMoodTransition(self):
        if self.BeamSettings.getMoodTransition() == "No transition":
            self.TransitionSpeed.Enable(False)
        else:
            self.TransitionSpeed.Enable(True)

        Timervalue = round(float(self.BeamSettings.getMoodTransitionSpeed())/1000,1)
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
        self.EditMoodButton = EditMoodDialog(self, self.MoodList.GetCount() + 1, "Add mood")
        self.EditMoodButton.Show()

    def OnEditMood(self, event):
        # V0.5.0.5 including default
        RowSelected = self.MoodList.GetSelection()
        if RowSelected>-1:
            self.MoodRule = EditMoodDialog(self, RowSelected, "Edit mood")
            self.MoodRule.Show()

    def OnDelMood(self, event):
        selrow = self.MoodList.GetSelection()
        # Do not delete 0 'Default'
        if selrow > 0:
            moodName = self.MoodList.GetString(selrow)
            deleteDialog = wx.MessageDialog(self,
                "Do you really want to delete '"+moodName+"' ?",
                "Confirm deletion", wx.OK|wx.CANCEL|wx.ICON_QUESTION)
            result = deleteDialog.ShowModal()
            deleteDialog.Destroy()
            if result == wx.ID_OK:
                self.BeamSettings.getMoods().pop(selrow)
                self.BeamSettings.markDirty()
                # points to self.BeamSettings.getMoods()[x]
            # List all configured moods
            self.BuildMoodList()
    
      #####################
        # LAYOUT CHECKBOXES #
        #####################
    def OnCheckMood(self, event):
        # V0.5.0.5 including default
        for i in range(0, len(self.BeamSettings.getMoods())):
            # 'Default' can not get uncecked
            if i == 0:
                self.MoodList.Check(i, check=True)

            mood = self.BeamSettings.getMoods()[i]
            if self.MoodList.IsChecked(i):
                mood['Active'] = "yes"
            else:
                mood['Active'] = "no"
        self.BeamSettings.markDirty()
        # List all configured moods
        self.BuildMoodList()

    # List all configured moods
    def BuildMoodList(self):
        self.MoodRows = []
        # V0.5.0.5 including default
        # for i in range(0, len(self.BeamSettings.getMoods())-1):
        for i in range(0, len(self.BeamSettings.getMoods())):
            # mood = self.BeamSettings.getMoods()[i+1]
            mood = self.BeamSettings.getMoods()[i]
            self.MoodRows.append(str(mood['Name']))
        self.MoodList.Set(self.MoodRows)
        # Check the rules
        for i in range(0, len(self.BeamSettings.getMoods())):
            moods = self.BeamSettings.getMoods()[i]
            if moods['Active'] == "yes":
                self.MoodList.Check(i, check=True)
            else:
                self.MoodList.Check(i, check=False)
