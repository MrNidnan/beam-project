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

###################################################################
#                      BasicSettingsTab                           #
###################################################################
class BasicSettings(wx.Panel):
    def __init__(self, parent, BeamSettings):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
        self.BeamSettings = BeamSettings
        self.parent = parent
        
        ##########
        # SIZERS #
        ##########
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        #########################
        # MEDIA PLAYER SELECTOR #
        #########################
        mediaplayer = wx.StaticText(self, wx.ID_ANY, "Mediaplayer")
        font = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        mediaplayer.SetFont(font)
        
        mediadescription = wx.StaticText(self, wx.ID_ANY, "Select mediaplayer to display information from")
        self.ModuleSelectorDropdown = wx.ComboBox(self, wx.ID_ANY,value=self.BeamSettings._moduleSelected, choices=self.BeamSettings._currentModules, style=wx.CB_READONLY)
        self.ModuleSelectorDropdown.Bind(wx.EVT_COMBOBOX, self.OnSelectMediaPlayer)
        vbox.Add(mediaplayer, flag=wx.LEFT | wx.TOP | wx.BOTTOM, border=10)
        vbox.Add(mediadescription, flag=wx.LEFT, border=20)
        vbox.Add(self.ModuleSelectorDropdown, flag=wx.LEFT, border=20)
        
        
        ############
        # Settings #
        ############
        settingslabel = wx.StaticText(self, -1, "Settings")
        font = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        settingslabel.SetFont(font)
        vbox.Add(settingslabel, flag=wx.LEFT | wx.TOP | wx.BOTTOM, border=10)
        
        
        ################
        # REFRESH TIME #
        ################
        refreshtime = wx.StaticText(self, -1, "Refresh time")
        self.RefreshTime = wx.Slider(self, -1, int(self.BeamSettings._updateTimer), 500, 10000,(0,0), (233,-1), wx.SL_HORIZONTAL)
        self.RefreshTimeLabel = wx.StaticText(self, -1, "")
        self.RefreshTime.Bind(wx.EVT_SCROLL, self.OnRefreshTimerScroll)
        self.OnRefreshTimerScroll()
        vbox.Add(refreshtime, flag=wx.LEFT, border=20)
        hboxRefresh = wx.BoxSizer(wx.HORIZONTAL)
        hboxRefresh.Add(self.RefreshTime, flag= wx.LEFT | wx.RIGHT | wx.TOP, border=7)
        hboxRefresh.Add(self.RefreshTimeLabel, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=7)
        vbox.Add(hboxRefresh, flag=wx.LEFT, border=20)
        
        
        ################
        # TANDA LENGTH #
        ################
        tandalength = wx.StaticText(self, -1, "Tanda Length")
        self.TandaLength = wx.Slider(self, -1, self.BeamSettings._maxTandaLength, 0, 10,(0,0), (233,-1), wx.SL_HORIZONTAL)
        self.TandaLengthLabel = wx.StaticText(self, -1, "")
        self.TandaLength.Bind(wx.EVT_SCROLL, self.OnTandaLengthScroll)
        self.OnTandaLengthScroll()
        vbox.Add(tandalength, flag=wx.LEFT, border=20)
        hboxTanda = wx.BoxSizer(wx.HORIZONTAL)
        hboxTanda.Add(self.TandaLength, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=7)
        hboxTanda.Add(self.TandaLengthLabel, flag=wx.LEFT | wx.TOP, border=7)
        vbox.Add(hboxTanda, flag=wx.LEFT, border=20)
        
        
        ################
        #   LOGGING    #
        ################
        logging = wx.StaticText(self, -1, "Logging (require restart)")
        self.LogCheckBox = wx.CheckBox(self, label='Log to '+self.BeamSettings._logPath)
        if self.BeamSettings._logging == 'True':
            self.LogCheckBox.SetValue(True)
        else:
            self.LogCheckBox.SetValue(False)
        print self.BeamSettings._logging
        self.LogCheckBox.Bind(wx.EVT_CHECKBOX, self.OnLoggingBox)
        vbox.Add(logging, flag=wx.LEFT, border=20)
        hboxLog = wx.BoxSizer(wx.HORIZONTAL)
        hboxLog.Add(self.LogCheckBox, flag=wx.LEFT | wx.RIGHT | wx.TOP | wx.BOTTOM, border=7)
        vbox.Add(hboxLog, flag=wx.LEFT, border=20)

        
        ##############
        # SET SIZERS #
        ##############
        self.SetSizer(vbox)






###################################################################
#                           EVENTS                                #
###################################################################

    #########################
    # MEDIA PLAYER SELECTOR #
    #########################
    def OnSelectMediaPlayer(self, event):
        self.BeamSettings._moduleSelected = self.ModuleSelectorDropdown.GetValue()
        # This is where callback to mainwindow should take place.

    ################
    # REFRESH TIME #
    ################
    def OnRefreshTimerScroll(self, event = wx.EVT_SCROLL):
        self.BeamSettings._updateTimer        = self.RefreshTime.GetValue()
        
        Timervalue = round(float(self.BeamSettings._updateTimer)/1000,1)
        if Timervalue < 2:
            # Fast
            self.RefreshTimeLabel.SetLabel(str(Timervalue) + " sec (Fast)")
        elif Timervalue < 5:
            # Medium
            self.RefreshTimeLabel.SetLabel(str(Timervalue) + " sec (Medium)")
        else:
            # Slow
            self.RefreshTimeLabel.SetLabel(str(Timervalue) + " sec (Slow)")
        # This is where callback to mainwindow should take place.

    ################
    # TANDA LENGTH #
    ################
    def OnTandaLengthScroll(self, event = wx.EVT_SCROLL):
        self.BeamSettings._maxTandaLength = self.TandaLength.GetValue()
        if self.BeamSettings._maxTandaLength > 0:
            self.TandaLengthLabel.SetLabel(str(self.BeamSettings._maxTandaLength) + " songs")
        else:
            self.TandaLengthLabel.SetLabel("No preview")

    ################
    #   LOGGING    #
    ################
    def OnLoggingBox(self, event):
        if self.LogCheckBox.GetValue():
            self.BeamSettings._logging = 'True'
        else:
            self.BeamSettings._logging = 'False'

###################################################################
#                             EOF                                 #
###################################################################
