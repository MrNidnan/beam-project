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
import wx.lib.colourselect as colourselect
import os
import platform

from bin.backgroundassets import import_background_asset, resolve_background_reference, to_persisted_background_reference
from bin.beamutils import normalizeMacControlHeight
from bin.DMX import dmxmodule
from bin.beamsettings import beamSettings
from bin.dialogs.editlayoutitemdialog import EditLayoutItemDialog
from copy import deepcopy


BACKGROUND_FILE_WILDCARD = "Image files(*.png,*.jpg)|*.png;*.jpg"
BACKGROUND_EXTENSIONS = ('.jpg', '.jpeg', '.png')

# Background mode selector. Order must match BACKGROUND_MODE_VALUES.
# "Keep existing" inherits the on-screen background and exposes the Readability
# slider (blur + dim). "Color" sets a solid colour. "Single image" uses one image
# file (no rotation). "Image slideshow" rotates through images in a folder.
BACKGROUND_MODE_LABELS = ["Keep existing", "Color", "Single image", "Image slideshow"]
BACKGROUND_MODE_VALUES = ["keep", "color", "image", "slideshow"]
BACKGROUND_MODE_KEEP = 0
BACKGROUND_MODE_COLOR = 1
BACKGROUND_MODE_IMAGE = 2
BACKGROUND_MODE_SLIDESHOW = 3

# "Change image every" options and the seconds they map to (index aligned).
SLIDESHOW_INTERVAL_LABELS = ['Every 15 seconds', 'Every 30 seconds', 'Every 1 minute',
                            'Every 2 minutes', 'Every 3 minutes', 'Every 5 minutes',
                            'Every 10 minutes', 'Every 20 minutes']
SLIDESHOW_INTERVAL_SECONDS = [15, 30, 60, 120, 180, 300, 600, 1200]
SLIDESHOW_DEFAULT_INTERVAL_INDEX = 1  # 30 seconds


def _get_background_picker_path(background_reference):
    resolved_background = resolve_background_reference(background_reference)
    if resolved_background.get('kind') == 'color':
        return ''
    return resolved_background['absolutePath'] or str(background_reference or '')


def _get_background_label_path(background_reference):
    resolved_background = resolve_background_reference(background_reference)
    if resolved_background.get('kind') == 'color':
        return resolved_background.get('colorValue', '') or str(background_reference or '')
    return resolved_background['absolutePath'] or resolved_background['relativePath'] or str(background_reference or '')


def _background_reference_is_color(background_reference):
    return resolve_background_reference(background_reference).get('kind') == 'color'


def _background_reference_to_colour(background_reference):
    resolved_background = resolve_background_reference(background_reference)
    color_value = str(resolved_background.get('colorValue', '') or '').strip()
    if color_value.startswith('#'):
        color_value = color_value[1:]

    if len(color_value) not in (6, 8):
        return wx.Colour(0, 0, 0)

    try:
        red = int(color_value[0:2], 16)
        green = int(color_value[2:4], 16)
        blue = int(color_value[4:6], 16)
        alpha = int(color_value[6:8], 16) if len(color_value) == 8 else 255
    except ValueError:
        return wx.Colour(0, 0, 0)

    return wx.Colour(red, green, blue, alpha)


def _colour_to_background_reference(colour):
    return 'color:#%02X%02X%02X' % (colour.Red(), colour.Green(), colour.Blue())


#
# Mood layout edit window
#

class EditMoodDialog(wx.Dialog):
    def __init__(self, moodsPanel, RowSelected, mode):
        xpos, ypos = moodsPanel.GetScreenPosition()
        dialog_width, dialog_height = moodsPanel.BeamSettings._moodSize
#        wx.Dialog.__init__(self, moodsPanel, title=mode, pos=(xpos + 50, ypos + 50), style=wx.RESIZE_BORDER)
        wx.Dialog.__init__(self, moodsPanel, title=mode, pos=wx.Point(xpos + 50, ypos + 50),
#                           size=moodsPanel.BeamSettings._moodSize, style=wx.RESIZE_BORDER)
                           size=wx.Size(dialog_width, dialog_height))
        # #        wx.Frame.__init__(self, moodsPanel, title=mode, pos=(xpos + 50, ypos + 50),
