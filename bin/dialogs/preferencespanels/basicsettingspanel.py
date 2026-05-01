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

import socket

import wx
from bin.beamutils import logLevelList, setLogLevel


VIRTUALDJ_INTEGRATION_MODES = ['History File', 'Network Control']
VIRTUALDJ_QUERY_MODES = ['Master', 'Deck 1', 'Deck 2', 'Left', 'Right']


###################################################################
#                      BasicSettingsTab                           #
###################################################################
class BasicSettingsPanel(wx.Panel):
    def __init__(self, parent, BeamSettings):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
        
        #############
        # VARIABLES #
        #############
        self.BeamSettings = BeamSettings
        self.networkBindDisplayHost = self.getNetworkHostDisplayValue()
        
        ##########
        # SIZERS #
        ##########
        outer_vbox = wx.BoxSizer(wx.VERTICAL)
        self.scrolledWindow = wx.ScrolledWindow(self, wx.ID_ANY, style=wx.VSCROLL)
        self.scrolledWindow.SetScrollRate(0, 20)
        self.scrolledWindow.SetMinSize((360, -1))

        content_vbox = wx.BoxSizer(wx.VERTICAL)
        
        #########################
        # MEDIA PLAYER SELECTOR #
        #########################
        mediaplayer = wx.StaticText(self.scrolledWindow, wx.ID_ANY, "Mediaplayer       ")
        font = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        mediaplayer.SetFont(font)
        
        mediadescription = wx.StaticText(self.scrolledWindow, wx.ID_ANY, "Select mediaplayer to display information from")
        self.ModuleSelectorDropdown = wx.ComboBox(self.scrolledWindow, wx.ID_ANY,
                                                  value = self.BeamSettings.getSelectedModuleName(),
                                                  choices = self.BeamSettings._moduleNames,
                                                  size=(233, -1),
                                                  style=wx.CB_READONLY)
        self.ModuleSelectorDropdown.Bind(wx.EVT_COMBOBOX, self.OnSelectMediaPlayer)
        content_vbox.Add(mediaplayer, flag=wx.LEFT | wx.TOP | wx.BOTTOM, border=10)
        content_vbox.Add(mediadescription, flag=wx.LEFT, border=20)
        content_vbox.Add(self.ModuleSelectorDropdown, flag=wx.LEFT | wx.RIGHT, border=20)

        self.foobarControls = []
        self.virtualDjCommonControls = []
        self.virtualDjHistoryControls = []
        self.virtualDjNetworkControls = []
        
        
        ############
        # Settings #
        ############
        settingslabel = wx.StaticText(self.scrolledWindow, -1, "Settings          ")
        font = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        settingslabel.SetFont(font)
        content_vbox.Add(settingslabel, flag=wx.LEFT | wx.TOP | wx.BOTTOM, border=10)
        
        
        ################
        # REFRESH TIME #
        ################
        refreshtime = wx.StaticText(self.scrolledWindow, -1, "Mediaplayer Refresh Time")
        self.RefreshTime = wx.Slider(self.scrolledWindow, -1, int(self.BeamSettings.getUpdtime()), 500, 10000, (0, 0), (233, -1), wx.SL_HORIZONTAL)
        self.RefreshTimeLabel = wx.StaticText(self.scrolledWindow, -1, "")
        self.RefreshTime.Bind(wx.EVT_SCROLL, self.OnRefreshTimerScroll)
        content_vbox.Add(refreshtime, flag=wx.LEFT, border=20)
        hboxRefresh = wx.BoxSizer(wx.HORIZONTAL)
        hboxRefresh.Add(self.RefreshTime, flag= wx.LEFT | wx.RIGHT | wx.TOP, border=7)
        hboxRefresh.Add(self.RefreshTimeLabel, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=7)
        content_vbox.Add(hboxRefresh, flag=wx.LEFT, border=20)
        self.updateRefreshTimeLabel()
        
        ################
        # TANDA LENGTH #
        ################
        tandalength = wx.StaticText(self.scrolledWindow, -1, "Max. Tanda Length")
        self.TandaLength = wx.Slider(self.scrolledWindow, -1, self.BeamSettings.getMaxTandaLength(), 0, 10,(0,0), (233,-1), wx.SL_HORIZONTAL)
        self.TandaLengthLabel = wx.StaticText(self.scrolledWindow, -1, "")
        self.TandaLength.Bind(wx.EVT_SCROLL, self.OnTandaLengthScroll)
        self.updateTandaLengthLabel()
        content_vbox.Add(tandalength, flag=wx.LEFT, border=20)
        hboxTanda = wx.BoxSizer(wx.HORIZONTAL)
        hboxTanda.Add(self.TandaLength, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=7)
        hboxTanda.Add(self.TandaLengthLabel, flag=wx.LEFT | wx.TOP, border=7)
        content_vbox.Add(hboxTanda, flag=wx.LEFT, border=20)
        

        '''        
        ################
        #   LOGGING    #
        ################
        logging = wx.StaticText(self, -1, "Logging (require restart)")
        self.LogCheckBox = wx.CheckBox(self, label='Log to '+self.BeamSettings._logPath)
        if self.BeamSettings._logging == 'True':
            self.LogCheckBox.SetValue(True)
        else:
            self.LogCheckBox.SetValue(False)
        self.LogCheckBox.Bind(wx.EVT_CHECKBOX, self.OnLoggingBox)
        vbox.Add(logging, flag=wx.LEFT, border=20)
        hboxLog = wx.BoxSizer(wx.HORIZONTAL)
        hboxLog.Add(self.LogCheckBox, flag=wx.LEFT | wx.RIGHT | wx.TOP | wx.BOTTOM, border=7)
        vbox.Add(hboxLog, flag=wx.LEFT, border=20)
        '''

        loglevel = wx.StaticText(self.scrolledWindow, wx.ID_ANY, "Logging Level            ")
        font = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        loglevel.SetFont(font)

        logleveldescription = wx.StaticText(self.scrolledWindow, wx.ID_ANY, "Select Log Level")
        self.LogLevelSelectorDropdown = wx.ComboBox(self.scrolledWindow, wx.ID_ANY,
                                                    value=self.BeamSettings.getLogLevel(),
                                                    choices=logLevelList,
                                                    size=(233, -1),
                                                    style=wx.CB_READONLY)
        self.LogLevelSelectorDropdown.Bind(wx.EVT_COMBOBOX, self.OnSelectLogLevel)
        content_vbox.Add(loglevel, flag=wx.LEFT | wx.TOP | wx.BOTTOM, border=10)
        content_vbox.Add(logleveldescription, flag=wx.LEFT, border=20)
        content_vbox.Add(self.LogLevelSelectorDropdown, flag=wx.LEFT | wx.RIGHT, border=20)

        networklabel = wx.StaticText(self.scrolledWindow, wx.ID_ANY, "Network Display        ")
        font = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        networklabel.SetFont(font)

        networkdescription = wx.StaticText(self.scrolledWindow, wx.ID_ANY, "Expose the current Beam display to browsers on your network.")
        self.NetworkEnabledCheckBox = wx.CheckBox(self.scrolledWindow, label='Enable network display')
        self.NetworkEnabledCheckBox.SetValue(self.BeamSettings.getNetworkServiceEnabled())
        self.NetworkEnabledCheckBox.Bind(wx.EVT_CHECKBOX, self.OnNetworkEnabled)

        hostlabel = wx.StaticText(self.scrolledWindow, wx.ID_ANY, "Host")
        self.NetworkHostField = wx.TextCtrl(self.scrolledWindow, wx.ID_ANY, value=self.networkBindDisplayHost, size=(233, -1))
        self.NetworkHostField.Bind(wx.EVT_TEXT, self.OnNetworkHostChanged)
        self.NetworkHostField.SetToolTip('Host or IP address to bind the network display service to. Use 0.0.0.0 to listen on all interfaces.')

        self.NetworkAddressHint = wx.StaticText(self.scrolledWindow, wx.ID_ANY, "")

        portlabel = wx.StaticText(self.scrolledWindow, wx.ID_ANY, "Port (default 8765)")
        self.NetworkPortField = wx.SpinCtrl(self.scrolledWindow, wx.ID_ANY, min=1, max=65535, initial=self.BeamSettings.getNetworkServicePort(), size=(100, -1))
        self.NetworkPortField.Bind(wx.EVT_SPINCTRL, self.OnNetworkPortChanged)
        self.NetworkPortField.Bind(wx.EVT_TEXT, self.OnNetworkPortChanged)
        self.NetworkPortField.SetToolTip('Change the HTTP/WebSocket port for the network display service. Default: 8765.')

        foobarlabel = wx.StaticText(self.scrolledWindow, wx.ID_ANY, "Foobar2000 Beefweb")
        font = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        foobarlabel.SetFont(font)

        foobardescription = wx.StaticText(self.scrolledWindow, wx.ID_ANY, "These settings are used only when Foobar2000 is the selected media player.")

        foobarurllabel = wx.StaticText(self.scrolledWindow, wx.ID_ANY, "Beefweb URL")
        self.FoobarUrlField = wx.TextCtrl(self.scrolledWindow, wx.ID_ANY, value=self.BeamSettings.getFoobarBeefwebUrl(), size=(233, -1))
        self.FoobarUrlField.Bind(wx.EVT_TEXT, self.OnFoobarUrlChanged)

        foobaruserlabel = wx.StaticText(self.scrolledWindow, wx.ID_ANY, "Beefweb Username")
        self.FoobarUserField = wx.TextCtrl(self.scrolledWindow, wx.ID_ANY, value=self.BeamSettings.getFoobarBeefwebUser(), size=(233, -1))
        self.FoobarUserField.Bind(wx.EVT_TEXT, self.OnFoobarUserChanged)

        foobarpasswordlabel = wx.StaticText(self.scrolledWindow, wx.ID_ANY, "Beefweb Password")
        self.FoobarPasswordField = wx.TextCtrl(self.scrolledWindow, wx.ID_ANY, value=self.BeamSettings.getFoobarBeefwebPassword(), size=(233, -1), style=wx.TE_PASSWORD)
        self.FoobarPasswordField.Bind(wx.EVT_TEXT, self.OnFoobarPasswordChanged)

        self.foobarControls = [
            foobarlabel,
            foobardescription,
            foobarurllabel,
            self.FoobarUrlField,
            foobaruserlabel,
            self.FoobarUserField,
            foobarpasswordlabel,
            self.FoobarPasswordField,
        ]

        content_vbox.Add(foobarlabel, flag=wx.LEFT | wx.TOP | wx.BOTTOM, border=10)
        content_vbox.Add(foobardescription, flag=wx.LEFT, border=20)
        content_vbox.Add(foobarurllabel, flag=wx.LEFT | wx.TOP, border=20)
        content_vbox.Add(self.FoobarUrlField, flag=wx.LEFT | wx.RIGHT, border=20)
        content_vbox.Add(foobaruserlabel, flag=wx.LEFT | wx.TOP, border=20)
        content_vbox.Add(self.FoobarUserField, flag=wx.LEFT | wx.RIGHT, border=20)
        content_vbox.Add(foobarpasswordlabel, flag=wx.LEFT | wx.TOP, border=20)
        content_vbox.Add(self.FoobarPasswordField, flag=wx.LEFT | wx.RIGHT, border=20)

        virtualdjlabel = wx.StaticText(self.scrolledWindow, wx.ID_ANY, "VirtualDJ")
        font = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        virtualdjlabel.SetFont(font)

        virtualdjdescription = wx.StaticText(self.scrolledWindow, wx.ID_ANY, "History File works without VirtualDJ Pro. Network Control requires the optional Pro plugin.")

        virtualdjintegrationlabel = wx.StaticText(self.scrolledWindow, wx.ID_ANY, "Integration")
        self.VirtualDJIntegrationDropdown = wx.ComboBox(self.scrolledWindow, wx.ID_ANY,
                                value=self.BeamSettings.getVirtualDJIntegrationMode(),
                                choices=VIRTUALDJ_INTEGRATION_MODES,
                                size=(233, -1),
                                style=wx.CB_READONLY)
        self.VirtualDJIntegrationDropdown.Bind(wx.EVT_COMBOBOX, self.OnVirtualDJIntegrationModeChanged)

        virtualdjhistorypathlabel = wx.StaticText(self.scrolledWindow, wx.ID_ANY, "History File Path")
        self.VirtualDJHistoryPathField = wx.TextCtrl(self.scrolledWindow, wx.ID_ANY, value=self.BeamSettings.getVirtualDJHistoryPath(), size=(233, -1))
        self.VirtualDJHistoryPathField.Bind(wx.EVT_TEXT, self.OnVirtualDJHistoryPathChanged)
        self.VirtualDJHistoryPathField.SetToolTip('Optional override for VirtualDJ tracklist.txt or a History folder. Leave blank for auto-detection.')

        virtualdjrecentwindowlabel = wx.StaticText(self.scrolledWindow, wx.ID_ANY, "Recent Track Window (sec)")
        self.VirtualDJRecentWindowField = wx.SpinCtrl(self.scrolledWindow, wx.ID_ANY, min=0, max=86400, initial=self.BeamSettings.getVirtualDJRecentTrackWindowSec(), size=(100, -1))
        self.VirtualDJRecentWindowField.Bind(wx.EVT_SPINCTRL, self.OnVirtualDJRecentTrackWindowChanged)
        self.VirtualDJRecentWindowField.Bind(wx.EVT_TEXT, self.OnVirtualDJRecentTrackWindowChanged)
        self.VirtualDJRecentWindowField.SetToolTip('How long a history file entry stays fresh before Beam treats VirtualDJ as stopped. Use 0 to disable staleness checks.')

        virtualdjhostlabel = wx.StaticText(self.scrolledWindow, wx.ID_ANY, "Host")
        self.VirtualDJHostField = wx.TextCtrl(self.scrolledWindow, wx.ID_ANY, value=self.BeamSettings.getVirtualDJHost(), size=(233, -1))
        self.VirtualDJHostField.Bind(wx.EVT_TEXT, self.OnVirtualDJHostChanged)
        self.VirtualDJHostField.SetToolTip('Host or IP address where the VirtualDJ Network Control plugin is listening.')

        virtualdjportlabel = wx.StaticText(self.scrolledWindow, wx.ID_ANY, "Port")
        self.VirtualDJPortField = wx.SpinCtrl(self.scrolledWindow, wx.ID_ANY, min=1, max=65535, initial=self.BeamSettings.getVirtualDJPort(), size=(100, -1))
        self.VirtualDJPortField.Bind(wx.EVT_SPINCTRL, self.OnVirtualDJPortChanged)
        self.VirtualDJPortField.Bind(wx.EVT_TEXT, self.OnVirtualDJPortChanged)
        self.VirtualDJPortField.SetToolTip('Port configured in the VirtualDJ Network Control plugin. Default: 80.')

        virtualdjtokenlabel = wx.StaticText(self.scrolledWindow, wx.ID_ANY, "Bearer Token")
        self.VirtualDJTokenField = wx.TextCtrl(self.scrolledWindow, wx.ID_ANY, value=self.BeamSettings.getVirtualDJBearerToken(), size=(233, -1), style=wx.TE_PASSWORD)
        self.VirtualDJTokenField.Bind(wx.EVT_TEXT, self.OnVirtualDJBearerTokenChanged)
        self.VirtualDJTokenField.SetToolTip('Optional authentication token configured in the VirtualDJ Network Control plugin.')

        virtualdjquerymodelabel = wx.StaticText(self.scrolledWindow, wx.ID_ANY, "Track Source")
        self.VirtualDJQueryModeDropdown = wx.ComboBox(self.scrolledWindow, wx.ID_ANY,
                                                      value=self.BeamSettings.getVirtualDJQueryMode(),
                                                      choices=VIRTUALDJ_QUERY_MODES,
                                                      size=(233, -1),
                                                      style=wx.CB_READONLY)
        self.VirtualDJQueryModeDropdown.Bind(wx.EVT_COMBOBOX, self.OnVirtualDJQueryModeChanged)

        self.virtualDjCommonControls = [
            virtualdjlabel,
            virtualdjdescription,
            virtualdjintegrationlabel,
            self.VirtualDJIntegrationDropdown,
        ]

        self.virtualDjHistoryControls = [
            virtualdjhistorypathlabel,
            self.VirtualDJHistoryPathField,
            virtualdjrecentwindowlabel,
            self.VirtualDJRecentWindowField,
        ]

        self.virtualDjNetworkControls = [
            virtualdjhostlabel,
            self.VirtualDJHostField,
            virtualdjportlabel,
            self.VirtualDJPortField,
            virtualdjtokenlabel,
            self.VirtualDJTokenField,
            virtualdjquerymodelabel,
            self.VirtualDJQueryModeDropdown,
        ]

        content_vbox.Add(virtualdjlabel, flag=wx.LEFT | wx.TOP | wx.BOTTOM, border=10)
        content_vbox.Add(virtualdjdescription, flag=wx.LEFT, border=20)
        content_vbox.Add(virtualdjintegrationlabel, flag=wx.LEFT | wx.TOP, border=20)
        content_vbox.Add(self.VirtualDJIntegrationDropdown, flag=wx.LEFT | wx.RIGHT, border=20)
        content_vbox.Add(virtualdjhistorypathlabel, flag=wx.LEFT | wx.TOP, border=20)
        content_vbox.Add(self.VirtualDJHistoryPathField, flag=wx.LEFT | wx.RIGHT, border=20)
        content_vbox.Add(virtualdjrecentwindowlabel, flag=wx.LEFT | wx.TOP, border=20)
        content_vbox.Add(self.VirtualDJRecentWindowField, flag=wx.LEFT, border=20)
        content_vbox.Add(virtualdjhostlabel, flag=wx.LEFT | wx.TOP, border=20)
        content_vbox.Add(self.VirtualDJHostField, flag=wx.LEFT | wx.RIGHT, border=20)
        content_vbox.Add(virtualdjportlabel, flag=wx.LEFT | wx.TOP, border=20)
        content_vbox.Add(self.VirtualDJPortField, flag=wx.LEFT, border=20)
        content_vbox.Add(virtualdjtokenlabel, flag=wx.LEFT | wx.TOP, border=20)
        content_vbox.Add(self.VirtualDJTokenField, flag=wx.LEFT | wx.RIGHT, border=20)
        content_vbox.Add(virtualdjquerymodelabel, flag=wx.LEFT | wx.TOP, border=20)
        content_vbox.Add(self.VirtualDJQueryModeDropdown, flag=wx.LEFT | wx.RIGHT, border=20)

        content_vbox.Add(networklabel, flag=wx.LEFT | wx.TOP | wx.BOTTOM, border=10)
        content_vbox.Add(networkdescription, flag=wx.LEFT, border=20)
        content_vbox.Add(self.NetworkEnabledCheckBox, flag=wx.LEFT | wx.TOP, border=20)
        content_vbox.Add(hostlabel, flag=wx.LEFT | wx.TOP, border=20)
        content_vbox.Add(self.NetworkHostField, flag=wx.LEFT | wx.RIGHT, border=20)
        content_vbox.Add(self.NetworkAddressHint, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=20)
        content_vbox.Add(portlabel, flag=wx.LEFT | wx.TOP, border=20)
        content_vbox.Add(self.NetworkPortField, flag=wx.LEFT, border=20)


        ##############
        # SET SIZERS #
        ##############
        self.scrolledWindow.SetSizer(content_vbox)
        content_vbox.SetMinSize((340, -1))
        self.scrolledWindow.FitInside()
        outer_vbox.Add(self.scrolledWindow, 1, wx.EXPAND)
        self.SetSizer(outer_vbox)
        self.updateModuleSpecificSettingsVisibility(self.BeamSettings.getSelectedModuleName())
        self.updateNetworkAddressHint()

    def reloadFromSettings(self):
        self.ModuleSelectorDropdown.SetValue(self.BeamSettings.getSelectedModuleName())
        self.RefreshTime.SetValue(int(self.BeamSettings.getUpdtime()))
        self.TandaLength.SetValue(int(self.BeamSettings.getMaxTandaLength()))
        self.LogLevelSelectorDropdown.SetValue(self.BeamSettings.getLogLevel())
        self.NetworkEnabledCheckBox.SetValue(self.BeamSettings.getNetworkServiceEnabled())
        self.networkBindDisplayHost = self.getNetworkHostDisplayValue()
        self.NetworkHostField.ChangeValue(self.networkBindDisplayHost)
        self.NetworkPortField.SetValue(self.BeamSettings.getNetworkServicePort())
        self.FoobarUrlField.ChangeValue(self.BeamSettings.getFoobarBeefwebUrl())
        self.FoobarUserField.ChangeValue(self.BeamSettings.getFoobarBeefwebUser())
        self.FoobarPasswordField.ChangeValue(self.BeamSettings.getFoobarBeefwebPassword())
        self.VirtualDJIntegrationDropdown.SetValue(self.BeamSettings.getVirtualDJIntegrationMode())
        self.VirtualDJHistoryPathField.ChangeValue(self.BeamSettings.getVirtualDJHistoryPath())
        self.VirtualDJRecentWindowField.SetValue(self.BeamSettings.getVirtualDJRecentTrackWindowSec())
        self.VirtualDJHostField.ChangeValue(self.BeamSettings.getVirtualDJHost())
        self.VirtualDJPortField.SetValue(self.BeamSettings.getVirtualDJPort())
        self.VirtualDJTokenField.ChangeValue(self.BeamSettings.getVirtualDJBearerToken())
        self.VirtualDJQueryModeDropdown.SetValue(self.BeamSettings.getVirtualDJQueryMode())
        self.updateRefreshTimeLabel()
        self.updateTandaLengthLabel()
        self.updateModuleSpecificSettingsVisibility(self.BeamSettings.getSelectedModuleName())
        self.updateNetworkAddressHint()






