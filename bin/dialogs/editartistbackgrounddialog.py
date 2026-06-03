#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

import wx

from bin.backgroundassets import import_background_asset, resolve_background_reference, to_persisted_background_reference
from bin.beamsettings import beamSettings


BACKGROUND_FILE_WILDCARD = "Image files(*.png,*.jpg)|*.png;*.jpg"
BACKGROUND_EXTENSIONS = ('.jpg', '.jpeg', '.png')
MAPPING_FIELDS = ["%AlbumArtist", "%Artist", "%Performer", "%Genre", "%Comment", "%Composer", "%Year", "%Album", "%Title"]
MAPPING_OPERATORS = ["is", "is not", "contains"]
MAPPING_MODES = ["blend", "replace", "off"]

# Background type selector, aligned with the mood editor's background UI. Artist
# backgrounds only need an image source (no "Keep existing"/"Color" mood types),
# so the choices are a single image or a rotating folder slideshow.
BACKGROUND_TYPE_LABELS = ["Single image", "Image slideshow"]
BACKGROUND_TYPE_IMAGE = 0
BACKGROUND_TYPE_SLIDESHOW = 1

# "Change image every" options and the seconds they map to (index aligned),
# matching the mood editor's slideshow interval choices.
SLIDESHOW_INTERVAL_LABELS = ['Every 15 seconds', 'Every 30 seconds', 'Every 1 minute',
                            'Every 2 minutes', 'Every 3 minutes', 'Every 5 minutes',
                            'Every 10 minutes', 'Every 20 minutes']
SLIDESHOW_INTERVAL_SECONDS = [15, 30, 60, 120, 180, 300, 600, 1200]
SLIDESHOW_DEFAULT_INTERVAL_INDEX = 3  # 120 seconds (the prior artist-background default)


def _get_background_picker_path(background_reference):
    resolved_background = resolve_background_reference(background_reference)
    return resolved_background['absolutePath'] or str(background_reference or '')


def _get_background_label_path(background_reference):
    resolved_background = resolve_background_reference(background_reference)
    return resolved_background['absolutePath'] or resolved_background['relativePath'] or str(background_reference or '')


