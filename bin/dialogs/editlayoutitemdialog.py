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
from copy import deepcopy
from bin.beamsettings import beamSettings



#
# Edit one layout item / tag
#
class EditLayoutItemDialog(wx.Dialog):
    def __init__(self, parent, row_selected, mode, layout_list):
        self.parent             = parent
        x, y = self.parent.GetScreenPosition()
        self.EditLayoutDialog   = wx.Dialog.__init__(self, parent, title=mode, pos = (x+50, y+50))
        self.EditLayoutPanel    = wx.Panel(self)
        self.RowSelected        = row_selected
        self.mode               = mode

        self.LayoutList         = layout_list
        self._original_layout_list = deepcopy(layout_list)
        self._preview_debounce = None
        # List of items do display and edit

        self.OkButton   = wx.Button(self.EditLayoutPanel, id=wx.ID_OK, label="Save")
        self.ButtonCancelLayout = wx.Button(self.EditLayoutPanel, id=wx.ID_CANCEL, label="Cancel")
        self.OkButton.Bind(wx.EVT_BUTTON, self.OnOK)
        self.ButtonCancelLayout.Bind(wx.EVT_BUTTON, self.OnCancelLayoutItem)

        e = wx.FontEnumerator()
        e.EnumerateFacenames()
        elist= e.GetFacenames()
 
        elist.sort()
 
        weights = ["Bold","Light","Normal"]
        styles = ["Italic","Normal","Slant"]
        alignments = ["Left","Center","Right"]
        text_flow_choices = ["Cut","Scale","Wrap"]
        
        hide_layout_tags = [
            '', '%Artist', '%Album', '%Title', '%Genre', '%Comment', '%Composer',
            '%Year', '%Singer', '%AlbumArtist', '%Performer', '%IsCortina', '%CoverArt',
            '%PreviousArtist', '%PreviousAlbum', '%PreviousTitle', '%PreviousGenre', '%PreviousComment', '%PreviousComposer',
            '%PreviousYear', '%PreviousSinger', '%PreviousAlbumArtist', '%PreviousPerformer', '%PreviousIsCortina',
            '%NextArtist', '%NextAlbum', '%NextTitle', '%NextGenre', '%NextComment', '%NextComposer',
            '%NextYear', '%NextSinger', '%NextAlbumArtist', '%NextPerformer', '%NextIsCortina',
            '%NextTandaArtist', '%NextTandaAlbum', '%NextTandaTitle', '%NextTandaGenre', '%NextTandaComment', '%NextTandaComposer',
            '%NextTandaYear', '%NextTandaSinger', '%NextTandaAlbumArtist', '%NextTandaPerformer'
        ]
                
        # Check if it is a new line
        if self.RowSelected < len(self.LayoutList):
            # Get the properties of the selected item
            self.Settings   = deepcopy(layout_list[self.RowSelected])
        else:
            # Create a new default item
            self.Settings   = ({"Field": "%Artist", "Font": "Default","Style": "Normal", "Weight": "Bold", "Size": 20, "FontColor": "(255,255,255,255)", "HideControl": "", "Position": [50,50], "Alignment": "Center", "Active": "yes", "TextFlow": "Wrap"})

        # Define fields
        self.LabelText          = wx.TextCtrl(self.EditLayoutPanel, size=(250,-1), value=self.Settings['Field'])
        self.FontDropdown       = wx.ComboBox(self.EditLayoutPanel, size=(125,-1), value=self.Settings['Font'], choices=elist, style=wx.CB_READONLY)
        self.StyleDropdown      = wx.ComboBox(self.EditLayoutPanel, size=(125,-1), value=self.Settings['Style'], choices=styles, style=wx.CB_READONLY)
        self.WeightDropdown     = wx.ComboBox(self.EditLayoutPanel, size=(125,-1), value=self.Settings['Weight'], choices=weights, style=wx.CB_READONLY)
        self.SizeText           = wx.SpinCtrl(self.EditLayoutPanel, size=(125,-1), value=str(self.Settings['Size']), min=1, max=99)
        self.ColorField         = wx.ColourPickerCtrl(self.EditLayoutPanel, size=(100,-1))
        self.HideText           = wx.ComboBox(self.EditLayoutPanel, size=(250,-1), value=self.Settings['HideControl'], choices=hide_layout_tags, style=wx.CB_READONLY)
        self.VerticalPos        = wx.SpinCtrl(self.EditLayoutPanel, size=(125,-1), value=str(self.Settings['Position'][0]), min=1, max=99)
        self.HorizontalPos      = wx.SpinCtrl(self.EditLayoutPanel, size=(125,-1), value=str(self.Settings['Position'][1]), min=1, max=99)
        self.Alignment          = wx.ComboBox(self.EditLayoutPanel, size=(125,-1), value=self.Settings['Alignment'], choices=alignments, style=wx.CB_READONLY)
        self.TextFlow           = wx.ComboBox(self.EditLayoutPanel, size=(125,-1), value=self.Settings['TextFlow'], choices=text_flow_choices, style=wx.CB_READONLY)
        self.ColorField.SetColour(eval(self.Settings['FontColor']))

        self.HorizontalPosLabel = wx.StaticText(self.EditLayoutPanel, label="Horizontal position")
        self._horizontal_position_disabled_tooltip = "Horizontal position is only used for left and right alignment."
        self.AutoPreviewHint = wx.StaticText(self.EditLayoutPanel, label="Preview updates automatically.")
        self.AutoPreviewHint.SetForegroundColour(wx.Colour(120, 120, 120))

        self.Alignment.Bind(wx.EVT_COMBOBOX, self.OnAlignmentChanged)
        self.LabelText.Bind(wx.EVT_TEXT, self.OnDebouncedPreviewChange)
        self.FontDropdown.Bind(wx.EVT_COMBOBOX, self.OnImmediatePreviewChange)
        self.StyleDropdown.Bind(wx.EVT_COMBOBOX, self.OnImmediatePreviewChange)
        self.WeightDropdown.Bind(wx.EVT_COMBOBOX, self.OnImmediatePreviewChange)
        self.SizeText.Bind(wx.EVT_SPINCTRL, self.OnImmediatePreviewChange)
        self.HideText.Bind(wx.EVT_COMBOBOX, self.OnImmediatePreviewChange)
        self.VerticalPos.Bind(wx.EVT_SPINCTRL, self.OnImmediatePreviewChange)
        self.HorizontalPos.Bind(wx.EVT_SPINCTRL, self.OnImmediatePreviewChange)
        self.TextFlow.Bind(wx.EVT_COMBOBOX, self.OnImmediatePreviewChange)
        self.ColorField.Bind(wx.EVT_COLOURPICKER_CHANGED, self.OnImmediatePreviewChange)

        content_box = wx.StaticBoxSizer(wx.VERTICAL, self.EditLayoutPanel, "Content")
        content_box.Add(wx.StaticText(self.EditLayoutPanel, label="Text template"), 0, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        content_box.Add(self.LabelText, 0, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, border=10)
        content_box.Add(wx.StaticText(self.EditLayoutPanel, label="Hide when tag is empty"), 0, flag=wx.LEFT | wx.RIGHT, border=10)
        content_box.Add(self.HideText, 0, flag=wx.ALL | wx.EXPAND, border=10)

        typography_box = wx.StaticBoxSizer(wx.VERTICAL, self.EditLayoutPanel, "Typography")
        typography_grid = wx.FlexGridSizer(6, 2, 5, 12)
        typography_grid.AddGrowableCol(0, 1)
        typography_grid.AddGrowableCol(1, 1)
        typography_grid.AddMany([
            (wx.StaticText(self.EditLayoutPanel, label="Font"), 0, wx.EXPAND),
            (wx.StaticText(self.EditLayoutPanel, label="Size"), 0, wx.EXPAND),
            (self.FontDropdown, 0, wx.EXPAND),
            (self.SizeText, 0, wx.EXPAND),
            (wx.StaticText(self.EditLayoutPanel, label="Style"), 0, wx.EXPAND),
            (wx.StaticText(self.EditLayoutPanel, label="Weight"), 0, wx.EXPAND),
            (self.StyleDropdown, 0, wx.EXPAND),
            (self.WeightDropdown, 0, wx.EXPAND),
        ])
        typography_box.Add(typography_grid, 0, flag=wx.ALL | wx.EXPAND, border=10)
        typography_box.Add(wx.StaticText(self.EditLayoutPanel, label="Font color"), 0, flag=wx.LEFT | wx.RIGHT, border=10)
        typography_box.Add(self.ColorField, 0, flag=wx.ALL, border=10)

        placement_box = wx.StaticBoxSizer(wx.VERTICAL, self.EditLayoutPanel, "Placement")
        placement_grid = wx.FlexGridSizer(4, 2, 5, 12)
        placement_grid.AddGrowableCol(0, 1)
        placement_grid.AddGrowableCol(1, 1)
        placement_grid.AddMany([
            (wx.StaticText(self.EditLayoutPanel, label="Alignment"), 0, wx.EXPAND),
            (wx.StaticText(self.EditLayoutPanel, label="Text flow"), 0, wx.EXPAND),
            (self.Alignment, 0, wx.EXPAND),
            (self.TextFlow, 0, wx.EXPAND),
            (wx.StaticText(self.EditLayoutPanel, label="Vertical position"), 0, wx.EXPAND),
            (self.HorizontalPosLabel, 0, wx.EXPAND),
            (self.VerticalPos, 0, wx.EXPAND),
            (self.HorizontalPos, 0, wx.EXPAND),
        ])
        placement_box.Add(placement_grid, 0, flag=wx.ALL | wx.EXPAND, border=10)

        self.vboxLayout = wx.BoxSizer(wx.VERTICAL)
        self.hboxLayout = wx.BoxSizer(wx.HORIZONTAL)
        
        self.hboxLayout.Add(self.ButtonCancelLayout, 0, flag=wx.LEFT | wx.BOTTOM | wx.TOP, border=10)
        self.hboxLayout.Add(self.OkButton, 0, flag=wx.LEFT | wx.BOTTOM | wx.TOP, border=10)

        self.vboxLayout.Add(content_box, 0, flag=wx.ALL | wx.EXPAND, border=10)
        self.vboxLayout.Add(typography_box, 0, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, border=10)
        self.vboxLayout.Add(placement_box, 0, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, border=10)
        self.vboxLayout.Add(self.AutoPreviewHint, 0, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM, border=10)

        self.vboxLayout.Add(self.hboxLayout, 0, flag=wx.ALL | wx.ALIGN_RIGHT)
        self.EditLayoutPanel.SetSizer(self.vboxLayout)
        self.vboxLayout.SetSizeHints(self)
        self._update_horizontal_position_state()
        self.Bind(wx.EVT_CLOSE, self.OnCancelLayoutItem)
        
    def DisableHorizontalBox(self, event):
        self._update_horizontal_position_state()
        event.Skip()

    def OnAlignmentChanged(self, event):
        self.DisableHorizontalBox(event)
        self._schedule_preview_refresh(immediate=True)

    def OnDebouncedPreviewChange(self, event):
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
            self._apply_preview_changes()
            return

        self._preview_debounce = wx.CallLater(250, self._apply_preview_changes)

    def _update_horizontal_position_state(self):
        is_centered = self.Alignment.GetValue() == "Center"
        self.HorizontalPos.Enable(not is_centered)
        tooltip = self._horizontal_position_disabled_tooltip if is_centered else "Horizontal position offset for left and right aligned items."
        self.HorizontalPos.SetToolTip(tooltip)
        self.HorizontalPosLabel.SetToolTip(tooltip)

    def _collect_settings_from_controls(self):
        settings = deepcopy(self.Settings)
        settings['Field'] = self.LabelText.GetValue()
        settings['Font'] = self.FontDropdown.GetValue()
        settings['Style'] = self.StyleDropdown.GetValue()
        settings['Weight'] = self.WeightDropdown.GetValue()
        settings['Size'] = int(self.SizeText.GetValue())
        settings['HideControl'] = self.HideText.GetValue()
        settings['FontColor'] = str(self.ColorField.GetColour())
        settings['Position'] = [int(self.VerticalPos.GetValue()), int(self.HorizontalPos.GetValue())]
        settings['Alignment'] = self.Alignment.GetValue()
        settings['TextFlow'] = self.TextFlow.GetValue()
        return settings

    def _build_layout_list_with_settings(self, settings):
        preview_layout_list = deepcopy(self._original_layout_list)

        if self.mode == "Edit layout item" and self.RowSelected < len(preview_layout_list):
            preview_layout_list.pop(self.RowSelected)

        xpos = settings['Position']
        newposition = len(preview_layout_list)
        for i in range(0, len(preview_layout_list)):
            pos = preview_layout_list[i]['Position']
            if xpos[0] < pos[0]:
                newposition = i
                break

        preview_layout_list.insert(newposition, settings)
        return preview_layout_list

    def _replace_live_layout_list(self, updated_layout_list):
        self.LayoutList[:] = updated_layout_list
        if hasattr(self.parent, 'BuildLayoutList'):
            self.parent.BuildLayoutList()
        self._refresh_parent_display()

    def _apply_preview_changes(self):
        if not self or self.IsBeingDeleted():
            return

        self.Settings = self._collect_settings_from_controls()
        self._replace_live_layout_list(self._build_layout_list_with_settings(self.Settings))

#
# SAVE
#
    def OnOK(self, event):
        if self._preview_debounce is not None:
            self._preview_debounce.Stop()
            self._preview_debounce = None

        self.Settings = self._collect_settings_from_controls()
        self._replace_live_layout_list(self._build_layout_list_with_settings(self.Settings))

        if hasattr(self.parent, 'BeamSettings'):
            self.parent.BeamSettings.markDirty()
        elif hasattr(self.parent, 'beamSettings'):
            self.parent.beamSettings.markDirty()
        elif getattr(self.parent, 'mode', None) == "Edit mood":
            beamSettings.markDirty()

        self.Destroy()

    def _refresh_parent_display(self):
        refresh_owner = self.parent

        if hasattr(refresh_owner, 'updateSettings'):
            refresh_owner.updateSettings()
            return

        if hasattr(refresh_owner, 'mainFrame') and hasattr(refresh_owner.mainFrame, 'updateSettings'):
            refresh_owner.mainFrame.updateSettings()
            return

        if hasattr(refresh_owner, 'moodsPanel') and hasattr(refresh_owner.moodsPanel, 'mainFrame') and hasattr(refresh_owner.moodsPanel.mainFrame, 'updateSettings'):
            refresh_owner.moodsPanel.mainFrame.updateSettings()

    #
    # CANCEL
    #
    def OnCancelLayoutItem(self, event):
        if self._preview_debounce is not None:
            self._preview_debounce.Stop()
            self._preview_debounce = None

        self._replace_live_layout_list(deepcopy(self._original_layout_list))
        self.Destroy()


