#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    Copyright (C) 2026 Piotr R. Sidorowicz http://http://www.beam-project.com
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
#    XX/XX/2026 Version 1.0
#       - Initial release
#
# This Python file uses the following encoding: utf-8

import wx
import os
import wx.grid as gridlib
import logging
from bin.DMX import dmxmodule
from bin.beamsettings import *
from bin.dialogs.editlayoutitemdialog import EditLayoutItemDialog
from copy import deepcopy
from bin.dialogs.editdmxdevicedialog import EditDMXdeviceDialog
#
# Mood layout edit window
#

class AddDMXdeviceDialog(wx.Dialog):
    def __init__(self, dmxcontrolsPanel, RowSelected, mode, beamSettings):
        xpos, ypos = dmxcontrolsPanel.GetScreenPosition()
        #        wx.Dialog.__init__(self, moodsPanel, title=mode, pos=(xpos + 50, ypos + 50), style=wx.RESIZE_BORDER)
        wx.Dialog.__init__(self, dmxcontrolsPanel, title=mode, pos=(xpos + 50, ypos + 50),
        #                           size=moodsPanel.BeamSettings._moodSize, style=wx.RESIZE_BORDER)
                           )
        # size=dmxcontrolsPanel.beamSettings._preferencesSize)
        # #        wx.Frame.__init__(self, moodsPanel, title=mode, pos=(xpos + 50, ypos + 50),
        #                          size=self.moodsPanel.BeamSettings._moodSize,
        #                          style=wx.DEFAULT_FRAME_STYLE & ~ (wx.RESIZE_BORDER | wx.MAXIMIZE_BOX))
        #self.beamSettings = beamSettings

        # DMXdevicePanel
        self.dmxcontrolsPanel = dmxcontrolsPanel
        self.RowSelected = RowSelected
        self.mode = mode
        self.EditDMXdevice = {}


        self.AddDevice = {}
        self.AddDevice["Name"] = 'Brand: Model'
        self.AddDevice["PaletteSize"] = '3'


        # Build the panel
        self.panel = wx.Panel(self)
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        font = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD)

        # Save/Cancel-buttons
        self.OkButton = wx.Button(self.panel, label="Continue")
        self.button_cancel = wx.Button(self.panel, label="Cancel")
        self.OkButton.Bind(wx.EVT_BUTTON, self.onContinue)
        self.button_cancel.Bind(wx.EVT_BUTTON, self.onCancel)
        self.hbox.Add(self.OkButton, flag=wx.LEFT | wx.BOTTOM | wx.TOP , border=10)
        self.hbox.Add(self.button_cancel, flag=wx.LEFT | wx.BOTTOM | wx.TOP | wx.RIGHT, border=10)

        # Add settings

        DeviceNameLabel = wx.StaticText(self.panel, label="Name")
        self.DeviceNameField = wx.TextCtrl(self.panel, value=self.AddDevice['Name'], size=(100, -1))
        self.vbox.Add(DeviceNameLabel, flag=wx.ALL | wx.EXPAND, border=10 )
        self.vbox.Add(self.DeviceNameField, flag=wx.ALL | wx.EXPAND, border=10)

        DevicePaletteSizeLabel = wx.StaticText(self.panel, label="Palette Size")
        self.DevicePaletteSizeField = wx.TextCtrl(self.panel, value=self.AddDevice['PaletteSize'], size=(100, -1))
        self.vbox.Add(DevicePaletteSizeLabel, flag=wx.ALL | wx.EXPAND, border=10 )
        self.vbox.Add(self.DevicePaletteSizeField, flag=wx.ALL | wx.EXPAND, border=10)

        self.vbox.Add(self.hbox, flag=wx.ALIGN_RIGHT)

        self.panel.SetSizer(self.vbox)

    # Crates fields and sets values
    #
    def AddDevice(self):
        # add stuff
        return 0

    def onCancel(self, event):
        self.Destroy()

    def onContinue(self, event):
        vetted = 1
        errormessage = "Good to go"
        # check if the name already exists
        # check if name is blank
        # check if the size is between 3 and 30
        if str(self.DeviceNameField.GetValue()) in beamSettings.getDMXdeviceDict().getDictionary().keys():
            # some warning
            errormessage = "Device name already exists."
            vetted = 0
        if not (self.DeviceNameField.GetValue() and self.DeviceNameField.GetValue().strip()):
            errormessage = "Device name cannot be empty."
            vetted = 0
        if not (self.DevicePaletteSizeField.GetValue() and self.DevicePaletteSizeField.GetValue().strip()):
            self.DevicePaletteSizeField.SetValue("0")
        if  (int(self.DevicePaletteSizeField.GetValue()) < 3) or (30 < int(self.DevicePaletteSizeField.GetValue())):
            errormessage = "Palette size cannot be less than 3 or bigger than 30."
            vetted = 0

        if vetted==1:
            self.EditDMXdeviceButton = EditDMXdeviceDialog(self, -1, self.DeviceNameField.GetValue(), self.DevicePaletteSizeField.GetValue(), "Add", beamSettings)
            self.EditDMXdeviceButton.Show()
            #self.Close()
            if self.EditDMXdeviceButton.ShowModal() == wx.ID_OK:
                self.EditDMXdeviceButton.Destroy()
                self.EndModal(wx.ID_OK)

        else:
            wx.MessageBox(errormessage, "Error", wx.OK | wx.ICON_ERROR)
            logging.debug(str(errormessage))
