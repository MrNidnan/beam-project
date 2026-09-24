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
import os
import logging
import wx.grid as gridlib
from sqlalchemy import false, true

from bin.DMX import dmxmodule
from bin.beamsettings import *
from bin.beamsettings import BeamSettings
from bin.dialogs.editlayoutitemdialog import EditLayoutItemDialog
from copy import deepcopy


#
# Mood layout edit window
#

class EditDMXdeviceDialog(wx.Dialog):
    def __init__(self, dmxcontrolsPanel, RowSelected, DevName, PaletteSize, mode, beamSettings):
        xpos, ypos = dmxcontrolsPanel.GetScreenPosition()
        #        wx.Dialog.__init__(self, moodsPanel, title=mode, pos=(xpos + 50, ypos + 50), style=wx.RESIZE_BORDER)
        wx.Dialog.__init__(self, dmxcontrolsPanel, title=mode, pos=(xpos + 50, ypos + 50),
        #                           size=moodsPanel.BeamSettings._moodSize, style=wx.RESIZE_BORDER)
        #                   )
        size=(300,800),
        # #        wx.Frame.__init__(self, moodsPanel, title=mode, pos=(xpos + 50, ypos + 50),
        #                          size=self.moodsPanel.BeamSettings._moodSize,
                                  style=wx.DEFAULT_FRAME_STYLE | wx.STAY_ON_TOP |  (wx.RESIZE_BORDER | wx.MAXIMIZE_BOX))
        # self.beamSettings = beamSettings

        # DMXdevicePanel
        self.dmxcontrolsPanel = dmxcontrolsPanel
        self.ColorField = wx.ColourPickerCtrl(self.dmxcontrolsPanel, size=(100,-1))
        self.InputError = false
        self.RowSelected = RowSelected
        self.mode = mode
        self.DevName = DevName
        self.PaletteSize = PaletteSize
        self.EditDMXdevice = {}
        # self.DMXdictionary = beamSettings.getDMXdeviceDict()

        # Define choices
        self.paletteRowLabels = ["None","Red","Green","Blue","White","Amber","Purple","Daylight",
                                  "Black","Sound1","Sound2","Auto0","Auto1","Auto2","Strobe"]
        self.paletteMaxChannels = int(self.PaletteSize)

        #
        # # Create a new default setting

        # Get item
        # self.EditDevice = deepcopy(beamSettings.getMoods()[0])
        self.EditDMXdevice["Name"] = self.DevName
        self.EditDMXdevice["PaletteSize"] = self.PaletteSize

        # Build the panel
        self.panel = wx.Panel(self)
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)

        # Save/Cancel-buttons
        self.OkButton = wx.Button(self.panel, label="Save")
        # if self.InputError == True:
        #     self.OkButton.Disable()
        # else:
        #     self.OkButton.Enable()

        self.button_cancel = wx.Button(self.panel, label="Cancel")
        self.OkButton.Bind(wx.EVT_BUTTON, self.OnOk)
        self.button_cancel.Bind(wx.EVT_BUTTON, self.onCancel)
        self.hbox.Add(self.OkButton, flag=wx.LEFT | wx.BOTTOM | wx.TOP , border=10)
        self.hbox.Add(self.button_cancel, flag=wx.LEFT | wx.BOTTOM | wx.TOP | wx.RIGHT, border=10)

        # Description Settings
        PropertiesText = wx.StaticText(self.panel, -1, "Properties")
        PropertiesText.SetFont(font)
        self.vbox.Add(PropertiesText, flag=wx.LEFT | wx.TOP | wx.BOTTOM, border=10)

        # Add settings

        DeviceNameLabel = wx.StaticText(self.panel, label="Name")
        self.DeviceNameField = wx.TextCtrl(self.panel, value=self.EditDMXdevice['Name'], size=(200, -1))
        self.vbox.Add(DeviceNameLabel, flag=wx.ALL | wx.EXPAND, border=10 )
        self.vbox.Add(self.DeviceNameField, flag=wx.ALL | wx.EXPAND, border=10)

        PaletteGridLabel = wx.StaticText(self.panel, label="Palette")
        self.vbox.Add(PaletteGridLabel, flag=wx.ALL | wx.EXPAND, border=10 )
        self.paletteGrid = self.CreatePaletteGrid()
        self.vbox.Add(self.paletteGrid, 1, flag=wx.EXPAND | wx.ALL, border=10)


        self.vbox.Add(self.hbox, flag=wx.ALIGN_RIGHT)

        self.panel.SetSizer(self.vbox)


    # Crates fields and sets values
    #
    def CreatePaletteGrid(self):

        # Create the fields

        #elf.DeviceNameField = wx.TextCtrl(self.panel, value=self.EditDevice['Name'], size=(120, -1))
        #paletteGrid = wx.FlexGridSizer(15, 3, 5, 5)
        paletteGrid = gridlib.Grid(self.panel)
        paletteGrid.CreateGrid(len(self.paletteRowLabels), self.paletteMaxChannels,1)
        paletteGrid.SetDefaultCellAlignment(wx.ALIGN_RIGHT, wx.ALIGN_CENTRE)

        for x in self.paletteRowLabels:
            paletteGrid.SetRowLabelValue(self.paletteRowLabels.index(x),x)
        for i in range(self.paletteMaxChannels):
            paletteGrid.SetColLabelValue(i,str(i+1))

        #  fill the values
        if self.mode == "Add":
            for x in self.paletteRowLabels:
                for i in range(self.paletteMaxChannels):
                    paletteGrid.SetCellValue(self.paletteRowLabels.index(x), i, "0")
        else:
            device = dmxmodule.DMXdevice(self.EditDMXdevice["Name"])
            # Palette = device.GetPalette()
            for x in self.paletteRowLabels:
                colourpattern = device.GetPattern(x)
                for i in range(self.paletteMaxChannels):
                    paletteGrid.SetCellValue(self.paletteRowLabels.index(x), i, str(colourpattern[i]))

        #paletteGrid.SetCellValue(0, 0, str(self.mode))
        self.Bind(gridlib.EVT_GRID_CELL_CHANGED, self.OnCellChange)
        #paletteGrid.AutoSize()
        return paletteGrid

    def OnCellChange(self, evt):
        print( "OnCellChange: (%d,%d) %s\n" % (evt.GetRow(), evt.GetCol(), evt.GetPosition()) )
        try:
            value = int(self.paletteGrid.GetCellValue(evt.GetRow(), evt.GetCol()))
        except ValueError:
            value = -1
            self.InputError = true
            self.OkButton.Disable()

        if value < 0 or 255 < value:
            self.moveto = evt.GetRow(), evt.GetCol()
            self.paletteGrid.SetCellTextColour(evt.GetRow(), evt.GetCol(), "red")
            self.InputError = true
            self.OkButton.Disable()
        else:
            self.paletteGrid.SetCellTextColour(evt.GetRow(), evt.GetCol(), str(self.ColorField))
            self.OkButton.Enable()
    #
    # Save device
    #
    def OnOk(self, evt):
        # get settings
        newname = self.DeviceNameField.GetValue()
        # check if it won't overwrite existing device definitions
        logging.debug("... Saving Device: " + str(newname))
        palette = {"Palette":{}}
        for x in self.paletteRowLabels:
            colour = []
            for i in range(self.paletteMaxChannels):
                numval = self.paletteGrid.GetCellValue(self.paletteRowLabels.index(x),i)
                # logging.debug("... numval: " + str(numval))
                colour.append(numval)

            logging.debug("... colour: " + x + " = " + str(colour))
            palette["Palette"][x] = colour

        logging.debug("... palette: " + x + " = " + str(palette))
        logging.debug("... current dictionary: " + str(beamSettings.getDMXdeviceDict().getDictionary()))
        beamSettings.getDMXdeviceDict().addDeviceToLibrary(newname, palette)
        # logging.debug("... modified dictionary: " + str(beamSettings.getDMXdeviceDict().getDictionary()))
        # logging.debug("... modified dictionary: " + str(beamSettings.getDMXdeviceList()))
        self.EndModal(wx.ID_OK)

        #self.Destroy()

    def onCancel(self, event):
        self.Destroy()

