#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

import wx

from bin.backgroundassets import import_background_asset, resolve_background_reference, to_persisted_background_reference
from bin.beamsettings import beamSettings
from bin.dialogs.preferencespanels.timercombobox import TimerComboBox


BACKGROUND_FILE_WILDCARD = "Image files(*.png,*.jpg)|*.png;*.jpg"
BACKGROUND_EXTENSIONS = ('.jpg', '.jpeg', '.png')
MAPPING_FIELDS = ["%AlbumArtist", "%Artist", "%Performer", "%Genre", "%Comment", "%Composer", "%Year", "%Album", "%Title"]
MAPPING_OPERATORS = ["is", "is not", "contains"]
MAPPING_MODES = ["blend", "replace", "off"]


def _get_background_picker_path(background_reference):
    resolved_background = resolve_background_reference(background_reference)
    return resolved_background['absolutePath'] or str(background_reference or '')


def _get_background_label_path(background_reference):
    resolved_background = resolve_background_reference(background_reference)
    return resolved_background['absolutePath'] or resolved_background['relativePath'] or str(background_reference or '')


class EditArtistBackgroundDialog(wx.Dialog):
    def __init__(self, moodsPanel, rowSelected, mode):
        xpos, ypos = moodsPanel.GetScreenPosition()
        wx.Dialog.__init__(self, moodsPanel, title=mode, pos=(xpos + 50, ypos + 50), size=(520, 520))

        self.moodsPanel = moodsPanel
        self.rowSelected = rowSelected
        self.mode = mode
        self.mapping = {}

        mappings = beamSettings.getArtistBackgroundMappings()
        if self.rowSelected < len(mappings):
            self.mapping = dict(mappings[self.rowSelected])
        else:
            self.mapping = {
                'Name': 'New artist background',
                'Field': '%AlbumArtist',
                'Operator': 'is',
                'Value': '',
                'Background': '',
                'Mode': 'blend',
                'Opacity': 35,
                'RotateBackground': 'no',
                'RotateTimer': 120,
                'Active': 'yes',
            }

        panel = wx.Panel(self)
        font = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD)

        title = wx.StaticText(panel, wx.ID_ANY, "Artist Background Mapping")
        title.SetFont(font)

        self.NameField = wx.TextCtrl(panel, value=self.mapping.get('Name', ''), size=(260, -1))
        self.ActiveCheckbox = wx.CheckBox(panel, label='Active')
        self.ActiveCheckbox.SetValue(str(self.mapping.get('Active', 'yes')).lower() == 'yes')
        self.FieldDropdown = wx.ComboBox(panel, value=self.mapping.get('Field', '%AlbumArtist'), choices=MAPPING_FIELDS, style=wx.CB_READONLY)
        self.OperatorDropdown = wx.ComboBox(panel, value=self.mapping.get('Operator', 'is'), choices=MAPPING_OPERATORS, style=wx.CB_READONLY)
        self.ValueField = wx.TextCtrl(panel, value=self.mapping.get('Value', ''), size=(260, -1))
        self.ModeDropdown = wx.ComboBox(panel, value=self.mapping.get('Mode', 'blend'), choices=MAPPING_MODES, style=wx.CB_READONLY)
        self.ModeDropdown.Bind(wx.EVT_COMBOBOX, self.OnModeChanged)

        self.OpacitySlider = wx.Slider(panel, value=int(self.mapping.get('Opacity', 35)), minValue=0, maxValue=100, size=(220, -1), style=wx.SL_HORIZONTAL)
        self.OpacitySlider.Bind(wx.EVT_SCROLL, self.OnOpacityChanged)
        self.OpacityLabel = wx.StaticText(panel, wx.ID_ANY, "")

        self.BackgroundBrowseButton = wx.Button(panel, label='Browse')
        self.BackgroundBrowseButton.Bind(wx.EVT_BUTTON, self.OnBrowseBackground)
        self.CurrentBackground = wx.StaticText(panel, wx.ID_ANY, "")

        self.RotateBackgroundBox = wx.CheckBox(panel, label='Rotate background folder')
        self.RotateBackgroundBox.Bind(wx.EVT_CHECKBOX, self.OnRotateChanged)
        self.RandomBackgroundBox = wx.CheckBox(panel, label='Random order')
        self.RandomBackgroundBox.Bind(wx.EVT_CHECKBOX, self.OnRotateChanged)
        self.BackgroundTimerBox = TimerComboBox(panel)
        self.BackgroundTimerBox.Bind(wx.EVT_COMBOBOX, self.OnRotateChanged)
        self.BackgroundTimerBox.setTimeSelection(int(self.mapping.get('RotateTimer', 120)))

        self.OrderField = wx.SpinCtrl(panel, value=str(min(self.rowSelected + 1, len(mappings) + 1)), min=1, max=max(1, len(mappings) + 1))

        infoGrid = wx.FlexGridSizer(0, 2, 8, 12)
        infoGrid.AddGrowableCol(1, 1)
        infoGrid.Add(wx.StaticText(panel, wx.ID_ANY, 'Name'), 0, wx.ALIGN_CENTER_VERTICAL)
        infoGrid.Add(self.NameField, 0, wx.EXPAND)
        infoGrid.Add(wx.StaticText(panel, wx.ID_ANY, 'Active'), 0, wx.ALIGN_CENTER_VERTICAL)
        infoGrid.Add(self.ActiveCheckbox, 0, wx.EXPAND)
        infoGrid.Add(wx.StaticText(panel, wx.ID_ANY, 'Match field'), 0, wx.ALIGN_CENTER_VERTICAL)
        infoGrid.Add(self.FieldDropdown, 0, wx.EXPAND)
        infoGrid.Add(wx.StaticText(panel, wx.ID_ANY, 'Operator'), 0, wx.ALIGN_CENTER_VERTICAL)
        infoGrid.Add(self.OperatorDropdown, 0, wx.EXPAND)
        infoGrid.Add(wx.StaticText(panel, wx.ID_ANY, 'Value'), 0, wx.ALIGN_CENTER_VERTICAL)
        infoGrid.Add(self.ValueField, 0, wx.EXPAND)
        infoGrid.Add(wx.StaticText(panel, wx.ID_ANY, 'Mode'), 0, wx.ALIGN_CENTER_VERTICAL)
        infoGrid.Add(self.ModeDropdown, 0, wx.EXPAND)

        opacitySizer = wx.BoxSizer(wx.HORIZONTAL)
        opacitySizer.Add(self.OpacitySlider, flag=wx.RIGHT, border=10)
        opacitySizer.Add(self.OpacityLabel, flag=wx.ALIGN_CENTER_VERTICAL)
        infoGrid.Add(wx.StaticText(panel, wx.ID_ANY, 'Opacity'), 0, wx.ALIGN_CENTER_VERTICAL)
        infoGrid.Add(opacitySizer, 0, wx.EXPAND)

        backgroundSizer = wx.BoxSizer(wx.HORIZONTAL)
        backgroundSizer.Add(self.BackgroundBrowseButton, flag=wx.RIGHT, border=10)
        backgroundSizer.Add(self.CurrentBackground, proportion=1, flag=wx.ALIGN_CENTER_VERTICAL)
        infoGrid.Add(wx.StaticText(panel, wx.ID_ANY, 'Background'), 0, wx.ALIGN_CENTER_VERTICAL)
        infoGrid.Add(backgroundSizer, 0, wx.EXPAND)

        rotateSizer = wx.BoxSizer(wx.VERTICAL)
        rotateRow = wx.BoxSizer(wx.HORIZONTAL)
        rotateRow.Add(self.RotateBackgroundBox, flag=wx.RIGHT, border=10)
        rotateRow.Add(self.BackgroundTimerBox)
        rotateSizer.Add(rotateRow, flag=wx.BOTTOM, border=5)
        rotateSizer.Add(self.RandomBackgroundBox)
        infoGrid.Add(wx.StaticText(panel, wx.ID_ANY, 'Rotation'), 0, wx.ALIGN_TOP)
        infoGrid.Add(rotateSizer, 0, wx.EXPAND)

        infoGrid.Add(wx.StaticText(panel, wx.ID_ANY, 'Order'), 0, wx.ALIGN_CENTER_VERTICAL)
        infoGrid.Add(self.OrderField, 0, wx.EXPAND)

        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        okButton = wx.Button(panel, wx.ID_OK, 'OK')
        okButton.Bind(wx.EVT_BUTTON, self.OnOk)
        cancelButton = wx.Button(panel, wx.ID_CANCEL, 'Cancel')
        buttonSizer.Add(okButton, flag=wx.RIGHT, border=10)
        buttonSizer.Add(cancelButton)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(title, flag=wx.LEFT | wx.TOP, border=10)
        sizer.Add(infoGrid, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)
        sizer.Add(buttonSizer, flag=wx.ALIGN_RIGHT | wx.ALL, border=10)
        panel.SetSizer(sizer)

        rotate_value = str(self.mapping.get('RotateBackground', 'no')).lower()
        self.RotateBackgroundBox.SetValue(rotate_value in ('linear', 'random'))
        self.RandomBackgroundBox.SetValue(rotate_value == 'random')

        self.OnOpacityChanged(None)
        self.updateBackgroundLabel()
        self.updateRotateControls()
        self.updateModeControls()

    def updateBackgroundLabel(self):
        label_path = _get_background_label_path(self.mapping.get('Background', ''))
        if label_path == '':
            self.CurrentBackground.SetLabel('No background selected')
            return

        path, backgroundfile = os.path.split(os.path.normpath(label_path))
        if self.RotateBackgroundBox.IsChecked() and os.path.splitext(backgroundfile)[1].lower() in BACKGROUND_EXTENSIONS:
            backgroundfile = os.path.split(path)[1]
        self.CurrentBackground.SetLabel(backgroundfile or label_path)

    def updateRotateControls(self):
        rotating = self.RotateBackgroundBox.IsChecked()
        self.RandomBackgroundBox.Enable(rotating)
        self.BackgroundTimerBox.Enable(rotating)
        if not rotating:
            self.RandomBackgroundBox.SetValue(False)

    def updateModeControls(self):
        mode = self.ModeDropdown.GetValue()
        enable_opacity = mode == 'blend'
        self.OpacitySlider.Enable(enable_opacity)
        self.OpacityLabel.Enable(enable_opacity)

    def OnOpacityChanged(self, event):
        self.OpacityLabel.SetLabel(str(self.OpacitySlider.GetValue()) + '%')

    def OnModeChanged(self, event):
        self.updateModeControls()

    def OnRotateChanged(self, event):
        self.updateRotateControls()
        self.updateBackgroundLabel()

    def OnBrowseBackground(self, event):
        background_path = _get_background_picker_path(self.mapping.get('Background', ''))
        if self.RotateBackgroundBox.IsChecked():
            dialog_directory = background_path
            if os.path.splitext(os.path.basename(background_path))[1].lower() in BACKGROUND_EXTENSIONS:
                dialog_directory = os.path.dirname(background_path)
            open_dialog = wx.DirDialog(self, 'Select background folder', dialog_directory, wx.DD_DIR_MUST_EXIST)
        else:
            dialog_directory, dialog_file = os.path.split(background_path)
            open_dialog = wx.FileDialog(
                self,
                'Set artist background image',
                dialog_directory,
                dialog_file,
                BACKGROUND_FILE_WILDCARD,
                wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
            )

        try:
            if open_dialog.ShowModal() != wx.ID_OK:
                return

            selected_path = open_dialog.GetPath()
            persisted_reference = to_persisted_background_reference(selected_path, 'orchestras')
            if persisted_reference is None:
                message = (
                    "Copy the selected background into Beam's managed orchestra background library?\n\n"
                    "Yes: import into ~/.beam/backgrounds/orchestras\n"
                    "No: keep an unmanaged external path\n"
                    "Cancel: keep the current background"
                )
                decision_dialog = wx.MessageDialog(self, message, 'Import background', wx.YES_NO | wx.CANCEL | wx.ICON_QUESTION)
                try:
                    decision = decision_dialog.ShowModal()
                finally:
                    decision_dialog.Destroy()

                if decision == wx.ID_CANCEL:
                    return
                if decision == wx.ID_YES:
                    import_result = import_background_asset(selected_path, 'orchestras')
                    if import_result['status'] == 'failed':
                        error_dialog = wx.MessageDialog(self, import_result['message'], 'Background import failed', wx.OK | wx.ICON_ERROR)
                        try:
                            error_dialog.ShowModal()
                        finally:
                            error_dialog.Destroy()
                        return
                    persisted_reference = import_result['reference']
                else:
                    persisted_reference = os.path.normpath(selected_path)

            self.mapping['Background'] = persisted_reference
            self.updateBackgroundLabel()
        finally:
            open_dialog.Destroy()

    def OnOk(self, event):
        mappings = beamSettings.getArtistBackgroundMappings()
        self.mapping['Name'] = self.NameField.GetValue().strip() or 'Artist background'
        self.mapping['Field'] = self.FieldDropdown.GetValue()
        self.mapping['Operator'] = self.OperatorDropdown.GetValue()
        self.mapping['Value'] = self.ValueField.GetValue().strip()
        self.mapping['Mode'] = self.ModeDropdown.GetValue()
        self.mapping['Opacity'] = int(self.OpacitySlider.GetValue())
        self.mapping['RotateBackground'] = 'no'
        if self.RotateBackgroundBox.IsChecked() and self.RandomBackgroundBox.IsChecked():
            self.mapping['RotateBackground'] = 'random'
        elif self.RotateBackgroundBox.IsChecked():
            self.mapping['RotateBackground'] = 'linear'
        self.mapping['RotateTimer'] = self.BackgroundTimerBox.getTimeSelection()
        self.mapping['Active'] = 'yes' if self.ActiveCheckbox.GetValue() else 'no'

        insert_index = int(self.OrderField.GetValue()) - 1
        insert_index = max(0, min(insert_index, len(mappings)))
        if self.rowSelected < len(mappings):
            mappings.pop(self.rowSelected)
            if insert_index > self.rowSelected:
                insert_index -= 1
        mappings.insert(insert_index, dict(self.mapping))

        beamSettings.markDirty()
        self.moodsPanel.BuildArtistBackgroundList()
        self.moodsPanel.updateSettings()
        self.Destroy()