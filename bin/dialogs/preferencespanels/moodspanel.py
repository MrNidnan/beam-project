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
from copy import deepcopy
from bin.beamutils import normalizeMacControlHeight
from bin.dialogs.editartistbackgrounddialog import ArtistBackgroundEditorPanel, create_default_artist_background_mapping
from bin.dialogs.editmooddialog import MoodEditorPanel

#
# Panel with a Moods / Artist Backgrounds tab pane on the left and an embedded
# editor for the selected item on the right. Selecting an item opens its
# editor; changing the selection saves the currently open editor first.
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
        self._preview_debounce = None
        self._currentEditor = None
        font = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        self.matchFields = ["%AlbumArtist", "%Artist", "%Performer"]

        self.notebook = wx.Notebook(self)
        moodsTab = wx.Panel(self.notebook)
        artistTab = wx.Panel(self.notebook)

        #############
        # MOODS TAB #
        #############
        moodsDescription = wx.StaticText(moodsTab, -1, "A Mood changes the layout and background for some songs.\nMoods can be activated and deactivated with the check box.\nSelect a mood to edit it on the right.")
        moodsDescription.Wrap(200)
        moodtransition = wx.StaticText(moodsTab, -1, "Mood Transition")
        moodtransition.SetFont(font)
        self.TransitionDropdown = normalizeMacControlHeight(wx.ComboBox(moodsTab, value=self.BeamSettings.getMoodTransition(), choices=['No transition', 'Fade directly','Fade to black'], style=wx.CB_READONLY))
        self.TransitionSpeed = wx.Slider(moodsTab, -1, int(self.BeamSettings.getMoodTransitionSpeed()), 500, 5000,(0,0), (130,-1), wx.SL_HORIZONTAL)
        self.TransitionSpeedLabel = wx.StaticText(moodsTab, -1, "")
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
        self.MoodList = wx.CheckListBox(moodsTab,-1, size=wx.Size(150, 180), choices=self.MoodRows, style= wx.LB_NEEDED_SB)
        bgcolour = self.MoodList.GetBackgroundColour()
        logging.debug("... bgcolour: " + str(bgcolour))
        bgcolour_rgba = (bgcolour.Red(), bgcolour.Green(), bgcolour.Blue(), bgcolour.Alpha())
        fgcolour = tuple(numpy.subtract((255,255,255,510), bgcolour_rgba))
        logging.debug("... fgcolour: " + str(fgcolour))
        self.MoodList.SetForegroundColour(wx.Colour(*fgcolour[:3]))
        self.MoodList.Bind(wx.EVT_LISTBOX, self.OnMoodSelected)
        self.MoodList.Bind(wx.EVT_CHECKLISTBOX, self.OnCheckMood)
        # List all configured moods
        self.BuildMoodList()

        ################
        # MOOD BUTTONS #
        ################
        self.AddMoodButton    = wx.Button(moodsTab, label="Add")
        self.DelMoodButton    = wx.Button(moodsTab, label="Delete")
        self.AddMoodButton.Bind(wx.EVT_BUTTON, self.OnAddMood)
        self.DelMoodButton.Bind(wx.EVT_BUTTON, self.OnDelMood)
        sizerbuttons    = wx.BoxSizer(wx.HORIZONTAL)
        sizerbuttons.Add(self.AddMoodButton, flag=wx.RIGHT | wx.TOP, border=10)
        sizerbuttons.Add(self.DelMoodButton, flag=wx.RIGHT | wx.TOP, border=10)

        moodsTabSizer = wx.BoxSizer(wx.VERTICAL)
        moodsTabSizer.Add(moodsDescription, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        moodsTabSizer.Add(moodtransition, flag=wx.LEFT | wx.TOP, border=10)
        moodsTabSizer.Add(hboxTransition, flag=wx.LEFT | wx.RIGHT, border=20)
        moodsTabSizer.Add(self.MoodList, proportion=1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        moodsTabSizer.Add(sizerbuttons, flag=wx.LEFT | wx.BOTTOM, border=10)
        moodsTab.SetSizer(moodsTabSizer)

        ##########################
        # ARTIST BACKGROUNDS TAB #
        ##########################
        artistBackgroundDescription = wx.StaticText(
            artistTab,
            -1,
            "Artist backgrounds add an optional orchestra/artist image layer on top of the mood background. Select a mapping to edit it on the right.",
        )
        artistBackgroundDescription.Wrap(200)

        artistBackgrounds = self.BeamSettings.getArtistBackgrounds()
        self.EnableArtistBackgrounds = wx.CheckBox(artistTab, label='Enable artist backgrounds')
        self.EnableArtistBackgrounds.SetValue(str(artistBackgrounds.get('Enabled', 'False')).lower() == 'true')
        self.EnableArtistBackgrounds.Bind(wx.EVT_CHECKBOX, self.OnArtistBackgroundSettingsChanged)
        self.UseCoverArtBackgrounds = wx.CheckBox(artistTab, label='Use cover art / album art')
        self.UseCoverArtBackgrounds.SetValue(str(artistBackgrounds.get('UseCoverArt', 'False')).lower() == 'true')
        self.UseCoverArtBackgrounds.Bind(wx.EVT_CHECKBOX, self.OnArtistBackgroundSettingsChanged)

        self.MatchFieldDropdown = normalizeMacControlHeight(wx.ComboBox(artistTab, value=artistBackgrounds.get('MatchField', '%AlbumArtist'), choices=self.matchFields, style=wx.CB_READONLY))
        self.MatchFieldDropdown.Bind(wx.EVT_COMBOBOX, self.OnArtistBackgroundSettingsChanged)
        self.FallbackFieldDropdown = normalizeMacControlHeight(wx.ComboBox(artistTab, value=artistBackgrounds.get('FallbackField', '%Artist'), choices=self.matchFields, style=wx.CB_READONLY))
        self.FallbackFieldDropdown.Bind(wx.EVT_COMBOBOX, self.OnArtistBackgroundSettingsChanged)
        self.DefaultModeDropdown = normalizeMacControlHeight(wx.ComboBox(artistTab, value=artistBackgrounds.get('DefaultMode', 'blend'), choices=['blend', 'replace', 'off'], style=wx.CB_READONLY))
        self.DefaultModeDropdown.Bind(wx.EVT_COMBOBOX, self.OnArtistBackgroundSettingsChanged)
        self.DefaultOpacitySlider = wx.Slider(artistTab, -1, int(artistBackgrounds.get('DefaultOpacity', 35)), 0, 100, (0,0), (120,-1), wx.SL_HORIZONTAL)
        self.DefaultOpacitySlider.Bind(wx.EVT_SCROLL, self.OnArtistBackgroundSettingsChanged)
        self.DefaultOpacityLabel = wx.StaticText(artistTab, -1, '')

        artistSettingsGrid = wx.FlexGridSizer(0, 2, 5, 10)
        artistSettingsGrid.AddGrowableCol(1, 1)
        artistSettingsGrid.Add(self.EnableArtistBackgrounds, 0, wx.ALIGN_CENTER_VERTICAL)
        artistSettingsGrid.Add(wx.StaticText(artistTab, -1, ''))
        artistSettingsGrid.Add(self.UseCoverArtBackgrounds, 0, wx.ALIGN_CENTER_VERTICAL)
        artistSettingsGrid.Add(wx.StaticText(artistTab, -1, ''))
        artistSettingsGrid.Add(wx.StaticText(artistTab, -1, 'Default match field'), 0, wx.ALIGN_CENTER_VERTICAL)
        artistSettingsGrid.Add(self.MatchFieldDropdown, 0, wx.EXPAND)
        artistSettingsGrid.Add(wx.StaticText(artistTab, -1, 'Fallback field'), 0, wx.ALIGN_CENTER_VERTICAL)
        artistSettingsGrid.Add(self.FallbackFieldDropdown, 0, wx.EXPAND)
        artistSettingsGrid.Add(wx.StaticText(artistTab, -1, 'Default mode'), 0, wx.ALIGN_CENTER_VERTICAL)
        artistSettingsGrid.Add(self.DefaultModeDropdown, 0, wx.EXPAND)
        opacitySizer = wx.BoxSizer(wx.HORIZONTAL)
        opacitySizer.Add(self.DefaultOpacitySlider, proportion=1, flag=wx.RIGHT, border=10)
        opacitySizer.Add(self.DefaultOpacityLabel, flag=wx.ALIGN_CENTER_VERTICAL)
        artistSettingsGrid.Add(wx.StaticText(artistTab, -1, 'Default opacity'), 0, wx.ALIGN_CENTER_VERTICAL)
        artistSettingsGrid.Add(opacitySizer, 0, wx.EXPAND)

        # Fixed size hint so long mapping labels don't widen the tab pane;
        # the list scrolls horizontally instead.
        self.ArtistBackgroundList = wx.CheckListBox(artistTab, -1, size=wx.Size(150, 180), choices=self.artistBackgroundRows, style=wx.LB_NEEDED_SB | wx.LB_HSCROLL)
        self.ArtistBackgroundList.Bind(wx.EVT_LISTBOX, self.OnArtistBackgroundSelected)
        self.ArtistBackgroundList.Bind(wx.EVT_CHECKLISTBOX, self.OnCheckArtistBackground)
        self.BuildArtistBackgroundList()

        self.AddArtistBackgroundButton = wx.Button(artistTab, label='Add')
        self.DelArtistBackgroundButton = wx.Button(artistTab, label='Delete')
        self.AddArtistBackgroundButton.Bind(wx.EVT_BUTTON, self.OnAddArtistBackground)
        self.DelArtistBackgroundButton.Bind(wx.EVT_BUTTON, self.OnDelArtistBackground)
        artistButtons = wx.BoxSizer(wx.HORIZONTAL)
        artistButtons.Add(self.AddArtistBackgroundButton, flag=wx.RIGHT | wx.TOP, border=10)
        artistButtons.Add(self.DelArtistBackgroundButton, flag=wx.RIGHT | wx.TOP, border=10)

        artistTabSizer = wx.BoxSizer(wx.VERTICAL)
        artistTabSizer.Add(artistBackgroundDescription, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        artistTabSizer.Add(artistSettingsGrid, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=20)
        artistTabSizer.Add(self.ArtistBackgroundList, proportion=1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        artistTabSizer.Add(artistButtons, flag=wx.LEFT | wx.BOTTOM, border=10)
        artistTab.SetSizer(artistTabSizer)

        self.notebook.AddPage(moodsTab, "Moods")
        self.notebook.AddPage(artistTab, "Artist Backgrounds")
        self.notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnTabChanged)

        #################
        # EDITOR COLUMN #
        #################
        self.editorContainer = wx.Panel(self)
        self.editorSizer = wx.BoxSizer(wx.VERTICAL)
        self.editorPlaceholder = wx.StaticText(self.editorContainer, -1, "Select a mood or artist background\nto edit it here.")
        self.editorSizer.Add(self.editorPlaceholder, flag=wx.ALL, border=20)
        self.editorContainer.SetSizer(self.editorSizer)

        ##############
        # SET SIZERS #
        ##############
        # Cap the tab pane width so the editor column gets the remaining
        # horizontal space; lists and descriptions scroll/wrap inside it.
        self.notebook.SetMaxSize(wx.Size(320, -1))
        columnsSizer = wx.BoxSizer(wx.HORIZONTAL)
        columnsSizer.Add(self.notebook, proportion=0, flag=wx.EXPAND | wx.RIGHT, border=10)
        columnsSizer.Add(self.editorContainer, proportion=1, flag=wx.EXPAND | wx.LEFT, border=10)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(columnsSizer, proportion=1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.TOP, border=10)
        self.SetSizer(sizer)
        self.updateArtistBackgroundControls()



    def updateSettings(self):
        if self._preview_debounce is not None:
            self._preview_debounce.Stop()
        self._preview_debounce = wx.CallLater(125, self._run_preview_update)

    def _run_preview_update(self):
        self._preview_debounce = None
        self.mainFrame.previewSettings()

    def applyCommittedSettings(self):
        if self._preview_debounce is not None:
            self._preview_debounce.Stop()
            self._preview_debounce = None
        if hasattr(self.mainFrame, '_persistDirtySettings'):
            self.mainFrame._persistDirtySettings()
        self.mainFrame.updateSettings(reload_preferences=False)

    def reloadFromSettings(self):
        # Settings were reloaded from disk; a live editor would point at stale
        # objects, so discard it instead of saving.
        self._close_editor(save=False)
        self.TransitionDropdown.SetValue(self.BeamSettings.getMoodTransition())
        self.TransitionSpeed.SetValue(int(self.BeamSettings.getMoodTransitionSpeed()))
        self.updateMoodTransition()
        self.BuildMoodList()
        artistBackgrounds = self.BeamSettings.getArtistBackgrounds()
        self.EnableArtistBackgrounds.SetValue(str(artistBackgrounds.get('Enabled', 'False')).lower() == 'true')
        self.UseCoverArtBackgrounds.SetValue(str(artistBackgrounds.get('UseCoverArt', 'False')).lower() == 'true')
        self.MatchFieldDropdown.SetValue(artistBackgrounds.get('MatchField', '%AlbumArtist'))
        self.FallbackFieldDropdown.SetValue(artistBackgrounds.get('FallbackField', '%Artist'))
        self.DefaultModeDropdown.SetValue(artistBackgrounds.get('DefaultMode', 'blend'))
        self.DefaultOpacitySlider.SetValue(int(artistBackgrounds.get('DefaultOpacity', 35)))
        self.updateArtistBackgroundControls()
        self.BuildArtistBackgroundList()

###################################################################
#                           EDITORS                               #
###################################################################

    def _close_editor(self, save=True):
        # Save (unless discarding) and remove the currently embedded editor.
        editor = self._currentEditor
        self._currentEditor = None
        if editor is not None and bool(editor):
            if save:
                editor.saveChanges()
            self.editorSizer.Detach(editor)
            editor.Destroy()
        if bool(self.editorPlaceholder):
            self.editorPlaceholder.Show()
        self.editorContainer.Layout()

    def _show_editor(self, editor):
        self.editorPlaceholder.Hide()
        self._currentEditor = editor
        self.editorSizer.Add(editor, 1, flag=wx.EXPAND)
        self.editorContainer.Layout()

    def _open_mood_editor(self, row):
        current = self._currentEditor
        if current is not None and bool(current) and isinstance(current, MoodEditorPanel) and current.RowSelected == row:
            return
        self._close_editor()
        if not (0 <= row < len(self.BeamSettings.getMoods())):
            return
        self._show_editor(MoodEditorPanel(self.editorContainer, self, row))
        if row < self.MoodList.GetCount():
            self.MoodList.SetSelection(row)

    def _open_artist_background_editor(self, row):
        current = self._currentEditor
        if current is not None and bool(current) and isinstance(current, ArtistBackgroundEditorPanel) and current.rowSelected == row:
            return
        self._close_editor()
        if not (0 <= row < len(self.BeamSettings.getArtistBackgroundMappings())):
            return
        self._show_editor(ArtistBackgroundEditorPanel(self.editorContainer, self, row))
        if row < self.ArtistBackgroundList.GetCount():
            self.ArtistBackgroundList.SetSelection(row)

    def _restore_editor_selection(self):
        # Rebuilding a CheckListBox clears its selection; restore the row of
        # the currently open editor so the list matches the editor column.
        editor = self._currentEditor
        if editor is None or not bool(editor):
            return
        if isinstance(editor, MoodEditorPanel):
            if 0 <= editor.RowSelected < self.MoodList.GetCount():
                self.MoodList.SetSelection(editor.RowSelected)
        elif isinstance(editor, ArtistBackgroundEditorPanel):
            if 0 <= editor.rowSelected < self.ArtistBackgroundList.GetCount():
                self.ArtistBackgroundList.SetSelection(editor.rowSelected)

    def OnTabChanged(self, event):
        # Switching between Moods and Artist Backgrounds saves the open editor.
        self._close_editor()
        event.Skip()

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
        self.UseCoverArtBackgrounds.Enable(enabled)
        self.MatchFieldDropdown.Enable(enabled)
        self.FallbackFieldDropdown.Enable(enabled)
        self.DefaultModeDropdown.Enable(enabled)
        self.DefaultOpacitySlider.Enable(enabled)
        self.DefaultOpacityLabel.Enable(enabled)

    def OnArtistBackgroundSettingsChanged(self, event):
        artistBackgrounds = self.BeamSettings.getArtistBackgrounds()
        artistBackgrounds['Enabled'] = 'True' if self.EnableArtistBackgrounds.GetValue() else 'False'
        artistBackgrounds['UseCoverArt'] = 'True' if self.UseCoverArtBackgrounds.GetValue() else 'False'
        artistBackgrounds['MatchField'] = self.MatchFieldDropdown.GetValue()
        artistBackgrounds['FallbackField'] = self.FallbackFieldDropdown.GetValue()
        artistBackgrounds['DefaultMode'] = self.DefaultModeDropdown.GetValue()
        artistBackgrounds['DefaultOpacity'] = int(self.DefaultOpacitySlider.GetValue())
        self.BeamSettings.markDirty()
        self.updateArtistBackgroundControls()
        self.updateSettings()



        ###################
        # LIST SELECTION  #
        ###################
    def OnMoodSelected(self, event):
        row = event.GetSelection()
        if row > -1:
            self._open_mood_editor(row)

    def OnArtistBackgroundSelected(self, event):
        row = event.GetSelection()
        if row > -1:
            self._open_artist_background_editor(row)

        ##################
        # LAYOUT BUTTONS #
        ##################
    def OnAddMood(self, event):
        self._close_editor()
        moods = self.BeamSettings.getMoods()
        newMood = deepcopy(moods[0])
        newMood['Name'] = "New Mood"
        newMood['Type'] = "Mood"
        moods.append(newMood)
        self.BeamSettings.markDirty()
        self.BuildMoodList()
        self._open_mood_editor(len(moods) - 1)

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
                # Discard the editor: row indexes shift after the removal.
                if isinstance(self._currentEditor, MoodEditorPanel):
                    self._close_editor(save=False)
                self.BeamSettings.getMoods().pop(selrow)
                self.BeamSettings.markDirty()
                # points to self.BeamSettings.getMoods()[x]
            # List all configured moods
            self.BuildMoodList()

    def OnAddArtistBackground(self, event):
        self._close_editor()
        mappings = self.BeamSettings.getArtistBackgroundMappings()
        mappings.append(create_default_artist_background_mapping())
        self.BeamSettings.markDirty()
        self.BuildArtistBackgroundList()
        self._open_artist_background_editor(len(mappings) - 1)

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
            # Discard the editor: row indexes shift after the removal.
            if isinstance(self._currentEditor, ArtistBackgroundEditorPanel):
                self._close_editor(save=False)
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
        self.applyCommittedSettings()

    def OnCheckArtistBackground(self, event):
        mappings = self.BeamSettings.getArtistBackgroundMappings()
        for i in range(0, len(mappings)):
            mappings[i]['Active'] = 'yes' if self.ArtistBackgroundList.IsChecked(i) else 'no'
        self.BeamSettings.markDirty()
        self.BuildArtistBackgroundList()
        self.applyCommittedSettings()

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
        self._restore_editor_selection()

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
        self._restore_editor_selection()