###################################################################
#                           EVENTS                                #
###################################################################

    def OnSelectMediaPlayer(self, event):
        module_name = self.ModuleSelectorDropdown.GetValue()
        self.BeamSettings.setSelectedModuleName(module_name)
        self.updateModuleSpecificSettingsVisibility(module_name)
    def OnSelectU1DMXdevice(self, event):
        self.BeamSettings.setSelectedU1DMXdeviceName(self.U1DMXdeviceSelectorDropdown.GetValue())
    def OnSelectU2DMXdevice(self, event):
        self.BeamSettings.setSelectedU2DMXdeviceName(self.U2DMXdeviceSelectorDropdown.GetValue())

    def OnSelectLogLevel(self, event):
        self.BeamSettings.setLogLevel(self.LogLevelSelectorDropdown.GetValue())
        setLogLevel(self.BeamSettings.getLogLevel())

    def OnNetworkEnabled(self, event):
        self.BeamSettings.setNetworkServiceEnabled(self.NetworkEnabledCheckBox.GetValue())
        self.updateNetworkAddressHint()

    def OnNetworkHostChanged(self, event):
        host_value = self.NetworkHostField.GetValue()
        self.BeamSettings.setNetworkServiceHost(host_value)
        self.networkBindDisplayHost = host_value.strip() or self.getNetworkHostDisplayValue()
        self.updateNetworkAddressHint()

    def OnNetworkPortChanged(self, event):
        self.BeamSettings.setNetworkServicePort(self.NetworkPortField.GetValue())
        self.updateNetworkAddressHint()

    def OnFoobarUrlChanged(self, event):
        self.BeamSettings.setFoobarBeefwebUrl(self.FoobarUrlField.GetValue())

    def OnFoobarUserChanged(self, event):
        self.BeamSettings.setFoobarBeefwebUser(self.FoobarUserField.GetValue())

    def OnFoobarPasswordChanged(self, event):
        self.BeamSettings.setFoobarBeefwebPassword(self.FoobarPasswordField.GetValue())

    def OnVirtualDJHostChanged(self, event):
        self.BeamSettings.setVirtualDJHost(self.VirtualDJHostField.GetValue())

    def OnVirtualDJPortChanged(self, event):
        self.BeamSettings.setVirtualDJPort(self.VirtualDJPortField.GetValue())

    def OnVirtualDJIntegrationModeChanged(self, event):
        self.BeamSettings.setVirtualDJIntegrationMode(self.VirtualDJIntegrationDropdown.GetValue())
        self.updateModuleSpecificSettingsVisibility(self.BeamSettings.getSelectedModuleName())

    def OnVirtualDJHistoryPathChanged(self, event):
        self.BeamSettings.setVirtualDJHistoryPath(self.VirtualDJHistoryPathField.GetValue())

    def OnVirtualDJRecentTrackWindowChanged(self, event):
        self.BeamSettings.setVirtualDJRecentTrackWindowSec(self.VirtualDJRecentWindowField.GetValue())

    def OnVirtualDJBearerTokenChanged(self, event):
        self.BeamSettings.setVirtualDJBearerToken(self.VirtualDJTokenField.GetValue())

    def OnVirtualDJQueryModeChanged(self, event):
        self.BeamSettings.setVirtualDJQueryMode(self.VirtualDJQueryModeDropdown.GetValue())

    def updateModuleSpecificSettingsVisibility(self, moduleName):
        show_foobar_settings = moduleName == 'Foobar2000'
        for control in self.foobarControls:
            control.Show(show_foobar_settings)

        show_virtualdj_settings = moduleName == 'VirtualDJ'
        for control in self.virtualDjCommonControls:
            control.Show(show_virtualdj_settings)

        show_virtualdj_history_controls = show_virtualdj_settings and self.BeamSettings.getVirtualDJIntegrationMode() == 'History File'
        for control in self.virtualDjHistoryControls:
            control.Show(show_virtualdj_history_controls)

        show_virtualdj_network_controls = show_virtualdj_settings and self.BeamSettings.getVirtualDJIntegrationMode() == 'Network Control'
        for control in self.virtualDjNetworkControls:
            control.Show(show_virtualdj_network_controls)

        self.scrolledWindow.FitInside()
        self.Layout()
        if self.GetParent() is not None:
            self.GetParent().Layout()

    def getNetworkHostDisplayValue(self):
        configured_host = self.BeamSettings.getNetworkServiceHost().strip()
        if configured_host in ('', '0.0.0.0', '::'):
            return self.getLocalNetworkIpAddress()
        return configured_host

    def getLocalNetworkIpAddress(self):
        fallback_ip = '127.0.0.1'

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe_socket:
                probe_socket.connect(('8.8.8.8', 80))
                detected_ip = probe_socket.getsockname()[0]
                if detected_ip:
                    return detected_ip
        except OSError:
            pass

        try:
            hostname_ip = socket.gethostbyname(socket.gethostname())
            if hostname_ip and not hostname_ip.startswith('127.'):
                return hostname_ip
        except OSError:
            pass

        return fallback_ip

    def updateNetworkAddressHint(self):
        configured_host = self.BeamSettings.getNetworkServiceHost().strip()
        display_host = self.NetworkHostField.GetValue().strip() or self.getNetworkHostDisplayValue()
        port = self.BeamSettings.getNetworkServicePort()

        if configured_host in ('', '0.0.0.0', '::'):
            self.NetworkAddressHint.SetLabel('Local address: http://{0}:{1}  (binding to all interfaces)'.format(display_host, port))
            return

        if configured_host in ('127.0.0.1', 'localhost', '::1'):
            self.NetworkAddressHint.SetLabel('Local-only address: http://{0}:{1}'.format(display_host, port))
            return

        self.NetworkAddressHint.SetLabel('Address: http://{0}:{1}'.format(display_host, port))

    ################
    # REFRESH TIME #
    ################
    def updateRefreshTimeLabel(self):
        timer_value = round(float(self.RefreshTime.GetValue()) / 1000, 1)
        if timer_value < float(2.0):
            self.RefreshTimeLabel.SetLabel(str(timer_value) + " sec (Fast)")
        elif timer_value < float(5.0):
            self.RefreshTimeLabel.SetLabel(str(timer_value) + " sec (Medium)")
        else:
            self.RefreshTimeLabel.SetLabel(str(timer_value) + " sec (Slow)")

    def OnRefreshTimerScroll(self, event = wx.EVT_SCROLL):
        self.BeamSettings.setUpdtime(self.RefreshTime.GetValue())
        self.updateRefreshTimeLabel()

    ################
    # TANDA LENGTH #
    ################
    def updateTandaLengthLabel(self):
        tanda_length = int(self.TandaLength.GetValue())
        if tanda_length > 0:
            self.TandaLengthLabel.SetLabel(str(tanda_length) + " songs")
        else:
            self.TandaLengthLabel.SetLabel("No preview")

    def OnTandaLengthScroll(self, event = wx.EVT_SCROLL):
        self.BeamSettings.setMaxTandaLength( self.TandaLength.GetValue())
        self.updateTandaLengthLabel()

    ################
    #   LOGGING    #
    ################
    def OnLoggingBox(self, event):
        if self.LogCheckBox.GetValue():
            self.BeamSettings.setLogging('True')
        else:
            self.BeamSettings.setLogging('False')


###################################################################
#                             EOF                                 #
###################################################################