#                          size=self.moodsPanel.BeamSettings._moodSize,
#                          style=wx.DEFAULT_FRAME_STYLE & ~ (wx.RESIZE_BORDER | wx.MAXIMIZE_BOX))

        # MoodsPanel
        self.moodsPanel = moodsPanel
        self.RowSelected = RowSelected
        self.mode = mode
        self.EditMood = {}
        self.isDefaultMood = False
        self._preview_debounce = None
        self._layout_tooltips = []
        self._dmx_supported = platform.system() != 'Windows'

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

        self.isDefaultMood = self.EditMood.get('Name') == 'Default'
        self._update_dialog_title()

        # Build the panel
        self.panel = wx.Panel(self)
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.hbox = wx.BoxSizer(wx.HORIZONTAL)

        # Save/Cancel-buttons
        self.OkButton = wx.Button(self.panel, label="Save")
        self.OkButton.Bind(wx.EVT_BUTTON, self.OnOk)
        self.hbox.Add(self.OkButton, flag=wx.LEFT | wx.BOTTOM | wx.TOP, border=10)

        # Description Settings
        if not self.isDefaultMood:
            propertiesBox = wx.StaticBoxSizer(wx.VERTICAL, self.panel, "Properties")
            propertiesGrid = self.CreatePropertiesGrid()
            propertiesBox.Add(propertiesGrid, flag=wx.ALL | wx.EXPAND, border=10)
            self.vbox.Add(propertiesBox, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        # Background: a type dropdown that reveals only the controls for the chosen type.
        background_box = wx.StaticBoxSizer(wx.VERTICAL, self.panel, "Background")
        type_row = wx.BoxSizer(wx.HORIZONTAL)
        self.BackgroundTypeChoice = normalizeMacControlHeight(wx.ComboBox(
            self.panel, choices=BACKGROUND_MODE_LABELS, style=wx.CB_READONLY))
        self.BackgroundTypeChoice.Bind(wx.EVT_COMBOBOX, self.OnBackgroundModeChanged)
        type_row.Add(self.BackgroundTypeChoice, proportion=1, flag=wx.ALIGN_CENTER_VERTICAL)
        background_box.Add(type_row, flag=wx.EXPAND | wx.ALL, border=10)

        # --- Keep existing: Readability slider ---
        keep_panel = wx.Panel(self.panel)
        try:
            initial_readability = int(self.EditMood.get('Readability', 0) or 0)
        except (TypeError, ValueError):
            initial_readability = 0
        initial_readability = max(0, min(100, initial_readability))
        self.ReadabilityLabel = wx.StaticText(keep_panel, -1, "Readability")
        self.ReadabilitySlider = wx.Slider(
            keep_panel, value=initial_readability, minValue=0, maxValue=100,
            style=wx.SL_HORIZONTAL | wx.SL_LABELS)
        self.ReadabilitySlider.SetToolTip(
            "Keeps the on-screen background but blurs and darkens it so text is easier to read")
        self.ReadabilitySlider.Bind(wx.EVT_SLIDER, self.OnReadabilityChanged)
        keep_sizer = wx.BoxSizer(wx.HORIZONTAL)
        keep_sizer.Add(self.ReadabilityLabel, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=10)
        keep_sizer.Add(self.ReadabilitySlider, proportion=1, flag=wx.ALIGN_CENTER_VERTICAL)
        keep_panel.SetSizer(keep_sizer)

        # --- Color: colour swatch button (shows the colour, opens the picker on click) ---
        color_panel = wx.Panel(self.panel)
        self.ChooseBackgroundColorButton = colourselect.ColourSelect(
            color_panel, -1, "", _background_reference_to_colour(self.EditMood.get('Background', '')),
            size=(120, 28))
        self.ChooseBackgroundColorButton.SetToolTip("Pick the solid background color for this mood")
        self.ChooseBackgroundColorButton.Bind(colourselect.EVT_COLOURSELECT, self.OnChooseBackgroundColor)
        color_sizer = wx.BoxSizer(wx.HORIZONTAL)
        color_sizer.Add(wx.StaticText(color_panel, -1, "Color:"), flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=10)
        color_sizer.Add(self.ChooseBackgroundColorButton, flag=wx.ALIGN_CENTER_VERTICAL)
        color_panel.SetSizer(color_sizer)

        # --- Single image: Browse image ---
        image_panel = wx.Panel(self.panel)
        self.BrowseImageButton = wx.Button(image_panel, label="Browse image...")
        self.currentImageLabel = wx.StaticText(image_panel, -1, "")
        self.BrowseImageButton.Bind(wx.EVT_BUTTON, self.OnBrowseImage)
        image_sizer = wx.BoxSizer(wx.HORIZONTAL)
        image_sizer.Add(self.BrowseImageButton, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=10)
        image_sizer.Add(self.currentImageLabel, proportion=1, flag=wx.ALIGN_CENTER_VERTICAL)
        image_panel.SetSizer(image_sizer)

        # --- Image slideshow: folder + interval + random order ---
        slideshow_panel = wx.Panel(self.panel)
        self.ChooseFolderButton = wx.Button(slideshow_panel, label="Choose folder...")
        self.currentFolderLabel = wx.StaticText(slideshow_panel, -1, "")
        self.BackgroundTimerBox = normalizeMacControlHeight(wx.ComboBox(
            slideshow_panel, choices=SLIDESHOW_INTERVAL_LABELS, style=wx.CB_READONLY))
        self.RandomBackgroundBox = wx.CheckBox(slideshow_panel, label='Random order')
        self.ChooseFolderButton.Bind(wx.EVT_BUTTON, self.OnChooseFolder)
        self.BackgroundTimerBox.Bind(wx.EVT_COMBOBOX, self.OnSlideshowChanged)
        self.RandomBackgroundBox.Bind(wx.EVT_CHECKBOX, self.OnSlideshowChanged)
        slideshow_sizer = wx.BoxSizer(wx.VERTICAL)
        folder_row = wx.BoxSizer(wx.HORIZONTAL)
        folder_row.Add(self.ChooseFolderButton, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=10)
        folder_row.Add(self.currentFolderLabel, proportion=1, flag=wx.ALIGN_CENTER_VERTICAL)
        slideshow_sizer.Add(folder_row, flag=wx.EXPAND)
        interval_row = wx.BoxSizer(wx.HORIZONTAL)
        interval_row.Add(wx.StaticText(slideshow_panel, -1, "Change image every:"),
                         flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=10)
        interval_row.Add(self.BackgroundTimerBox, flag=wx.ALIGN_CENTER_VERTICAL)
        slideshow_sizer.Add(interval_row, flag=wx.TOP, border=8)
        slideshow_sizer.Add(self.RandomBackgroundBox, flag=wx.TOP, border=8)
        slideshow_panel.SetSizer(slideshow_sizer)

        # Panels indexed to match BACKGROUND_MODE_*; only the selected one is shown.
        self._background_option_panels = [keep_panel, color_panel, image_panel, slideshow_panel]
        for option_panel in self._background_option_panels:
            background_box.Add(option_panel, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=10)
        self.vbox.Add(background_box, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        self._set_selected_background_mode(self._resolve_initial_background_mode())
        self._update_background_controls_state()

        # Layout controls
        self.LayoutSettings()

        mood_duration_box = wx.StaticBoxSizer(wx.VERTICAL, self.panel, "Mood Timing")
        mood_duration_row = wx.BoxSizer(wx.HORIZONTAL)
        mood_duration_label = wx.StaticText(self.panel, -1, "Display duration:")
        mood_duration_units = wx.StaticText(self.panel, -1, "seconds")
        mood_duration_tooltip = "Time in seconds that the mood will last before fallback to default mood"
        mood_duration_label.SetToolTip(mood_duration_tooltip)
        self.DisplayTimerField.SetToolTip(mood_duration_tooltip)
        mood_duration_row.Add(mood_duration_label, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=10)
        mood_duration_row.Add(self.DisplayTimerField, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=10)
        mood_duration_row.Add(mood_duration_units, flag=wx.ALIGN_CENTER_VERTICAL)
        mood_duration_box.Add(mood_duration_row, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        self.vbox.Add(mood_duration_box, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        layout_box = wx.StaticBoxSizer(wx.VERTICAL, self.panel, "On-screen Text Layout")
        layout_box.Add(self.LayoutList, 1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        layout_box.Add(self.sizerbuttons, flag=wx.LEFT | wx.BOTTOM, border=10)
        self.vbox.Add(layout_box, proportion=1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        # DMX
        lighting_box = wx.StaticBoxSizer(wx.VERTICAL, self.panel, "Lighting / DMX")
        if self._dmx_supported:
            u1c = self.getU1DMXColourList()
            u2c = self.getU2DMXColourList()
            self.vboxU1 = wx.BoxSizer(wx.VERTICAL)
            self.vboxU2 = wx.BoxSizer(wx.VERTICAL)
            self.hboxU1 = wx.BoxSizer(wx.HORIZONTAL)
            self.hboxU2 = wx.BoxSizer(wx.HORIZONTAL)
            self.hboxDMX = wx.BoxSizer(wx.HORIZONTAL)

            dmxU1Device = dmxmodule.DMXdevice(beamSettings.getSelectedU1DMXdeviceName())
            self.U1DMXcolourDropdown = wx.ComboBox(self.panel, value=self.EditMood['U1DMXcolour'],
                                                 choices=dmxU1Device.GetPaletteList(),
                                                 style=wx.CB_READONLY)
            self.U1DMXcolourDropdown.Bind(wx.EVT_COMBOBOX, self.OnSelectU1DMXcolour)
            self.U1DMXfixtureColourList = wx.ListBox(self.panel, wx.ID_ANY, choices=u1c, style=wx.LB_MULTIPLE)
            self.hboxU1.Add(self.U1DMXfixtureColourList, border=10)
            self.hboxU1.Add(self.U1DMXcolourDropdown, flag=wx.LEFT | wx.BOTTOM, border=10)
            self.vboxU1.Add(wx.StaticText(self.panel, -1, 'U1 DMX colours'), flag=wx.LEFT | wx.BOTTOM, border=10)
            self.vboxU1.Add(self.hboxU1, flag=wx.LEFT | wx.BOTTOM, border=10)

            dmxU2Device = dmxmodule.DMXdevice(beamSettings.getSelectedU2DMXdeviceName())
            self.U2DMXcolourDropdown = wx.ComboBox(self.panel, value=self.EditMood['U2DMXcolour'],
                                                 choices=dmxU2Device.GetPaletteList(),
                                                 style=wx.CB_READONLY)
            self.U2DMXcolourDropdown.Bind(wx.EVT_COMBOBOX, self.OnSelectU2DMXcolour)
            self.U2DMXfixtureColourList = wx.ListBox(self.panel, wx.ID_ANY, choices=u2c, style=wx.LB_MULTIPLE)
            self.hboxU2.Add(self.U2DMXfixtureColourList, border=10)
            self.hboxU2.Add(self.U2DMXcolourDropdown, flag=wx.LEFT | wx.BOTTOM, border=10)
            self.vboxU2.Add(wx.StaticText(self.panel, -1, 'U2 DMX colours'), flag=wx.LEFT | wx.BOTTOM, border=10)
            self.vboxU2.Add(self.hboxU2, flag=wx.LEFT | wx.BOTTOM, border=10)

            self.hboxDMX.Add(self.vboxU1, proportion=1, flag=wx.RIGHT, border=10)
            self.hboxDMX.Add(self.vboxU2, proportion=1)
            lighting_box.Add(self.hboxDMX, flag=wx.EXPAND | wx.ALL, border=10)
        else:
            self.U1DMXcolourDropdown = None
            self.U2DMXcolourDropdown = None
            self.U1DMXfixtureColourList = None
            self.U2DMXfixtureColourList = None
            lighting_box.Add(wx.StaticText(self.panel, -1, 'DMX module is not enabled on this system.'), flag=wx.ALL, border=10)
        self.vbox.Add(lighting_box, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        # Set sizers
        self.vbox.Add(self.hbox, flag=wx.ALIGN_RIGHT)
        self.panel.SetSizer(self.vbox)
        self._fit_dialog_to_content(dialog_width)
        self._bind_live_preview_events()

    def _fit_dialog_to_content(self, min_width):
        self.panel.Layout()
        self.vbox.Fit(self.panel)
        best_size = self.panel.GetBestSize()
        fitted_size = wx.Size(max(min_width, best_size.GetWidth()), best_size.GetHeight())
        self.SetClientSize(fitted_size)
        self.SetMinSize(fitted_size)

    #
    # Crates fields and sets values
    #
    def CreatePropertiesGrid(self):

        # Create the fields

        self.MoodNameField = normalizeMacControlHeight(wx.TextCtrl(self.panel, value=self.EditMood['Name'], size=(120, -1)), default_width=120)
        self.MoodStateField = normalizeMacControlHeight(wx.ComboBox(self.panel, value=self.EditMood['PlayState'],
                                          choices=["Playing", "Not Playing"],
                          size=(120, -1), style=wx.CB_READONLY), default_width=120)
        # min > 0 not to push away the default mood
        self.MoodOrderField = wx.SpinCtrl(self.panel, value=str(self.RowSelected), min=1, max=99)
        self.InputID3Field = normalizeMacControlHeight(wx.ComboBox(self.panel, size=(120, -1), value=self.EditMood['Field1'],
                         choices=self.Fields, style=wx.CB_READONLY), default_width=120)
        self.IsIsNotField = normalizeMacControlHeight(wx.ComboBox(self.panel, value=self.EditMood['Field2'], choices=["is", "is not", "contains"],
                        style=wx.CB_READONLY), default_width=120)
        self.OutputField = normalizeMacControlHeight(wx.TextCtrl(self.panel, value=self.EditMood['Field3'], size=(120, -1)), default_width=120)

        if self.isDefaultMood:
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
        self.LayoutList.Bind(wx.EVT_LISTBOX, self.OnLayoutSelectionChanged)
        self.LayoutList.Bind(wx.EVT_LISTBOX_DCLICK, self.OnEditLayoutItem)
        self.LayoutList.Bind(wx.EVT_CHECKLISTBOX, self.OnCheckLayout)

        # Load data into table
        self.BuildLayoutList()

        self.AddLayoutItemButton.Bind(wx.EVT_BUTTON, self.OnAddLayoutItem)
        self.EditLayoutItemButton.Bind(wx.EVT_BUTTON, self.OnEditLayoutItem)
        self.DelLayoutItemButton.Bind(wx.EVT_BUTTON, self.OnDelLayoutItem)
        # Background controls (image / folder / colour swatch) are bound in __init__.

    #
    # BUILD LIST AND CHECK
    #
    def BuildLayoutList(self):

        self.DisplayRows = []
        self._layout_tooltips = []
        MoodLayout = self.EditMood['Display']
        for i in range(0, len(MoodLayout)):
            Settings = MoodLayout[i]
            self.DisplayRows.append(self._format_layout_item_label(Settings))
            self._layout_tooltips.append(str(Settings.get('Field', '')))
        self.LayoutList.Set(self.DisplayRows)
        for i in range(0, len(MoodLayout)):
            Settings = MoodLayout[i]
            if Settings['Active'] == "yes":
                self.LayoutList.Check(i, check=True)
            else:
                self.LayoutList.Check(i, check=False)
        self._update_layout_list_tooltip()

    def _format_layout_item_label(self, settings):
        field_value = str(settings.get('Field', '')).strip()
        tag_labels = {
            '%Artist': 'Artist',
            '%AlbumArtist': 'Album Artist',
            '%Title': 'Title',
            '%Album': 'Album',
            '%Genre': 'Genre',
            '%Comment': 'Comment',
            '%Composer': 'Composer',
            '%Year': 'Year',
            '%Singer': 'Singer',
            '%Performer': 'Performer',
            '%IsCortina': 'Cortina Flag',
            '%CoverArt': 'Cover Art',
            '%PreviousTitle': 'Previous Title',
            '%PreviousArtist': 'Previous Artist',
            '%NextTitle': 'Next Title',
            '%NextArtist': 'Next Artist',
        }
        if field_value in tag_labels:
            return tag_labels[field_value]
        if field_value.startswith('%') and ' ' not in field_value:
            return field_value.lstrip('%').replace('_', ' ')
        shortened_value = field_value if len(field_value) <= 40 else field_value[:37] + '...'
        return 'Custom: ' + shortened_value

    def OnLayoutSelectionChanged(self, event):
        self._update_layout_list_tooltip()
        event.Skip()

    def _update_layout_list_tooltip(self):
        row_selected = self.LayoutList.GetSelection()
        if 0 <= row_selected < len(self._layout_tooltips):
            self.LayoutList.SetToolTip('Raw expression: ' + self._layout_tooltips[row_selected])
        else:
            self.LayoutList.SetToolTip('')


    def OnCheckLayout(self, event):
        MoodLayout = self.EditMood['Display']
        for i in range(0, len(MoodLayout)):
            layout = MoodLayout[i]
            if self.LayoutList.IsChecked(i):
                layout['Active'] = "yes"
            else:
                layout['Active'] = "no"
        if self.mode == "Edit mood":
            beamSettings.markDirty()
        self.BuildLayoutList()
        self._schedule_preview_refresh(immediate=True)

    #
    # BACKGROUND MODE ("Keep existing" / "Color" / "Single image" / "Image slideshow")
    #
    def _resolve_initial_background_mode(self):
        # "Keep existing" (and the legacy "readability") inherit the on-screen background.
        mode = str(self.EditMood.get('BackgroundMode', '')).strip().lower()
        if mode in ('keep', 'readability'):
            return BACKGROUND_MODE_KEEP
        # Otherwise reflect the mood's actual stored background.
        background_reference = self.EditMood.get('Background', '')
        if _background_reference_is_color(background_reference):
            return BACKGROUND_MODE_COLOR
        # Rotation enabled => slideshow; a plain image reference => single image.
        rotate = str(self.EditMood.get('RotateBackground', 'no')).strip().lower()
        if rotate in ('linear', 'random'):
            return BACKGROUND_MODE_SLIDESHOW
        if str(background_reference or '').strip():
            return BACKGROUND_MODE_IMAGE
        return BACKGROUND_MODE_KEEP

    def _get_selected_background_mode(self):
        selection = self.BackgroundTypeChoice.GetSelection()
        return selection if selection >= 0 else BACKGROUND_MODE_KEEP

    def _set_selected_background_mode(self, mode_index):
        mode_index = max(0, min(len(BACKGROUND_MODE_VALUES) - 1, int(mode_index)))
        self.BackgroundTypeChoice.SetSelection(mode_index)

    def _update_background_controls_state(self):
        # Show only the controls for the selected background type, then reflow.
        selection = self._get_selected_background_mode()
        for mode_index, option_panel in enumerate(self._background_option_panels):
            option_panel.Show(mode_index == selection)
        self._update_background_labels()
        self.panel.Layout()

    def OnBackgroundModeChanged(self, event):
        selection = self._get_selected_background_mode()
        self.EditMood['BackgroundMode'] = BACKGROUND_MODE_VALUES[selection]
        # Rotation is only on for the slideshow mode.
        if selection == BACKGROUND_MODE_SLIDESHOW:
            self._apply_slideshow_rotation_from_controls()
        else:
            self.EditMood['RotateBackground'] = 'no'
        self._update_background_controls_state()
        if self.mode == "Edit mood":
            beamSettings.markDirty()
        self._schedule_preview_refresh(immediate=True)

    def OnReadabilityChanged(self, event):
        self.EditMood['Readability'] = int(self.ReadabilitySlider.GetValue())
        if self.mode == "Edit mood":
            beamSettings.markDirty()
        self._schedule_preview_refresh(immediate=True)

    #
    # IMAGE SLIDESHOW (folder rotation)
    #
    def _apply_slideshow_rotation_from_controls(self):
        self.EditMood['RotateBackground'] = 'random' if self.RandomBackgroundBox.IsChecked() else 'linear'
        interval_index = self.BackgroundTimerBox.GetSelection()
        if interval_index < 0:
            interval_index = SLIDESHOW_DEFAULT_INTERVAL_INDEX
        self.EditMood['RotateTimer'] = SLIDESHOW_INTERVAL_SECONDS[interval_index]

    def OnSlideshowChanged(self, event):
        self._apply_slideshow_rotation_from_controls()
        if self.mode == "Edit mood":
            beamSettings.markDirty()
        self._schedule_preview_refresh(immediate=True)
        event.Skip()

    def _update_color_button_swatch(self):
        # The ColourSelect button face shows the chosen colour (no separate hex label).
        background_reference = self.EditMood.get('Background', '')
        if _background_reference_is_color(background_reference):
            self.ChooseBackgroundColorButton.SetColour(_background_reference_to_colour(background_reference))

    def _update_background_labels(self):
        # Reflect the stored interval / random order and the selected image/folder names.
        try:
            interval_index = SLIDESHOW_INTERVAL_SECONDS.index(int(self.EditMood.get('RotateTimer', 30)))
        except (ValueError, TypeError):
            interval_index = SLIDESHOW_DEFAULT_INTERVAL_INDEX
        self.BackgroundTimerBox.SetSelection(interval_index)
        self.RandomBackgroundBox.SetValue(
            str(self.EditMood.get('RotateBackground', 'no')).strip().lower() == 'random')

        self._update_color_button_swatch()

        background_reference = self.EditMood.get('Background', '')
        if _background_reference_is_color(background_reference):
            self.currentImageLabel.SetLabel("")
            self.currentFolderLabel.SetLabel("")
            return

        label_path = _get_background_label_path(background_reference)
        if not label_path:
            self.currentImageLabel.SetLabel("")
            self.currentFolderLabel.SetLabel("")
            return

        parent_path, background_file = os.path.split(os.path.normpath(label_path))
        is_image_file = os.path.splitext(background_file)[1].lower() in BACKGROUND_EXTENSIONS
        self.currentImageLabel.SetLabel(background_file if is_image_file else "")
        # For a file the slideshow folder is its parent; for a folder it is the folder itself.
        self.currentFolderLabel.SetLabel(os.path.split(parent_path)[1] if is_image_file else background_file)



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
                if self.mode == "Edit mood":
                    beamSettings.markDirty()
                self.BuildLayoutList()
                self._schedule_preview_refresh(immediate=True)

    def _bind_live_preview_events(self):
        if not self.isDefaultMood:
            self.MoodNameField.Bind(wx.EVT_TEXT, self.OnTextPreviewChange)
            self.OutputField.Bind(wx.EVT_TEXT, self.OnTextPreviewChange)
            self.MoodStateField.Bind(wx.EVT_COMBOBOX, self.OnImmediatePreviewChange)
            self.MoodOrderField.Bind(wx.EVT_SPINCTRL, self.OnImmediatePreviewChange)
            self.InputID3Field.Bind(wx.EVT_COMBOBOX, self.OnImmediatePreviewChange)
            self.IsIsNotField.Bind(wx.EVT_COMBOBOX, self.OnImmediatePreviewChange)
        self.DisplayTimerField.Bind(wx.EVT_SPINCTRL, self.OnImmediatePreviewChange)
        # Slideshow controls (interval / random order) refresh the preview via OnSlideshowChanged.

    def OnTextPreviewChange(self, event):
        self._schedule_preview_refresh(immediate=False)
        event.Skip()

    def OnImmediatePreviewChange(self, event):
        self._schedule_preview_refresh(immediate=True)
        event.Skip()

    def _schedule_preview_refresh(self, immediate):
        if self._preview_debounce is not None:
            self._preview_debounce.Stop()
            self._preview_debounce = None

        if immediate:
            self._apply_preview_updates()
            return

        self._preview_debounce = wx.CallLater(250, self._apply_preview_updates)

    def _apply_preview_updates(self):
        if self._preview_debounce is not None and not self._preview_debounce.IsRunning():
            self._preview_debounce = None

        if not self or self.IsBeingDeleted():
            return

        if not self.isDefaultMood:
            self.EditMood['Name'] = self.MoodNameField.GetValue()
            self.EditMood['PlayState'] = self.MoodStateField.GetValue()
            self.EditMood['Field1'] = self.InputID3Field.GetValue()
            self.EditMood['Field2'] = self.IsIsNotField.GetValue()
            self.EditMood['Field3'] = self.OutputField.GetValue()
        self.EditMood['DisplayTimer'] = self.DisplayTimerField.GetValue()
        self._update_dialog_title()

        if self.mode == 'Edit mood':
            beamSettings.markDirty()
            self.moodsPanel.updateSettings()

    def _update_dialog_title(self):
        mood_name = str(self.EditMood.get('Name', '')).strip() or 'New Mood'
        self.SetTitle('Edit Mood: ' + mood_name)

    def updateSettings(self):
        self._schedule_preview_refresh(immediate=True)

    #
    # Save mood layout
    #
    def OnOk(self, e):
        if self._preview_debounce is not None:
            self._preview_debounce.Stop()
            self._preview_debounce = None

        # Get Settings
        if self.isDefaultMood:
            self.EditMood['Name'] = 'Default'
            self.EditMood['PlayState'] = 'Playing'
            self.EditMood['Field1'] = '%Title'
            self.EditMood['Field2'] = 'contains'
            self.EditMood['Field3'] = 'something'
        else:
            self.EditMood['Name'] = self.MoodNameField.GetValue()
            self.EditMood['PlayState'] = self.MoodStateField.GetValue()
            self.EditMood['Field1'] = self.InputID3Field.GetValue()
            self.EditMood['Field2'] = self.IsIsNotField.GetValue()
            self.EditMood['Field3'] = self.OutputField.GetValue()
        self.EditMood['DisplayTimer'] = self.DisplayTimerField.GetValue()
        background_mode = self._get_selected_background_mode()
        self.EditMood['BackgroundMode'] = BACKGROUND_MODE_VALUES[background_mode]
        self.EditMood['Readability'] = int(self.ReadabilitySlider.GetValue())
        # Rotation is only enabled for the slideshow mode.
        if background_mode == BACKGROUND_MODE_SLIDESHOW:
            self._apply_slideshow_rotation_from_controls()
        else:
            self.EditMood['RotateBackground'] = 'no'
        if self._dmx_supported:
            self.EditMood['U1DMXcolour'] = self.U1DMXcolourDropdown.GetValue()
            self.EditMood['U1DMXcolours'] = self.U1DMXColourList()
            self.EditMood['U2DMXcolour'] = self.U2DMXcolourDropdown.GetValue()
            self.EditMood['U2DMXcolours'] = self.U2DMXColourList()
        self.EditMood['Type'] = 'Default' if self.EditMood['Name'] == 'Default' else 'Mood'

        if self.isDefaultMood:
            moodorder = 0
        else:
            moodorder = int(self.MoodOrderField.GetValue())

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

        beamSettings.markDirty()
        self.moodsPanel.BuildMoodList()
        if hasattr(self.moodsPanel, 'applyCommittedSettings'):
            self.moodsPanel.applyCommittedSettings()
        else:
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
    def _persist_background_selection(self, selected_path):
        # Returns a persisted background reference for the chosen file/folder, or
        # None if the user cancelled or the import failed.
        persisted_reference = to_persisted_background_reference(selected_path, 'moods')
        if persisted_reference is not None:
            return persisted_reference

        message = (
            "Copy the selected background into Beam's managed background library?\n\n"
            "Yes: import into ~/.beam/backgrounds/moods\n"
            "No: keep an unmanaged external path\n"
            "Cancel: keep the current background"
        )
        decision_dialog = wx.MessageDialog(
            self, message, "Import background", wx.YES_NO | wx.CANCEL | wx.ICON_QUESTION)
        try:
            decision = decision_dialog.ShowModal()
        finally:
            decision_dialog.Destroy()

        if decision == wx.ID_CANCEL:
            return None
        if decision == wx.ID_YES:
            import_result = import_background_asset(selected_path, 'moods')
            if import_result['status'] == 'failed':
                error_dialog = wx.MessageDialog(
                    self, import_result['message'], "Background import failed", wx.OK | wx.ICON_ERROR)
                try:
                    error_dialog.ShowModal()
                finally:
                    error_dialog.Destroy()
                return None
            return import_result['reference']
        return os.path.normpath(selected_path)

    def OnBrowseImage(self, event):
        # "Single image" mode: pick one image file (no rotation).
        background_path = _get_background_picker_path(self.EditMood['Background'])
        dialog_directory, dialog_file = os.path.split(background_path)
        open_dialog = wx.FileDialog(
            self, "Choose background image for mood", dialog_directory, dialog_file,
            BACKGROUND_FILE_WILDCARD, wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        try:
            if open_dialog.ShowModal() != wx.ID_OK:
                return
            persisted_reference = self._persist_background_selection(open_dialog.GetPath())
            if persisted_reference is None:
                return
            self.EditMood['Background'] = persisted_reference
            self.EditMood['BackgroundMode'] = 'image'
            self.EditMood['RotateBackground'] = 'no'
            self._set_selected_background_mode(BACKGROUND_MODE_IMAGE)
            if self.mode == "Edit mood":
                beamSettings.markDirty()
            self._update_background_controls_state()
            self._schedule_preview_refresh(immediate=True)
        finally:
            open_dialog.Destroy()

    def OnChooseFolder(self, event):
        # "Image slideshow" mode: pick a folder and rotate through its images.
        background_path = _get_background_picker_path(self.EditMood['Background'])
        dialog_directory = background_path
        if os.path.splitext(os.path.basename(background_path))[1].lower() in BACKGROUND_EXTENSIONS:
            dialog_directory = os.path.dirname(background_path)
        open_dialog = wx.DirDialog(
            self, "Select background folder for mood", dialog_directory, wx.DD_DIR_MUST_EXIST)
        try:
            if open_dialog.ShowModal() != wx.ID_OK:
                return
            persisted_reference = self._persist_background_selection(open_dialog.GetPath())
            if persisted_reference is None:
                return
            self.EditMood['Background'] = persisted_reference
            self.EditMood['BackgroundMode'] = 'slideshow'
            self._set_selected_background_mode(BACKGROUND_MODE_SLIDESHOW)
            self._apply_slideshow_rotation_from_controls()
            if self.mode == "Edit mood":
                beamSettings.markDirty()
            self._update_background_controls_state()
            self._schedule_preview_refresh(immediate=True)
        finally:
            open_dialog.Destroy()

    def OnChooseBackgroundColor(self, event):
        # The ColourSelect swatch button handles the picker dialog and reports the colour.
        selected_colour = event.GetValue()
        self.EditMood['Background'] = _colour_to_background_reference(selected_colour)
        self.EditMood['RotateBackground'] = 'no'
        self.EditMood['BackgroundMode'] = 'color'
        self._set_selected_background_mode(BACKGROUND_MODE_COLOR)
        if self.mode == "Edit mood":
            beamSettings.markDirty()
        self._update_background_controls_state()
        self._schedule_preview_refresh(immediate=True)

    def OnSelectU1DMXcolour(self, event):
        if not self._dmx_supported or self.U1DMXfixtureColourList is None or self.U1DMXcolourDropdown is None:
            return
        fixtureindices = self.U1DMXfixtureColourList.GetSelections()
        self.U1CurrentColour = self.U1DMXcolourDropdown.GetValue()
        u1c = self.U1DMXColourList()
        for i in fixtureindices:
            u1c[i] = self.U1CurrentColour
        u1 = beamSettings._Universe1
        self.U1DMXfixtureColourList.Clear()
        u1n = u1.FixtureNames()
        for index, value in enumerate(u1n):
            self.U1DMXfixtureColourList.Append(u1c[index])
        self._schedule_preview_refresh(immediate=True)

    def OnSelectU2DMXcolour(self, event):
        if not self._dmx_supported or self.U2DMXfixtureColourList is None or self.U2DMXcolourDropdown is None:
            return
        fixtureindices = self.U2DMXfixtureColourList.GetSelections()
        self.U2CurrentColour = self.U2DMXcolourDropdown.GetValue()
        u2c = self.U2DMXColourList()
        for i in fixtureindices:
            u2c[i] = self.U2CurrentColour
        u = beamSettings._Universe2
        self.U2DMXfixtureColourList.Clear()
        u2n = u.FixtureNames()
        for index, value in enumerate(u2n):
            self.U2DMXfixtureColourList.Append(u2c[index])
        self._schedule_preview_refresh(immediate=True)

    def U1DMXColourList (self):
        if self.U1DMXfixtureColourList is None:
            return list(self.EditMood.get('U1DMXcolours', []))
        list = []
        count = self.U1DMXfixtureColourList.GetCount()
        for i in range(count):
            list.append(self.U1DMXfixtureColourList.GetString(i))
        return list
    def U2DMXColourList (self):
        if self.U2DMXfixtureColourList is None:
            return list(self.EditMood.get('U2DMXcolours', []))
        list = []
        count = self.U2DMXfixtureColourList.GetCount()
        for i in range(count):
            list.append(self.U2DMXfixtureColourList.GetString(i))
        return list
    def getU1DMXColourList (self):
        list = []
        colour = self.EditMood['U1DMXcolour']
        try:
            list = self.EditMood['U1DMXcolours']
        except: pass
        finally:
            listlength = len(list)
            u = beamSettings._Universe1
            u1n = u.FixtureNames()
            fixtureCnt = len(u1n)
        return list[:fixtureCnt] + [colour]*(fixtureCnt-listlength)
    def getU2DMXColourList (self):
        list = []
        colour = self.EditMood['U2DMXcolour']
        try :
            list = self.EditMood['U2DMXcolours']
        except: pass
        finally:
            listlength = len(list)
            u = beamSettings._Universe2
            u2n = u.FixtureNames()
            fixtureCnt = len(u2n)
        return list[:fixtureCnt] + [colour]*(fixtureCnt-listlength)