class EditArtistBackgroundDialog(wx.Dialog):
    def __init__(self, moodsPanel, rowSelected, mode):
        xpos, ypos = moodsPanel.GetScreenPosition()
        wx.Dialog.__init__(self, moodsPanel, title=mode, pos=(xpos + 50, ypos + 50), size=(520, 560))

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
        self.panel = panel
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

        self.OrderField = wx.SpinCtrl(panel, value=str(min(self.rowSelected + 1, len(mappings) + 1)), min=1, max=max(1, len(mappings) + 1))

        infoGrid = wx.FlexGridSizer(0, 2, 8, 12)
        infoGrid.AddGrowableCol(1, 1)
        infoGrid.Add(wx.StaticText(panel, wx.ID_ANY, 'Name'), 0, wx.ALIGN_CENTER_VERTICAL)
        infoGrid.Add(self.NameField, 0, wx.EXPAND)
        # Active: empty label column so the only "Active" text is the checkbox's own
        # label. No wx.EXPAND on the checkbox: stretching it triggers a GTK
        # negative-size assertion ("gtk_box_gadget_distribute: 'size >= 0' failed").
        infoGrid.Add(wx.StaticText(panel, wx.ID_ANY, ''), 0, wx.ALIGN_CENTER_VERTICAL)
        infoGrid.Add(self.ActiveCheckbox, 0, wx.ALIGN_CENTER_VERTICAL)
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

        infoGrid.Add(wx.StaticText(panel, wx.ID_ANY, 'Order'), 0, wx.ALIGN_CENTER_VERTICAL)
        infoGrid.Add(self.OrderField, 0, wx.EXPAND)

        # Background: a type dropdown that reveals only the controls for the chosen
        # type, matching the mood editor's background section.
        background_box = wx.StaticBoxSizer(wx.VERTICAL, panel, "Background")
        type_row = wx.BoxSizer(wx.HORIZONTAL)
        self.BackgroundTypeChoice = wx.ComboBox(panel, choices=BACKGROUND_TYPE_LABELS, style=wx.CB_READONLY)
        self.BackgroundTypeChoice.Bind(wx.EVT_COMBOBOX, self.OnBackgroundTypeChanged)
        type_row.Add(self.BackgroundTypeChoice, proportion=1, flag=wx.ALIGN_CENTER_VERTICAL)
        background_box.Add(type_row, flag=wx.EXPAND | wx.ALL, border=10)

        # --- Single image: Browse image ---
        image_panel = wx.Panel(panel)
        self.BackgroundBrowseButton = wx.Button(image_panel, label='Browse image...')
        self.BackgroundBrowseButton.Bind(wx.EVT_BUTTON, self.OnBrowseImage)
        self.CurrentBackground = wx.StaticText(image_panel, wx.ID_ANY, "")
        image_sizer = wx.BoxSizer(wx.HORIZONTAL)
        image_sizer.Add(self.BackgroundBrowseButton, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=10)
        image_sizer.Add(self.CurrentBackground, proportion=1, flag=wx.ALIGN_CENTER_VERTICAL)
        image_panel.SetSizer(image_sizer)

        # --- Image slideshow: folder + interval + random order ---
        slideshow_panel = wx.Panel(panel)
        self.ChooseFolderButton = wx.Button(slideshow_panel, label='Choose folder...')
        self.ChooseFolderButton.Bind(wx.EVT_BUTTON, self.OnChooseFolder)
        self.currentFolderLabel = wx.StaticText(slideshow_panel, wx.ID_ANY, "")
        self.BackgroundTimerBox = wx.ComboBox(slideshow_panel, choices=SLIDESHOW_INTERVAL_LABELS, style=wx.CB_READONLY)
        self.BackgroundTimerBox.Bind(wx.EVT_COMBOBOX, self.OnSlideshowChanged)
        self.RandomBackgroundBox = wx.CheckBox(slideshow_panel, label='Random order')
        self.RandomBackgroundBox.Bind(wx.EVT_CHECKBOX, self.OnSlideshowChanged)
        slideshow_sizer = wx.BoxSizer(wx.VERTICAL)
        folder_row = wx.BoxSizer(wx.HORIZONTAL)
        folder_row.Add(self.ChooseFolderButton, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=10)
        folder_row.Add(self.currentFolderLabel, proportion=1, flag=wx.ALIGN_CENTER_VERTICAL)
        slideshow_sizer.Add(folder_row, flag=wx.EXPAND)
        interval_row = wx.BoxSizer(wx.HORIZONTAL)
        interval_row.Add(wx.StaticText(slideshow_panel, wx.ID_ANY, "Change image every:"), flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=10)
        interval_row.Add(self.BackgroundTimerBox, flag=wx.ALIGN_CENTER_VERTICAL)
        slideshow_sizer.Add(interval_row, flag=wx.TOP, border=8)
        slideshow_sizer.Add(self.RandomBackgroundBox, flag=wx.TOP, border=8)
        slideshow_panel.SetSizer(slideshow_sizer)

        # Panels indexed to match BACKGROUND_TYPE_*; only the selected one is shown.
        self._background_option_panels = [image_panel, slideshow_panel]
        for option_panel in self._background_option_panels:
            background_box.Add(option_panel, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=10)

        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        okButton = wx.Button(panel, wx.ID_OK, 'OK')
        okButton.Bind(wx.EVT_BUTTON, self.OnOk)
        cancelButton = wx.Button(panel, wx.ID_CANCEL, 'Cancel')
        buttonSizer.Add(okButton, flag=wx.RIGHT, border=10)
        buttonSizer.Add(cancelButton)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(title, flag=wx.LEFT | wx.TOP, border=10)
        sizer.Add(infoGrid, proportion=0, flag=wx.EXPAND | wx.ALL, border=10)
        sizer.Add(background_box, proportion=1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)
        sizer.Add(buttonSizer, flag=wx.ALIGN_RIGHT | wx.ALL, border=10)
        panel.SetSizer(sizer)

        self._set_selected_background_type(self._resolve_initial_background_type())
        self.OnOpacityChanged(None)
        self.updateModeControls()
        self._update_background_controls_state()

    #
    # BACKGROUND TYPE ("Single image" / "Image slideshow")
    #
    def _resolve_initial_background_type(self):
        rotate = str(self.mapping.get('RotateBackground', 'no')).strip().lower()
        if rotate in ('linear', 'random'):
            return BACKGROUND_TYPE_SLIDESHOW
        return BACKGROUND_TYPE_IMAGE

    def _get_selected_background_type(self):
        selection = self.BackgroundTypeChoice.GetSelection()
        return selection if selection >= 0 else BACKGROUND_TYPE_IMAGE

    def _set_selected_background_type(self, type_index):
        type_index = max(0, min(len(BACKGROUND_TYPE_LABELS) - 1, int(type_index)))
        self.BackgroundTypeChoice.SetSelection(type_index)

    def _update_background_controls_state(self):
        # Show only the controls for the selected background type, then reflow.
        selection = self._get_selected_background_type()
        for type_index, option_panel in enumerate(self._background_option_panels):
            option_panel.Show(type_index == selection)
        self._update_background_labels()
        self.panel.Layout()
        self.panel.Refresh()

    def OnBackgroundTypeChanged(self, event):
        if self._get_selected_background_type() != BACKGROUND_TYPE_SLIDESHOW:
            self.mapping['RotateBackground'] = 'no'
        self._update_background_controls_state()

    def _apply_slideshow_rotation_from_controls(self):
        self.mapping['RotateBackground'] = 'random' if self.RandomBackgroundBox.IsChecked() else 'linear'
        interval_index = self.BackgroundTimerBox.GetSelection()
        if interval_index < 0:
            interval_index = SLIDESHOW_DEFAULT_INTERVAL_INDEX
        self.mapping['RotateTimer'] = SLIDESHOW_INTERVAL_SECONDS[interval_index]

    def OnSlideshowChanged(self, event):
        self._apply_slideshow_rotation_from_controls()
        self._update_background_labels()
        event.Skip()

    def _update_background_labels(self):
        # Reflect the stored interval / random order and the image / folder names.
        try:
            interval_index = SLIDESHOW_INTERVAL_SECONDS.index(int(self.mapping.get('RotateTimer', 120)))
        except (ValueError, TypeError):
            interval_index = SLIDESHOW_DEFAULT_INTERVAL_INDEX
        self.BackgroundTimerBox.SetSelection(interval_index)
        self.RandomBackgroundBox.SetValue(str(self.mapping.get('RotateBackground', 'no')).strip().lower() == 'random')

        label_path = _get_background_label_path(self.mapping.get('Background', ''))
        if label_path == '':
            self.CurrentBackground.SetLabel('No image selected')
            self.currentFolderLabel.SetLabel('No folder selected')
            return

        parent_path, background_file = os.path.split(os.path.normpath(label_path))
        is_image_file = os.path.splitext(background_file)[1].lower() in BACKGROUND_EXTENSIONS
        self.CurrentBackground.SetLabel(background_file if is_image_file else label_path)
        # For a file the slideshow folder is its parent; for a folder it is the folder itself.
        self.currentFolderLabel.SetLabel(os.path.split(parent_path)[1] if is_image_file else background_file)

    def updateModeControls(self):
        mode = self.ModeDropdown.GetValue()
        enable_opacity = mode == 'blend'
        self.OpacitySlider.Enable(enable_opacity)
        self.OpacityLabel.Enable(enable_opacity)

    def OnOpacityChanged(self, event):
        self.OpacityLabel.SetLabel(str(self.OpacitySlider.GetValue()) + '%')

    def OnModeChanged(self, event):
        self.updateModeControls()

    def _persist_background_selection(self, selected_path):
        # Import into Beam's managed orchestra library, or keep the external path.
        # Returns the reference to store, or None if the user cancelled.
        persisted_reference = to_persisted_background_reference(selected_path, 'orchestras')
        if persisted_reference is not None:
            return persisted_reference

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
            return None
        if decision == wx.ID_YES:
            import_result = import_background_asset(selected_path, 'orchestras')
            if import_result['status'] == 'failed':
                error_dialog = wx.MessageDialog(self, import_result['message'], 'Background import failed', wx.OK | wx.ICON_ERROR)
                try:
                    error_dialog.ShowModal()
                finally:
                    error_dialog.Destroy()
                return None
            return import_result['reference']
        return os.path.normpath(selected_path)

    def OnBrowseImage(self, event):
        # "Single image" type: pick one image file (no rotation).
        background_path = _get_background_picker_path(self.mapping.get('Background', ''))
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
            persisted_reference = self._persist_background_selection(open_dialog.GetPath())
            if persisted_reference is None:
                return
            self.mapping['Background'] = persisted_reference
            self.mapping['RotateBackground'] = 'no'
            self._set_selected_background_type(BACKGROUND_TYPE_IMAGE)
            self._update_background_controls_state()
        finally:
            open_dialog.Destroy()

    def OnChooseFolder(self, event):
        # "Image slideshow" type: pick a folder and rotate through its images.
        background_path = _get_background_picker_path(self.mapping.get('Background', ''))
        dialog_directory = background_path
        if os.path.splitext(os.path.basename(background_path))[1].lower() in BACKGROUND_EXTENSIONS:
            dialog_directory = os.path.dirname(background_path)
        open_dialog = wx.DirDialog(self, 'Select background folder', dialog_directory, wx.DD_DIR_MUST_EXIST)
        try:
            if open_dialog.ShowModal() != wx.ID_OK:
                return
            persisted_reference = self._persist_background_selection(open_dialog.GetPath())
            if persisted_reference is None:
                return
            self.mapping['Background'] = persisted_reference
            self._set_selected_background_type(BACKGROUND_TYPE_SLIDESHOW)
            self._apply_slideshow_rotation_from_controls()
            self._update_background_controls_state()
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
        if self._get_selected_background_type() == BACKGROUND_TYPE_SLIDESHOW:
            self.mapping['RotateBackground'] = 'random' if self.RandomBackgroundBox.IsChecked() else 'linear'
        interval_index = self.BackgroundTimerBox.GetSelection()
        if interval_index < 0:
            interval_index = SLIDESHOW_DEFAULT_INTERVAL_INDEX
        self.mapping['RotateTimer'] = SLIDESHOW_INTERVAL_SECONDS[interval_index]
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
        if hasattr(self.moodsPanel, 'applyCommittedSettings'):
            self.moodsPanel.applyCommittedSettings()
        else:
            self.moodsPanel.updateSettings()
        self.Destroy()
