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

from bin.DMX import olamodule, dmxmodule
from bin.beamutils import *

###################################################################
#                      DMXcontrolsTab                           #
###################################################################
class DMXcontrolsPanel(wx.Panel):
    def __init__(self, parent, BeamSettings):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
        
        #############
        # VARIABLES #
        #############
        self.BeamSettings = BeamSettings
        self.U1CurrentColour = 'None'
        self.U2CurrentColour = 'None'

        ##########
        # SIZERS #
        ##########
        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)  # For buttons
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)  # For buttons

        #########################
        # DMX CONTROL SELECTOR  #
        #########################
        dmxplayer = wx.StaticText(self, wx.ID_ANY, "DMX Controls       ")
        font = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        dmxplayer.SetFont(font)
        
        dmxdescription = wx.StaticText(self, wx.ID_ANY, "Select desired light pattern")
        U1description = wx.StaticText(self, wx.ID_ANY, "Universe 1")
        U2description = wx.StaticText(self, wx.ID_ANY, "Universe 2")
        dmxU1Device = dmxmodule.DMXdevice(self.BeamSettings.getSelectedU1DMXdeviceName())
        self.U1DMXpatternSelectorDropdown = wx.ComboBox(self, wx.ID_ANY,
                                                      value=self.U1CurrentColour,
                                                    choices=dmxU1Device.GetPaletteList(),
                                                    style=wx.CB_READONLY)
        if self.BeamSettings.getSelectedU1DMXdeviceName() == 'None': device = self.U1DMXpatternSelectorDropdown.Disable()
        self.U1DMXpatternSelectorDropdown.Bind(wx.EVT_COMBOBOX, self.OnSelectU1DMXpattern)
        dmxU2Device = dmxmodule.DMXdevice(self.BeamSettings.getSelectedU2DMXdeviceName())
        self.U2DMXpatternSelectorDropdown = wx.ComboBox(self, wx.ID_ANY,
                                                      value=self.U2CurrentColour,
                                                    choices=dmxU2Device.GetPaletteList(),
                                                    style=wx.CB_READONLY)
        if self.BeamSettings.getSelectedU2DMXdeviceName() == 'None': device = self.U2DMXpatternSelectorDropdown.Disable()
        self.U2DMXpatternSelectorDropdown.Bind(wx.EVT_COMBOBOX, self.OnSelectU2DMXpattern)
        vbox.Add(dmxplayer, flag=wx.LEFT | wx.TOP | wx.BOTTOM, border=10)
        vbox.Add(dmxdescription, flag=wx.LEFT, border=20)
        hbox1.Add(U1description, flag=wx.LEFT | wx.TOP, border=20)
        hbox1.Add(self.U1DMXpatternSelectorDropdown, flag=wx.LEFT | wx.TOP, border=20)
        hbox2.Add(U2description, flag=wx.LEFT | wx.TOP, border=20)
        hbox2.Add(self.U2DMXpatternSelectorDropdown, flag=wx.LEFT | wx.TOP, border=20)

        ###########
        # BUTTONS #
        ###########
        self.runU1Btn = wx.Button(self, label="Run Pattern")
        self.runU1Btn.Bind(wx.EVT_BUTTON, self.onU1Run)
        if self.BeamSettings.getSelectedU1DMXdeviceName() == 'None': device = self.runU1Btn.Disable()
        hbox1.Add(self.runU1Btn, flag=wx.ALL, border=20)
        self.runU2Btn = wx.Button(self, label="Run Pattern")
        if self.BeamSettings.getSelectedU2DMXdeviceName() == 'None': device = self.runU2Btn.Disable()
        self.runU2Btn.Bind(wx.EVT_BUTTON, self.onU2Run)
        hbox2.Add(self.runU2Btn, flag=wx.ALL, border=20)



        vbox.Add(hbox1, flag=wx.LEFT)
        vbox.Add(hbox2, flag=wx.LEFT)
        ##############
        # SET SIZERS #
        ##############
        self.SetSizer(vbox)
 #       self.SetSizer(hbox)






###################################################################
#                           EVENTS                                #
###################################################################

    def OnSelectU1DMXpattern(self, event):
        self.U1CurrentColour = self.U1DMXpatternSelectorDropdown.GetValue()
    def OnSelectU2DMXpattern(self, event):
        self.U2CurrentColour = self.U2DMXpatternSelectorDropdown.GetValue()

    def onU1Run (self, event):
        device = None
        device = dmxmodule.DMXdevice(self.BeamSettings.getSelectedU1DMXdeviceName())
        if device is not None:
            colourpattern = device.GetPattern(self.U1CurrentColour)
            olamodule.sendDMXrequest(1, colourpattern)

    def onU2Run (self, event):
        device = None
        device = dmxmodule.DMXdevice(self.BeamSettings.getSelectedU2DMXdeviceName())
        if device is not None:
            colourpattern = device.GetPattern(self.U2CurrentColour)
            olamodule.sendDMXrequest(2, colourpattern)


###################################################################
#                             EOF                                 #
###################################################################
