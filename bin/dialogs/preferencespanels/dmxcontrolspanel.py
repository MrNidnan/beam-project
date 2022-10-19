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

from bin.beamutils import *
from bin.DMX import *

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
        self.CurrentColour = 'None'

        ##########
        # SIZERS #
        ##########
        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox = wx.BoxSizer(wx.HORIZONTAL)  # For buttons

        #########################
        # DMX CONTROL SELECTOR  #
        #########################
        dmxplayer = wx.StaticText(self, wx.ID_ANY, "DMX Controls       ")
        font = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        dmxplayer.SetFont(font)
        
        dmxdescription = wx.StaticText(self, wx.ID_ANY, "Select desired light pattern")
        dmxDevice = adj_ub_6h.DMXdevice()
        self.DMXpatternSelectorDropdown = wx.ComboBox(self, wx.ID_ANY,
                                                      value=self.CurrentColour,
                                                    choices=dmxDevice.GetPaletteList(),
                                                    style=wx.CB_READONLY)
        self.DMXpatternSelectorDropdown.Bind(wx.EVT_COMBOBOX, self.OnSelectDMXpattern)
        vbox.Add(dmxplayer, flag=wx.LEFT | wx.TOP | wx.BOTTOM, border=10)
        vbox.Add(dmxdescription, flag=wx.LEFT, border=20)
        hbox.Add(self.DMXpatternSelectorDropdown, flag=wx.LEFT | wx.TOP, border=20)

        ###########
        # BUTTONS #
        ###########
        self.runBtn = wx.Button(self, label="Run Pattern")
        self.runBtn.Bind(wx.EVT_BUTTON, self.onRun)
        hbox.Add(self.runBtn, flag=wx.ALL, border=20)



        vbox.Add(hbox, flag=wx.LEFT)
        ##############
        # SET SIZERS #
        ##############
        self.SetSizer(vbox)
 #       self.SetSizer(hbox)






###################################################################
#                           EVENTS                                #
###################################################################

    def OnSelectDMXpattern(self, event):
        self.CurrentColour = self.DMXpatternSelectorDropdown.GetValue()

    def onRun (self, event):
        device = adj_ub_6h.DMXdevice()
        palette = device.GetPalette()
        colourpattern = palette[self.CurrentColour]
        DMXuniverse = device.GetUniverse()
        olamodule.sendDMXrequest(DMXuniverse, colourpattern)


###################################################################
#                             EOF                                 #
###################################################################
