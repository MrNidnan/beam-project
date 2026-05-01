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
from bin.dialogs.editartistbackgrounddialog import EditArtistBackgroundDialog
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
        self.artistBackgroundRows = []
        font = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        self.matchFields = ["%AlbumArtist", "%Artist", "%Performer"]

        ##########
        # MOODS  #
        ##########
        moodsDescription = wx.StaticText(self, -1, "A Mood changes the layout and background for some songs.\nMoods can be activated and deactivated with the check box.")
        moodsDescription.Wrap(380)        
        moodtransition = wx.StaticText(self, -1, "Mood Transition                     ")
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
        self.MoodList = wx.CheckListBox(self,-1, size=(240, 180), choices=self.MoodRows, style= wx.LB_NEEDED_SB)
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

        ############################
        # ARTIST BACKGROUND INPUTS #
        ############################
        artistBackgroundTitle = wx.StaticText(self, -1, "Artist Backgrounds")
        artistBackgroundTitle.SetFont(font)
        artistBackgroundDescription = wx.StaticText(
            self,
            -1,
            "Artist backgrounds add an optional orchestra/artist image layer on top of the mood background. Configure matching here instead of editing JSON manually.",
        )
        artistBackgroundDescription.Wrap(380)

        artistBackgrounds = self.BeamSettings.getArtistBackgrounds()
        self.EnableArtistBackgrounds = wx.CheckBox(self, label='Enable artist backgrounds')
        self.EnableArtistBackgrounds.SetValue(str(artistBackgrounds.get('Enabled', 'False')).lower() == 'true')
        self.EnableArtistBackgrounds.Bind(wx.EVT_CHECKBOX, self.OnArtistBackgroundSettingsChanged)

        self.MatchFieldDropdown = wx.ComboBox(self, value=artistBackgrounds.get('MatchField', '%AlbumArtist'), choices=self.matchFields, style=wx.CB_READONLY)
        self.MatchFieldDropdown.Bind(wx.EVT_COMBOBOX, self.OnArtistBackgroundSettingsChanged)
        self.FallbackFieldDropdown = wx.ComboBox(self, value=artistBackgrounds.get('FallbackField', '%Artist'), choices=self.matchFields, style=wx.CB_READONLY)
        self.FallbackFieldDropdown.Bind(wx.EVT_COMBOBOX, self.OnArtistBackgroundSettingsChanged)
        self.DefaultModeDropdown = wx.ComboBox(self, value=artistBackgrounds.get('DefaultMode', 'blend'), choices=['blend', 'replace', 'off'], style=wx.CB_READONLY)
        self.DefaultModeDropdown.Bind(wx.EVT_COMBOBOX, self.OnArtistBackgroundSettingsChanged)
        self.DefaultOpacitySlider = wx.Slider(self, -1, int(artistBackgrounds.get('DefaultOpacity', 35)), 0, 100, (0,0), (233,-1), wx.SL_HORIZONTAL)
        self.DefaultOpacitySlider.Bind(wx.EVT_SCROLL, self.OnArtistBackgroundSettingsChanged)
        self.DefaultOpacityLabel = wx.StaticText(self, -1, '')

        artistSettingsGrid = wx.FlexGridSizer(0, 2, 5, 10)
        artistSettingsGrid.AddGrowableCol(1, 1)
        artistSettingsGrid.Add(self.EnableArtistBackgrounds, 0, wx.ALIGN_CENTER_VERTICAL)
        artistSettingsGrid.Add(wx.StaticText(self, -1, ''))
        artistSettingsGrid.Add(wx.StaticText(self, -1, 'Default match field'), 0, wx.ALIGN_CENTER_VERTICAL)
        artistSettingsGrid.Add(self.MatchFieldDropdown, 0, wx.EXPAND)
        artistSettingsGrid.Add(wx.StaticText(self, -1, 'Fallback field'), 0, wx.ALIGN_CENTER_VERTICAL)
        artistSettingsGrid.Add(self.FallbackFieldDropdown, 0, wx.EXPAND)
        artistSettingsGrid.Add(wx.StaticText(self, -1, 'Default mode'), 0, wx.ALIGN_CENTER_VERTICAL)
        artistSettingsGrid.Add(self.DefaultModeDropdown, 0, wx.EXPAND)
        opacitySizer = wx.BoxSizer(wx.HORIZONTAL)
        opacitySizer.Add(self.DefaultOpacitySlider, proportion=1, flag=wx.RIGHT, border=10)
        opacitySizer.Add(self.DefaultOpacityLabel, flag=wx.ALIGN_CENTER_VERTICAL)
        artistSettingsGrid.Add(wx.StaticText(self, -1, 'Default opacity'), 0, wx.ALIGN_CENTER_VERTICAL)
        artistSettingsGrid.Add(opacitySizer, 0, wx.EXPAND)

        self.ArtistBackgroundList = wx.CheckListBox(self, -1, choices=self.artistBackgroundRows, style=wx.LB_NEEDED_SB)
        self.ArtistBackgroundList.Bind(wx.EVT_LISTBOX_DCLICK, self.OnEditArtistBackground)
        self.ArtistBackgroundList.Bind(wx.EVT_CHECKLISTBOX, self.OnCheckArtistBackground)
        self.BuildArtistBackgroundList()

        self.AddArtistBackgroundButton = wx.Button(self, label='Add')
        self.EditArtistBackgroundButton = wx.Button(self, label='Edit')
        self.DelArtistBackgroundButton = wx.Button(self, label='Delete')
        self.AddArtistBackgroundButton.Bind(wx.EVT_BUTTON, self.OnAddArtistBackground)
        self.EditArtistBackgroundButton.Bind(wx.EVT_BUTTON, self.OnEditArtistBackground)
        self.DelArtistBackgroundButton.Bind(wx.EVT_BUTTON, self.OnDelArtistBackground)
        artistButtons = wx.BoxSizer(wx.HORIZONTAL)
        artistButtons.Add(self.AddArtistBackgroundButton, flag=wx.RIGHT | wx.TOP, border=10)
        artistButtons.Add(self.DelArtistBackgroundButton, flag=wx.RIGHT | wx.TOP, border=10)
        artistButtons.Add(self.EditArtistBackgroundButton, flag=wx.RIGHT | wx.TOP, border=10)
    
    
        ##############
        # SET SIZERS #
        ##############
        moodColumn = wx.BoxSizer(wx.VERTICAL)
        moodColumn.Add(moodstitle, flag=wx.LEFT | wx.TOP, border=10)
        moodColumn.Add(moodsDescription, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        moodColumn.Add(moodtransition, flag=wx.LEFT | wx.TOP, border=10)
        moodColumn.Add(hboxTransition, flag=wx.LEFT | wx.RIGHT, border=20)
        moodColumn.Add(self.MoodList, proportion=1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        moodColumn.Add(sizerbuttons, flag=wx.LEFT | wx.BOTTOM, border=10)

        artistColumn = wx.BoxSizer(wx.VERTICAL)
        artistColumn.Add(artistBackgroundTitle, flag=wx.LEFT | wx.TOP, border=10)
        artistColumn.Add(artistBackgroundDescription, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        artistColumn.Add(artistSettingsGrid, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=20)
        artistColumn.Add(self.ArtistBackgroundList, proportion=1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        artistColumn.Add(artistButtons, flag=wx.LEFT | wx.BOTTOM, border=10)

        columnsSizer = wx.BoxSizer(wx.HORIZONTAL)
        columnsSizer.Add(moodColumn, proportion=1, flag=wx.EXPAND | wx.RIGHT, border=10)
        columnsSizer.Add(artistColumn, proportion=1, flag=wx.EXPAND | wx.LEFT, border=10)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(columnsSizer, proportion=1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=10)
        self.SetSizer(sizer)
        self.updateArtistBackgroundControls()



    def updateSettings(self):
        self.mainFrame.updateSettings();

    def reloadFromSettings(self):
        self.TransitionDropdown.SetValue(self.BeamSettings.getMoodTransition())
        self.TransitionSpeed.SetValue(int(self.BeamSettings.getMoodTransitionSpeed()))
        self.updateMoodTransition()
        self.BuildMoodList()
        artistBackgrounds = self.BeamSettings.getArtistBackgrounds()
        self.EnableArtistBackgrounds.SetValue(str(artistBackgrounds.get('Enabled', 'False')).lower() == 'true')
        self.MatchFieldDropdown.SetValue(artistBackgrounds.get('MatchField', '%AlbumArtist'))
        self.FallbackFieldDropdown.SetValue(artistBackgrounds.get('FallbackField', '%Artist'))
        self.DefaultModeDropdown.SetValue(artistBackgrounds.get('DefaultMode', 'blend'))
        self.DefaultOpacitySlider.SetValue(int(artistBackgrounds.get('DefaultOpacity', 35)))
        self.updateArtistBackgroundControls()
        self.BuildArtistBackgroundList()

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

    def updateArtistBackgroundControls(self):
        self.DefaultOpacityLabel.SetLabel(str(self.DefaultOpacitySlider.GetValue()) + '%')
        enabled = self.EnableArtistBackgrounds.GetValue()
        self.MatchFieldDropdown.Enable(enabled)
        self.FallbackFieldDropdown.Enable(enabled)
        self.DefaultModeDropdown.Enable(enabled)
        self.DefaultOpacitySlider.Enable(enabled)
        self.DefaultOpacityLabel.Enable(enabled)

    def OnArtistBackgroundSettingsChanged(self, event):
        artistBackgrounds = self.BeamSettings.getArtistBackgrounds()
        artistBackgrounds['Enabled'] = 'True' if self.EnableArtistBackgrounds.GetValue() else 'False'
        artistBackgrounds['MatchField'] = self.MatchFieldDropdown.GetValue()
        artistBackgrounds['FallbackField'] = self.FallbackFieldDropdown.GetValue()
        artistBackgrounds['DefaultMode'] = self.DefaultModeDropdown.GetValue()
        artistBackgrounds['DefaultOpacity'] = int(self.DefaultOpacitySlider.GetValue())
        self.BeamSettings.markDirty()
        self.updateArtistBackgroundControls()
        self.updateSettings()



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

    def OnAddArtistBackground(self, event):
        dialog = EditArtistBackgroundDialog(self, self.ArtistBackgroundList.GetCount(), 'Add artist background')
        dialog.Show()

    def OnEditArtistBackground(self, event):
        rowSelected = self.ArtistBackgroundList.GetSelection()
        if rowSelected > -1:
            dialog = EditArtistBackgroundDialog(self, rowSelected, 'Edit artist background')
            dialog.Show()

    def OnDelArtistBackground(self, event):
        rowSelected = self.ArtistBackgroundList.GetSelection()
        if rowSelected < 0:
            return

        lineToDelete = self.ArtistBackgroundList.GetString(rowSelected)
        dialog = wx.MessageDialog(
            self,
            "Do you really want to delete '" + lineToDelete + "' ?",
            'Confirm deletion',
            wx.OK | wx.CANCEL | wx.ICON_QUESTION,
        )
        result = dialog.ShowModal()
        dialog.Destroy()
        if result == wx.ID_OK:
            self.BeamSettings.getArtistBackgroundMappings().pop(rowSelected)
            self.BeamSettings.markDirty()
            self.BuildArtistBackgroundList()
            self.updateSettings()
    
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

    def OnCheckArtistBackground(self, event):
        mappings = self.BeamSettings.getArtistBackgroundMappings()
        for i in range(0, len(mappings)):
            mappings[i]['Active'] = 'yes' if self.ArtistBackgroundList.IsChecked(i) else 'no'
        self.BeamSettings.markDirty()
        self.BuildArtistBackgroundList()
        self.updateSettings()

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

    def BuildArtistBackgroundList(self):
        self.artistBackgroundRows = []
        mappings = self.BeamSettings.getArtistBackgroundMappings()
        for mapping in mappings:
            name = str(mapping.get('Name', 'Artist background'))
            field_name = str(mapping.get('Field', '%AlbumArtist'))
            operator = str(mapping.get('Operator', 'is'))
            value = str(mapping.get('Value', ''))
            mode = str(mapping.get('Mode', 'blend'))
            row = name + ' | ' + field_name + ' ' + operator + ' ' + value
            if mode == 'blend':
                row += ' | blend ' + str(mapping.get('Opacity', 35)) + '%'
            else:
                row += ' | ' + mode
            self.artistBackgroundRows.append(row)

        self.ArtistBackgroundList.Set(self.artistBackgroundRows)
        for i in range(0, len(mappings)):
            if str(mappings[i].get('Active', 'yes')).lower() == 'yes':
                self.ArtistBackgroundList.Check(i, check=True)
            else:
                self.ArtistBackgroundList.Check(i, check=False)
