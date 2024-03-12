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
import wx.adv

from bin.DMX import olamodule, dmxmodule
from bin.beamutils import *


###################################################################
#                      DMXcontrolsTab                           #
###################################################################
class DMXcontrolsPanel(wx.Panel):
    def __init__(self, parent, beamSettings):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        #############
        # VARIABLES #
        #############
        self.beamSettings = beamSettings
        self.U1CurrentColour = 'None'
        self.U2CurrentColour = 'None'
        self.U1SelectedDevices = []
        self.U2SelectedDevices = []
        ##########
        # SIZERS #
        ##########
        vbox = wx.BoxSizer(wx.VERTICAL)
        hboxWarning = wx.BoxSizer(wx.HORIZONTAL)
        vboxU1 = wx.BoxSizer(wx.VERTICAL)
        vboxU2 = wx.BoxSizer(wx.VERTICAL)
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)  # For buttons
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)  # For buttons
        hboxU1 = wx.BoxSizer(wx.HORIZONTAL)  # For buttons
        hboxU2 = wx.BoxSizer(wx.HORIZONTAL)  # For buttons
        hboxF = wx.BoxSizer(wx.HORIZONTAL)

        #########################
        # DMX Device SELECTOR #
        #########################
        self.dmxtitle = wx.StaticText(self, wx.ID_ANY, "DMX       ")
        font = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        self.dmxtitle.SetFont(font)
        vbox.Add(self.dmxtitle, flag=wx.LEFT | wx.TOP | wx.BOTTOM, border=10)
        if not olamodule.isRunningOlad():
            self.olalink = wx.adv.HyperlinkCtrl(self, id=wx.ID_ANY, label="",
                                                url="https://www.openlighting.org/ola/",
                                                style=wx.adv.HL_DEFAULT_STYLE)
            self.olalink.SetVisitedColour((255, 0, 0))
            self.olalink.SetNormalColour((255, 0, 0))
            self.warning = wx.StaticText(self, wx.ID_ANY, "OLA server is not running. For more information, visit:")
            self.warning.SetForegroundColour((255, 0, 0))
            hboxWarning.Add(self.warning, flag=wx.LEFT)
            hboxWarning.Add(self.olalink, flag=wx.LEFT)
            vbox.Add(hboxWarning, flag=wx.LEFT | wx.TOP | wx.BOTTOM, border=10)

        dmxU1description = wx.StaticText(self, wx.ID_ANY, "DMX devices in Universe 1")
        dmxU2description = wx.StaticText(self, wx.ID_ANY, "DMX devices in Universe 2")
        hboxU = wx.BoxSizer(wx.HORIZONTAL)
        self.DMXdeviceSelectorDropdown = wx.ComboBox(self, wx.ID_ANY,
                                                     value=self.beamSettings.getSelectedU1DMXdeviceName(),
                                                     choices=self.beamSettings._U1DMXdeviceName,
                                                     style=wx.CB_READONLY)
        # self.DMXdeviceSelectorDropdown.Bind(wx.EVT_COMBOBOX, self.OnSelectDMXdevice)

        u1 = self.beamSettings._Universe1
        u1n = u1.FixtureNames()
        u1a = u1.FixtureAddresses()
        u1c = u1.FixtureColours()
        u2 = self.beamSettings._Universe2
        u2n = u2.FixtureNames()
        u2a = u2.FixtureAddresses()
        u2c = u2.FixtureColours()

        self.U1DMXfixtureList = wx.ListBox(self, wx.ID_ANY, style=wx.LB_SINGLE)
        for index, value in enumerate(u1n):
            self.U1DMXfixtureList.Append('(' + u1a[index] + ') ' + value)

        self.U2DMXfixtureList = wx.ListBox(self, wx.ID_ANY, style=wx.LB_SINGLE)
        for index, value in enumerate(u2n):
            self.U2DMXfixtureList.Append('(' + u2a[index] + ') ' + value)

        ###########
        # BUTTONS #
        ###########
        self.addU1Btn = wx.Button(self, label="Add")
        self.addU1Btn.Bind(wx.EVT_BUTTON, self.onU1Add)
        # if self.beamSettings.getSelectedU1DMXdeviceName() == 'None': device = self.addU1Btn.Disable()
        hboxU1.Add(self.addU1Btn, flag=wx.ALL, border=2)
        self.addU2Btn = wx.Button(self, label="Add")
        self.addU2Btn.Bind(wx.EVT_BUTTON, self.onU2Add)
        # if self.beamSettings.getSelectedU2DMXdeviceName() == 'None': device = self.addU2Btn.Disable()
        hboxU2.Add(self.addU2Btn, flag=wx.ALL, border=2)

        self.delU1Btn = wx.Button(self, label="Delete")
        self.delU1Btn.Bind(wx.EVT_BUTTON, self.onU1Del)
        if self.U1DMXfixtureList.GetCount() < 1: self.delU1Btn.Disable()
        hboxU1.Add(self.delU1Btn, flag=wx.ALL, border=2)
        self.delU2Btn = wx.Button(self, label="Delete")
        # if self.beamSettings.getSelectedU2DMXdeviceName() == 'None': device = self.delU2Btn.Disable()
        self.delU2Btn.Bind(wx.EVT_BUTTON, self.onU2Del)
        hboxU2.Add(self.delU2Btn, flag=wx.ALL, border=2)

        vboxU1.Add(dmxU1description, flag=wx.LEFT | wx.TOP | wx.BOTTOM, border=10)
        vboxU1.Add(hboxU1, border=30)
        vboxU1.Add(self.U1DMXfixtureList, flag=wx.ALL | wx.EXPAND, border=1)
        vboxU2.Add(dmxU2description, flag=wx.LEFT | wx.TOP | wx.BOTTOM, border=10)
        vboxU2.Add(hboxU2, border=30)
        vboxU2.Add(self.U2DMXfixtureList, flag=wx.ALL | wx.EXPAND, border=1)
        hboxU.Add(vboxU1, border=30)
        hboxU.Add(vboxU2, border=30)

        AvailFixture = wx.StaticText(self, wx.ID_ANY, "Available Devices")
        hboxF.Add(AvailFixture, flag=wx.LEFT, border=10)
        hboxF.Add(self.DMXdeviceSelectorDropdown, flag=wx.LEFT, border=10)
        vbox.Add(hboxF, flag=wx.TOP, border=10)
        vbox.Add(hboxU, flag=wx.LEFT, border=1)

        #########################
        # DMX CONTROL SELECTOR  #
        #########################
        self.dmxcontrols = wx.StaticText(self, wx.ID_ANY, "Controls       ")
        font = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        self.dmxcontrols.SetFont(font)

        self.dmxdescription = wx.StaticText(self, wx.ID_ANY, "Select desired light pattern")
        self.U1description = wx.StaticText(self, wx.ID_ANY, "Universe 1")
        self.U2description = wx.StaticText(self, wx.ID_ANY, "Universe 2")
        dmxU1Device = dmxmodule.DMXdevice(self.beamSettings.getSelectedU1DMXdeviceName())
        self.U1DMXpatternSelectorDropdown = wx.ComboBox(self, wx.ID_ANY,
                                                        value=self.U1CurrentColour,
                                                        choices=dmxU1Device.GetPaletteList(),
                                                        style=wx.CB_READONLY)
        if self.beamSettings.getSelectedU1DMXdeviceName() == 'None': device = self.U1DMXpatternSelectorDropdown.Disable()
        self.U1DMXpatternSelectorDropdown.Bind(wx.EVT_COMBOBOX, self.OnSelectU1DMXpattern)

        self.U1DMXfixtureColourList = wx.ListBox(self, wx.ID_ANY, choices=u1c, style=wx.LB_MULTIPLE)
        self.U2DMXfixtureColourList = wx.ListBox(self, wx.ID_ANY, choices=u2c, style=wx.LB_MULTIPLE)

        dmxU2Device = dmxmodule.DMXdevice(self.beamSettings.getSelectedU2DMXdeviceName())
        self.U2DMXpatternSelectorDropdown = wx.ComboBox(self, wx.ID_ANY,
                                                        value=self.U2CurrentColour,
                                                        choices=dmxU2Device.GetPaletteList(),
                                                        style=wx.CB_READONLY)
        if self.beamSettings.getSelectedU2DMXdeviceName() == 'None': device = self.U2DMXpatternSelectorDropdown.Disable()
        self.U2DMXpatternSelectorDropdown.Bind(wx.EVT_COMBOBOX, self.OnSelectU2DMXpattern)
        vbox.Add(self.dmxcontrols, flag=wx.LEFT | wx.TOP | wx.BOTTOM, border=10)
        vbox.Add(self.dmxdescription, flag=wx.LEFT, border=10)
        hbox1.Add(self.U1description, flag=wx.LEFT | wx.TOP, border=10)
        hbox1.Add(self.U1DMXfixtureColourList, flag=wx.LEFT | wx.TOP, border=10)
        hbox1.Add(self.U1DMXpatternSelectorDropdown, flag=wx.LEFT | wx.TOP, border=10)

        hbox2.Add(self.U2description, flag=wx.LEFT | wx.TOP, border=10)
        hbox2.Add(self.U2DMXfixtureColourList, flag=wx.LEFT | wx.TOP, border=10)
        hbox2.Add(self.U2DMXpatternSelectorDropdown, flag=wx.LEFT | wx.TOP, border=10)

        ###########
        # BUTTONS #
        ###########
        self.runU1Btn = wx.Button(self, label="Run Pattern")
        self.runU1Btn.Bind(wx.EVT_BUTTON, self.onU1Run)
        if self.beamSettings.getSelectedU1DMXdeviceName() == 'None': device = self.runU1Btn.Disable()
        hbox1.Add(self.runU1Btn, flag=wx.ALL, border=10)
        self.runU2Btn = wx.Button(self, label="Run Pattern")
        if self.beamSettings.getSelectedU2DMXdeviceName() == 'None': device = self.runU2Btn.Disable()
        self.runU2Btn.Bind(wx.EVT_BUTTON, self.onU2Run)
        hbox2.Add(self.runU2Btn, flag=wx.ALL, border=10)

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
    # def OnSelectDMXdevice(self, event):
    #    self.beamSettings.setSelectedU1DMXdeviceName(self.U1DMXdeviceSelectorDropdown.GetValue())
    def onU1ListItemSelected(self, event):
        currentitem = self.U1DMXfixtureList.GetSelection()
        logging.debug("... currentitem: " + str(currentitem))
        return currentitem

    def onU1Add(self, event):
        u1 = None
        u1 = self.beamSettings._Universe1
        newfixture = self.DMXdeviceSelectorDropdown.GetValue()
        u1.AddFixture(newfixture)
        logging.debug("... newfixture: " + str(newfixture))
        logging.debug("... u1: " + str(u1.FixtureNames()))
        self.U1DMXfixtureList.Clear()
        self.U1DMXfixtureColourList.Clear()
        u1n = u1.FixtureNames()
        u1a = u1.FixtureAddresses()
        u1c = u1.FixtureColours()
        for index, value in enumerate(u1n):
            self.U1DMXfixtureList.Append('(' + u1a[index] + ') ' + value)
            self.U1DMXfixtureColourList.Append(u1c[index])
        self.beamSettings.setDMXuniverse1(u1)

    def onU2Add(self, event):
        u2 = None
        u2 = self.beamSettings._Universe2
        newfixture = self.DMXdeviceSelectorDropdown.GetValue()
        u2.AddFixture(newfixture)
        logging.debug("... newfixture: " + str(newfixture))
        logging.debug("... u2: " + str(u2.FixtureNames()))
        self.U2DMXfixtureList.Clear()
        self.U2DMXfixtureColourList.Clear()
        u2n = u2.FixtureNames()
        u2a = u2.FixtureAddresses()
        u2c = u2.FixtureColours()
        for index, value in enumerate(u2n):
            self.U2DMXfixtureList.Append('(' + u2a[index] + ') ' + value)
            self.U2DMXfixtureColourList.Append(u2c[index])
        self.beamSettings.setDMXuniverse2(u2)

    def onU1Del(self, event):
        u1 = None
        u1 = self.beamSettings._Universe1
        newfixture = self.U1DMXfixtureList.GetSelection()
        u1.DelFixture(newfixture)
        logging.debug("... newfixture: " + str(newfixture))
        logging.debug("... u1: " + str(u1.FixtureNames()))
        self.U1DMXfixtureList.Clear()
        self.U1DMXfixtureColourList.Clear()
        u1n = u1.FixtureNames()
        u1a = u1.FixtureAddresses()
        u1c = u1.FixtureColours()
        for index, value in enumerate(u1n):
            self.U1DMXfixtureList.Append('(' + u1a[index] + ') ' + value)
            self.U1DMXfixtureColourList.Append(u1c[index])
        self.beamSettings.setDMXuniverse1(u1)
        logging.debug("... u1 count: " + str(self.U1DMXfixtureList.GetCount()))

    def onU2Del(self, event):
        u2 = None
        u2 = self.beamSettings._Universe2
        newfixture = self.U2DMXfixtureList.GetSelection()
        u2.DelFixture(newfixture)
        logging.debug("... newfixture: " + str(newfixture))
        logging.debug("... u2: " + str(u2.FixtureNames()))
        self.U2DMXfixtureList.Clear()
        self.U2DMXfixtureColourList.Clear()
        u2n = u2.FixtureNames()
        u2a = u2.FixtureAddresses()
        u2c = u2.FixtureColours()
        for index, value in enumerate(u2n):
            self.U2DMXfixtureList.Append('(' + u2a[index] + ') ' + value)
            self.U2DMXfixtureColourList.Append(u2c[index])
        self.beamSettings.setDMXuniverse2(u2)

    def OnSelectU1DMXpattern(self, event):
        fixtureindices = self.U1DMXfixtureColourList.GetSelections()
        self.U1CurrentColour = self.U1DMXpatternSelectorDropdown.GetValue()
        u1 = self.beamSettings._Universe1
        u1.setFixtureColours(self.U1CurrentColour, fixtureindices)
        self.U1DMXfixtureColourList.Clear()
        u1n = u1.FixtureNames()
        u1c = u1.FixtureColours()
        for index, value in enumerate(u1n):
            self.U1DMXfixtureColourList.Append(u1c[index])
    def OnSelectU2DMXpattern(self, event):
        fixtureindices = self.U2DMXfixtureColourList.GetSelections()
        self.U2CurrentColour = self.U2DMXpatternSelectorDropdown.GetValue()
        u2 = self.beamSettings._Universe2
        u2.setFixtureColours(self.U2CurrentColour, fixtureindices)
        self.U2DMXfixtureColourList.Clear()
        u2n = u2.FixtureNames()
        u2c = u2.FixtureColours()
        for index, value in enumerate(u2n):
            self.U2DMXfixtureColourList.Append(u2c[index])

    def onU1Run(self, event):
        u = self.beamSettings._Universe1
        colourpattern = u.FixturePatterns()
        logging.debug("... U1 colourpattern: " + str(colourpattern))
        if self.beamSettings._oladIsRunning :
            if (0 < len(colourpattern)): olamodule.sendDMXrequest(1, colourpattern)

    def onU2Run(self, event):
        u = self.beamSettings._Universe2
        colourpattern = u.FixturePatterns()
        logging.debug("... U2 colourpattern: " + str(colourpattern))
        if self.beamSettings._oladIsRunning :
            if (0 < len(colourpattern)): olamodule.sendDMXrequest(2, colourpattern)

###################################################################
#                             EOF                                 #
###################################################################
