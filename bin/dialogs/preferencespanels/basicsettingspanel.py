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
import platform

import wx
from bin.beamutils import logLevelList, normalizeMacControlHeight, setLogLevel
from bin.modules import mixxxutils


VIRTUALDJ_AUTO_INTEGRATION_MODE = 'Auto (Network -> History)'
VIRTUALDJ_INTEGRATION_MODES = ['History File', 'Network Control', VIRTUALDJ_AUTO_INTEGRATION_MODE]
VIRTUALDJ_HISTORY_DECK_MODES = ['-1', 'Deck 1', 'Deck 2']
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
        self.scrolledWindow.SetMinSize((760, -1))
        self.scrolledWindow.Bind(wx.EVT_SIZE, self.OnScrolledWindowSize)

        content_hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.leftColumnPanel = wx.Panel(self.scrolledWindow, wx.ID_ANY)
        self.rightColumnPanel = wx.Panel(self.scrolledWindow, wx.ID_ANY)
        left_column_vbox = wx.BoxSizer(wx.VERTICAL)
        right_column_vbox = wx.BoxSizer(wx.VERTICAL)
        self.leftColumnPanel.SetSizer(left_column_vbox)
        self.rightColumnPanel.SetSizer(right_column_vbox)

        self.virtualDjHistoryControls = []
        self.virtualDjNetworkControls = []

        self.mediaPlayerSection, media_player_grid = self._create_section(
            self.leftColumnPanel,
            "Mediaplayer",
            "Choose the active media player and refresh behavior.",
        )
        _, _, self.ModuleSelectorDropdown = self._add_section_row(
            self.mediaPlayerSection,
            media_player_grid,
            "Selected media player",
            lambda parent: self._build_media_player_dropdown(parent),
        )
        _, _, refresh_field = self._add_section_row(
            self.mediaPlayerSection,
            media_player_grid,
            "Refresh interval",
            lambda parent: self._build_refresh_interval_field(parent),
        )
        _, _, tanda_field = self._add_section_row(
            self.mediaPlayerSection,
            media_player_grid,
            "Maximum tanda length",
            lambda parent: self._build_tanda_length_field(parent),
        )
        refresh_field.GetSizer().Layout()
        tanda_field.GetSizer().Layout()
        self.updateRefreshTimeLabel()
        self.updateTandaLengthLabel()
        left_column_vbox.Add(self.mediaPlayerSection, flag=wx.EXPAND | wx.ALL, border=10)

        self.foobarSection, foobar_grid = self._create_section(
            self.rightColumnPanel,
            "Foobar2000 Beefweb",
            "Used only when Foobar2000 is the selected media player.",
        )
        _, _, self.FoobarUrlField = self._add_section_row(
            self.foobarSection,
            foobar_grid,
            "Beefweb URL",
            lambda parent: self._build_text_field(parent, self.BeamSettings.getFoobarBeefwebUrl(), self.OnFoobarUrlChanged),
            helper_text="Example: http://localhost:8880/api/",
        )
        _, _, self.FoobarUserField = self._add_section_row(
            self.foobarSection,
            foobar_grid,
            "Username",
            lambda parent: self._build_text_field(parent, self.BeamSettings.getFoobarBeefwebUser(), self.OnFoobarUserChanged),
        )
        _, _, self.FoobarPasswordField = self._add_section_row(
            self.foobarSection,
            foobar_grid,
            "Password",
            lambda parent: self._build_text_field(parent, self.BeamSettings.getFoobarBeefwebPassword(), self.OnFoobarPasswordChanged, style=wx.TE_PASSWORD),
            helper_text="Leave username and password blank unless Beefweb authentication is enabled.",
        )
        _, _, self.FoobarTestButton = self._add_section_row(
            self.foobarSection,
            foobar_grid,
            "Test Foobar2000",
            lambda parent: self._build_button_field(parent, 'Run test', self.OnFoobarTest),
            helper_text="Runs the current Foobar2000 integration and shows the detected status and metadata.",
        )
        right_column_vbox.Add(self.foobarSection, flag=wx.EXPAND | wx.ALL, border=10)

        self.jriverSection, jriver_grid = self._create_section(
            self.rightColumnPanel,
            "JRiver",
            "Used only when JRiver is the selected media player.",
        )
        _, _, self.JRiverTargetZoneField = self._add_section_row(
            self.jriverSection,
            jriver_grid,
            "Target zone",
            lambda parent: self._build_text_field(parent, self.BeamSettings.getJRiverTargetZone(), self.OnJRiverTargetZoneChanged),
            helper_text="Use -1 for the current/default playback zone, or enter a specific JRiver zone id.",
        )
        right_column_vbox.Add(self.jriverSection, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=10)

        self.mixxxSection, mixxx_grid = self._create_section(
            self.rightColumnPanel,
            "Mixxx",
            "Used only when Mixxx is the selected media player.",
        )
        _, _, self.MixxxDatabasePathField = self._add_section_row(
            self.mixxxSection,
            mixxx_grid,
            "Database path",
            lambda parent: self._build_text_field(parent, self.getMixxxDatabasePathDisplayValue(), self.OnMixxxDatabasePathChanged),
            helper_text="Prefilled with the platform default path. Change it if your Mixxx sqlite database lives somewhere else.",
        )
        _, _, self.MixxxTestButton = self._add_section_row(
            self.mixxxSection,
            mixxx_grid,
            "Test Mixxx",
            lambda parent: self._build_button_field(parent, 'Run test', self.OnMixxxTest),
            helper_text="Shows the selected database path, playback status, and current metadata detected from Mixxx.",
        )
        right_column_vbox.Add(self.mixxxSection, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=10)

        self.virtualDjSection, virtualdj_grid = self._create_section(
            self.rightColumnPanel,
            "VirtualDJ",
            "Used only when VirtualDJ is the selected media player.",
        )
        _, _, self.VirtualDJIntegrationDropdown = self._add_section_row(
            self.virtualDjSection,
            virtualdj_grid,
            "Integration",
            lambda parent: self._build_combo_field(parent, self.BeamSettings.getVirtualDJIntegrationMode(), VIRTUALDJ_INTEGRATION_MODES, self.OnVirtualDJIntegrationModeChanged),
        )
        history_path_row = self._add_section_row(
            self.virtualDjSection,
            virtualdj_grid,
            "History file path",
            lambda parent: self._build_text_field(parent, self.BeamSettings.getVirtualDJHistoryPath(), self.OnVirtualDJHistoryPathChanged),
            helper_text="Leave blank for auto-detection.",
        )
        self.VirtualDJHistoryPathField = history_path_row[2]
        self.virtualDjHistoryControls.extend(history_path_row[:2])
        recent_window_row = self._add_section_row(
            self.virtualDjSection,
            virtualdj_grid,
            "Recent track window (sec)",
            lambda parent: self._build_spin_field(parent, self.BeamSettings.getVirtualDJRecentTrackWindowSec(), self.OnVirtualDJRecentTrackWindowChanged, minimum=0, maximum=86400),
            helper_text="Use 0 to disable staleness checks.",
        )
        self.VirtualDJRecentWindowField = recent_window_row[2]
        self.virtualDjHistoryControls.extend(recent_window_row[:2])
        history_deck_row = self._add_section_row(
            self.virtualDjSection,
            virtualdj_grid,
            "History deck",
            lambda parent: self._build_combo_field(parent, self.BeamSettings.getVirtualDJHistoryDeck(), VIRTUALDJ_HISTORY_DECK_MODES, self.OnVirtualDJHistoryDeckChanged),
            helper_text="Used when reading deck-marked VirtualDJ history lines. Use -1 to accept any deck.",
        )
        self.VirtualDJHistoryDeckDropdown = history_deck_row[2]
        self.virtualDjHistoryControls.extend(history_deck_row[:2])
        virtualdj_host_row = self._add_section_row(
            self.virtualDjSection,
            virtualdj_grid,
            "Host",
            lambda parent: self._build_text_field(parent, self.BeamSettings.getVirtualDJHost(), self.OnVirtualDJHostChanged),
        )
        self.VirtualDJHostField = virtualdj_host_row[2]
        self.virtualDjNetworkControls.extend(virtualdj_host_row[:2])
        virtualdj_port_row = self._add_section_row(
            self.virtualDjSection,
            virtualdj_grid,
            "Port",
            lambda parent: self._build_spin_field(parent, self.BeamSettings.getVirtualDJPort(), self.OnVirtualDJPortChanged, minimum=1, maximum=65535),
        )
        self.VirtualDJPortField = virtualdj_port_row[2]
        self.virtualDjNetworkControls.extend(virtualdj_port_row[:2])
        virtualdj_token_row = self._add_section_row(
            self.virtualDjSection,
            virtualdj_grid,
            "Bearer token",
            lambda parent: self._build_text_field(parent, self.BeamSettings.getVirtualDJBearerToken(), self.OnVirtualDJBearerTokenChanged, style=wx.TE_PASSWORD),
            helper_text="Optional authentication token configured in the VirtualDJ Network Control plugin.",
        )
        self.VirtualDJTokenField = virtualdj_token_row[2]
        self.virtualDjNetworkControls.extend(virtualdj_token_row[:2])
        virtualdj_query_row = self._add_section_row(
            self.virtualDjSection,
            virtualdj_grid,
            "Track source",
            lambda parent: self._build_combo_field(parent, self.BeamSettings.getVirtualDJQueryMode(), VIRTUALDJ_QUERY_MODES, self.OnVirtualDJQueryModeChanged),
        )
        self.VirtualDJQueryModeDropdown = virtualdj_query_row[2]
        self.virtualDjNetworkControls.extend(virtualdj_query_row[:2])
        _, _, self.VirtualDJTestButton = self._add_section_row(
            self.virtualDjSection,
            virtualdj_grid,
            "Test VirtualDJ",
            lambda parent: self._build_button_field(parent, 'Run test', self.OnVirtualDJTest),
            helper_text="Runs the current VirtualDJ integration and shows the detected route, status, and metadata.",
        )
        right_column_vbox.Add(self.virtualDjSection, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=10)

        self.loggingSection, logging_grid = self._create_section(self.leftColumnPanel, "Logging")
        _, _, self.LogLevelSelectorDropdown = self._add_section_row(
            self.loggingSection,
            logging_grid,
            "Log level",
            lambda parent: self._build_combo_field(parent, self.BeamSettings.getLogLevel(), logLevelList, self.OnSelectLogLevel),
        )
        left_column_vbox.Add(self.loggingSection, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=10)

        self.NetworkDisplayPane = wx.CollapsiblePane(self.leftColumnPanel, wx.ID_ANY, "Network display")
        self.NetworkDisplayPane.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.OnNetworkDisplayPaneChanged)
        self.NetworkDisplayPane.Collapse(True)
        self._style_collapsible_pane_header(self.NetworkDisplayPane)
        network_pane = self.NetworkDisplayPane.GetPane()
        network_pane_sizer = wx.BoxSizer(wx.VERTICAL)
        network_pane.SetSizer(network_pane_sizer)
        network_description = wx.StaticText(
            network_pane,
            wx.ID_ANY,
            "Expose the current Beam display to browsers on your network.",
        )
        network_grid = self._create_form_grid()
        network_pane_sizer.Add(network_description, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=8)
        network_pane_sizer.Add(network_grid, flag=wx.EXPAND | wx.ALL, border=8)
        _, _, self.NetworkEnabledCheckBox = self._add_section_row(
            network_pane,
            network_grid,
            "Enable service",
            lambda parent: self._build_checkbox_field(parent, 'Enable network display', self.BeamSettings.getNetworkServiceEnabled(), self.OnNetworkEnabled),
        )
        _, _, self.NetworkHostField = self._add_section_row(
            network_pane,
            network_grid,
            "Host",
            lambda parent: self._build_text_field(parent, self.networkBindDisplayHost, self.OnNetworkHostChanged),
            helper_text='Use 0.0.0.0 to listen on all interfaces.',
        )
        _, _, self.NetworkPortField = self._add_section_row(
            network_pane,
            network_grid,
            "Port",
            lambda parent: self._build_spin_field(parent, self.BeamSettings.getNetworkServicePort(), self.OnNetworkPortChanged, minimum=1, maximum=65535),
            helper_text='Default: 8765.',
        )
        _, _, self.NetworkAddressHint = self._add_section_row(
            network_pane,
            network_grid,
            "Address",
            lambda parent: wx.StaticText(parent, wx.ID_ANY, ""),
        )
        left_column_vbox.Add(self.NetworkDisplayPane, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=10)

        self.ExpertDisplayTweaksPane = wx.CollapsiblePane(self.leftColumnPanel, wx.ID_ANY, "Advanced display options")
        self.ExpertDisplayTweaksPane.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.OnExpertDisplayTweaksPaneChanged)
        self.ExpertDisplayTweaksPane.Collapse(True)
        self._style_collapsible_pane_header(self.ExpertDisplayTweaksPane)
        expert_pane = self.ExpertDisplayTweaksPane.GetPane()
        expert_pane_sizer = wx.BoxSizer(wx.VERTICAL)
        expert_pane.SetSizer(expert_pane_sizer)
        expert_hint = wx.StaticText(
            expert_pane,
            wx.ID_ANY,
            "Optional advanced rendering knobs for cover art and background bitmap caching. Use auto for proportional radius and feather.",
        )
        expert_grid = self._create_form_grid()
        expert_pane_sizer.Add(expert_hint, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=8)
        expert_pane_sizer.Add(expert_grid, flag=wx.EXPAND | wx.ALL, border=8)
        _, _, self.BackgroundBitmapCacheLimitField = self._add_section_row(
            expert_pane,
            expert_grid,
            "Background cache limit",
            lambda parent: self._build_spin_field(parent, self.BeamSettings.getBackgroundBitmapCacheLimit(), self.OnBackgroundBitmapCacheLimitChanged, minimum=1, maximum=64),
        )
        _, _, self.CoverArtCornerRadiusField = self._add_section_row(
            expert_pane,
            expert_grid,
            "Cover art corner radius",
            lambda parent: self._build_auto_numeric_field(parent, self.BeamSettings.getCoverArtCornerRadius(), self.OnCoverArtCornerRadiusChanged),
        )
        _, _, self.CoverArtFeatherAmountField = self._add_section_row(
            expert_pane,
            expert_grid,
            "Cover art feather amount",
            lambda parent: self._build_auto_numeric_field(parent, self.BeamSettings.getCoverArtFeatherAmount(), self.OnCoverArtFeatherAmountChanged),
        )
        _, _, self.CoverArtOutlineEnabledField = self._add_section_row(
            expert_pane,
            expert_grid,
            "Cover art outline",
            lambda parent: self._build_checkbox_field(parent, 'Enable thin translucent outline', self.BeamSettings.getCoverArtOutlineEnabled(), self.OnCoverArtOutlineEnabledChanged),
        )
        _, _, self.CoverArtOutlineAlphaField = self._add_section_row(
            expert_pane,
            expert_grid,
            "Cover art outline alpha",
            lambda parent: self._build_spin_field(parent, self.BeamSettings.getCoverArtOutlineAlpha(), self.OnCoverArtOutlineAlphaChanged, minimum=0, maximum=255),
        )
        _, _, self.CoverArtOutlineWidthField = self._add_section_row(
            expert_pane,
            expert_grid,
            "Cover art outline width",
            lambda parent: self._build_spin_field(parent, self.BeamSettings.getCoverArtOutlineWidth(), self.OnCoverArtOutlineWidthChanged, minimum=1, maximum=12),
        )
        left_column_vbox.Add(self.ExpertDisplayTweaksPane, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=10)

        content_hbox.Add(self.leftColumnPanel, 0, wx.EXPAND | wx.RIGHT, 6)
        content_hbox.Add(self.rightColumnPanel, 0, wx.EXPAND | wx.LEFT, 6)


        ##############
        # SET SIZERS #
        ##############
        self.scrolledWindow.SetSizer(content_hbox)
        left_column_vbox.SetMinSize((360, -1))
        right_column_vbox.SetMinSize((360, -1))
        self.scrolledWindow.FitInside()
        outer_vbox.Add(self.scrolledWindow, 1, wx.EXPAND)
        self.SetSizer(outer_vbox)
        self._sync_column_widths()
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
        self.MixxxDatabasePathField.ChangeValue(self.getMixxxDatabasePathDisplayValue())
        self.JRiverTargetZoneField.ChangeValue(self.BeamSettings.getJRiverTargetZone())
        self.VirtualDJIntegrationDropdown.SetValue(self.BeamSettings.getVirtualDJIntegrationMode())
        self.VirtualDJHistoryPathField.ChangeValue(self.BeamSettings.getVirtualDJHistoryPath())
        self.VirtualDJRecentWindowField.SetValue(self.BeamSettings.getVirtualDJRecentTrackWindowSec())
        self.VirtualDJHostField.ChangeValue(self.BeamSettings.getVirtualDJHost())
        self.VirtualDJPortField.SetValue(self.BeamSettings.getVirtualDJPort())
        self.VirtualDJTokenField.ChangeValue(self.BeamSettings.getVirtualDJBearerToken())
        self.VirtualDJQueryModeDropdown.SetValue(self.BeamSettings.getVirtualDJQueryMode())
        self.BackgroundBitmapCacheLimitField.SetValue(self.BeamSettings.getBackgroundBitmapCacheLimit())
        self.CoverArtCornerRadiusField.ChangeValue(self._get_auto_numeric_display_value(self.BeamSettings.getCoverArtCornerRadius()))
        self.CoverArtFeatherAmountField.ChangeValue(self._get_auto_numeric_display_value(self.BeamSettings.getCoverArtFeatherAmount()))
        self.CoverArtOutlineEnabledField.SetValue(self.BeamSettings.getCoverArtOutlineEnabled())
        self.CoverArtOutlineAlphaField.SetValue(self.BeamSettings.getCoverArtOutlineAlpha())
        self.CoverArtOutlineWidthField.SetValue(self.BeamSettings.getCoverArtOutlineWidth())
        self.updateRefreshTimeLabel()
        self.updateTandaLengthLabel()
        self.updateModuleSpecificSettingsVisibility(self.BeamSettings.getSelectedModuleName())
        self.updateNetworkAddressHint()






###################################################################
#                           EVENTS                                #
###################################################################

    def OnExpertDisplayTweaksPaneChanged(self, event):
        self.scrolledWindow.FitInside()
        self.Layout()
        if self.GetParent() is not None:
            self.GetParent().Layout()

    def OnNetworkDisplayPaneChanged(self, event):
        self.scrolledWindow.FitInside()
        self.Layout()
        if self.GetParent() is not None:
            self.GetParent().Layout()

    def OnScrolledWindowSize(self, event):
        self._sync_column_widths()
        event.Skip()

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

    def getMixxxDatabasePathDisplayValue(self):
        configured_path = self.BeamSettings.getMixxxDatabasePath()
        if configured_path != '':
            return configured_path

        candidate_paths = mixxxutils.get_mixxx_database_candidates()
        if candidate_paths:
            return candidate_paths[0]

        return ''

    def OnMixxxDatabasePathChanged(self, event):
        self.BeamSettings.setMixxxDatabasePath(self.MixxxDatabasePathField.GetValue())

    def OnMixxxTest(self, event):
        if platform.system() == 'Windows':
            from bin.modules.win import mixxxmodule
        elif platform.system() == 'Darwin':
            from bin.modules.mac import mixxxmodule
        else:
            from bin.modules.lin import mixxxmodule

        try:
            playlist, status, details = mixxxmodule.run_with_details(self.BeamSettings.getMaxTandaLength(), [])
        except Exception as error:
            wx.MessageBox(str(error), 'Mixxx test failed', wx.OK | wx.ICON_ERROR)
            return

        message_lines = [
            'Route: {0}'.format(details.get('route', 'unknown')),
            'Status: {0}'.format(status),
            'State model: {0}'.format(details.get('stateModel', '')),
            'Path source: {0}'.format(details.get('pathSource', '')),
            'Database path: {0}'.format(details.get('databasePath', '')),
            'Metadata source: {0}'.format(details.get('metadataSource', '')),
            'Schema: {0}'.format(details.get('schemaFlavor', '')),
        ]

        if details.get('playlistSource'):
            message_lines.append('Playlist source: {0}'.format(details.get('playlistSource', '')))
        if details.get('schemaMissingColumns'):
            message_lines.append('Schema missing columns: {0}'.format(', '.join(details.get('schemaMissingColumns', []))))
        if details.get('candidatePaths'):
            message_lines.append('Candidate paths: {0}'.format('; '.join(details.get('candidatePaths', []))))

        if playlist:
            song = playlist[0]
            message_lines.extend([
                '',
                'Artist: {0}'.format(song.Artist),
                'Title: {0}'.format(song.Title),
                'Album: {0}'.format(song.Album),
                'Genre: {0}'.format(song.Genre),
                'Year: {0}'.format(song.Year),
                'File path: {0}'.format(song.FilePath),
                'Diagnostics: {0}'.format(song.ModuleMessage),
            ])
        elif details.get('error'):
            message_lines.extend(['', 'Error: {0}'.format(details['error'])])
        else:
            message_lines.extend(['', 'Diagnostics: {0}'.format(mixxxmodule.mixxxutils.describe_mixxx_status_message(details, include_database_path=True))])

        wx.MessageBox('\n'.join(message_lines), 'Mixxx test', wx.OK | wx.ICON_INFORMATION)

    def OnFoobarTest(self, event):
        if platform.system() != 'Windows':
            wx.MessageBox('Foobar2000 integration is only available on Windows.', 'Foobar2000 test', wx.OK | wx.ICON_INFORMATION)
            return

        from bin.modules.win import foobar2kmodule

        try:
            playlist, status, details = foobar2kmodule.run_with_details(self.BeamSettings.getMaxTandaLength(), emit_debug_log=False)
        except Exception as error:
            wx.MessageBox(str(error), 'Foobar2000 test failed', wx.OK | wx.ICON_ERROR)
            return

        message_lines = [
            'Route: {0}'.format(details.get('route', 'unknown')),
            'Status: {0}'.format(status),
            'Base URL: {0}'.format(details.get('baseUrl', '')),
            'Authentication: {0}'.format(details.get('authMode', '')),
        ]

        if details.get('activePlaylistId') not in (None, ''):
            message_lines.append('Playlist id: {0}'.format(details.get('activePlaylistId', '')))
        if details.get('activeIndex') not in (None, ''):
            message_lines.append('Playlist index: {0}'.format(details.get('activeIndex', '')))

        if playlist:
            song = playlist[0]
            message_lines.extend([
                '',
                'Artist: {0}'.format(song.Artist),
                'Title: {0}'.format(song.Title),
                'Album: {0}'.format(song.Album),
                'Genre: {0}'.format(song.Genre),
                'Year: {0}'.format(song.Year),
                'File path: {0}'.format(song.FilePath),
            ])
        elif details.get('error'):
            message_lines.extend(['', 'Error: {0}'.format(details['error'])])

        wx.MessageBox('\n'.join(message_lines), 'Foobar2000 test', wx.OK | wx.ICON_INFORMATION)

    def OnJRiverTargetZoneChanged(self, event):
        self.BeamSettings.setJRiverTargetZone(self.JRiverTargetZoneField.GetValue())

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

    def OnVirtualDJHistoryDeckChanged(self, event):
        self.BeamSettings.setVirtualDJHistoryDeck(self.VirtualDJHistoryDeckDropdown.GetValue())

    def OnVirtualDJBearerTokenChanged(self, event):
        self.BeamSettings.setVirtualDJBearerToken(self.VirtualDJTokenField.GetValue())

    def OnVirtualDJQueryModeChanged(self, event):
        self.BeamSettings.setVirtualDJQueryMode(self.VirtualDJQueryModeDropdown.GetValue())

    def OnVirtualDJTest(self, event):
        from bin.modules import virtualdjmodule

        try:
            playlist, status, details = virtualdjmodule.run_with_details(self.BeamSettings.getMaxTandaLength(), [], emit_debug_log=False)
        except Exception as error:
            wx.MessageBox(str(error), 'VirtualDJ test failed', wx.OK | wx.ICON_ERROR)
            return

        message_lines = [
            'Integration: {0}'.format(details.get('integrationMode', self.BeamSettings.getVirtualDJIntegrationMode())),
            'Route: {0}'.format(details.get('route', 'unknown')),
            'Status: {0}'.format(status),
        ]

        if details.get('route') in ('history', 'fallback-history'):
            message_lines.append('History deck: {0}'.format(details.get('historyDeck', '')))
            message_lines.append('History file: {0}'.format(details.get('historyFilePath', '')))
        else:
            message_lines.append('Track source: {0}'.format(details.get('queryMode', '')))
            message_lines.append('Base URL: {0}'.format(details.get('baseUrl', '')))

        if playlist:
            song = playlist[0]
            message_lines.extend([
                '',
                'Artist: {0}'.format(song.Artist),
                'Title: {0}'.format(song.Title),
                'Album: {0}'.format(song.Album),
                'Genre: {0}'.format(song.Genre),
                'Year: {0}'.format(song.Year),
                'File path: {0}'.format(song.FilePath),
            ])
        elif details.get('error'):
            message_lines.extend(['', 'Error: {0}'.format(details['error'])])

        wx.MessageBox('\n'.join(message_lines), 'VirtualDJ test', wx.OK | wx.ICON_INFORMATION)

    def OnBackgroundBitmapCacheLimitChanged(self, event):
        self.BeamSettings.setBackgroundBitmapCacheLimit(self.BackgroundBitmapCacheLimitField.GetValue())

    def OnCoverArtCornerRadiusChanged(self, event):
        self.BeamSettings.setCoverArtCornerRadius(self.CoverArtCornerRadiusField.GetValue())

    def OnCoverArtFeatherAmountChanged(self, event):
        self.BeamSettings.setCoverArtFeatherAmount(self.CoverArtFeatherAmountField.GetValue())

    def OnCoverArtOutlineEnabledChanged(self, event):
        self.BeamSettings.setCoverArtOutlineEnabled(self.CoverArtOutlineEnabledField.GetValue())

    def OnCoverArtOutlineAlphaChanged(self, event):
        self.BeamSettings.setCoverArtOutlineAlpha(self.CoverArtOutlineAlphaField.GetValue())

    def OnCoverArtOutlineWidthChanged(self, event):
        self.BeamSettings.setCoverArtOutlineWidth(self.CoverArtOutlineWidthField.GetValue())

    def updateModuleSpecificSettingsVisibility(self, moduleName):
        show_foobar_settings = moduleName == 'Foobar2000'
        self.foobarSection.Show(show_foobar_settings)

        show_mixxx_settings = moduleName == 'Mixxx'
        self.mixxxSection.Show(show_mixxx_settings)

        show_jriver_settings = moduleName == 'JRiver' and platform.system() in ('Darwin', 'Windows')
        self.jriverSection.Show(show_jriver_settings)

        show_virtualdj_settings = moduleName == 'VirtualDJ'
        self.virtualDjSection.Show(show_virtualdj_settings)

        integration_mode = self.BeamSettings.getVirtualDJIntegrationMode()
        show_virtualdj_history_controls = show_virtualdj_settings and integration_mode in ('History File', VIRTUALDJ_AUTO_INTEGRATION_MODE)
        for control in self.virtualDjHistoryControls:
            control.Show(show_virtualdj_history_controls)

        show_virtualdj_network_controls = show_virtualdj_settings and integration_mode in ('Network Control', VIRTUALDJ_AUTO_INTEGRATION_MODE)
        for control in self.virtualDjNetworkControls:
            control.Show(show_virtualdj_network_controls)

        self.scrolledWindow.FitInside()
        self.Layout()
        if self.GetParent() is not None:
            self.GetParent().Layout()

    def _sync_column_widths(self):
        available_width, _ = self.scrolledWindow.GetClientSize()
        if available_width <= 0:
            return

        gap_width = 12
        column_width = max(320, int((available_width - gap_width) / 2))
        fixed_column_size = wx.Size(column_width, -1)
        self.leftColumnPanel.SetMinSize(fixed_column_size)
        self.leftColumnPanel.SetMaxSize(fixed_column_size)
        self.rightColumnPanel.SetMinSize(fixed_column_size)
        self.rightColumnPanel.SetMaxSize(fixed_column_size)
        self.leftColumnPanel.GetSizer().Layout()
        self.rightColumnPanel.GetSizer().Layout()
        self.scrolledWindow.Layout()
        self.scrolledWindow.FitInside()

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

    def _create_section(self, parent, title, description=''):
        section_panel = wx.Panel(parent, wx.ID_ANY)
        section_sizer = wx.StaticBoxSizer(wx.VERTICAL, section_panel, "")
        header_label = wx.StaticText(section_panel, wx.ID_ANY, title)
        header_font = wx.Font(13, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        header_label.SetFont(header_font)
        section_sizer.Add(header_label, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        if description:
            description_label = wx.StaticText(section_panel, wx.ID_ANY, description)
            section_sizer.Add(description_label, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=6)
        form_grid = self._create_form_grid()
        section_sizer.Add(form_grid, flag=wx.EXPAND | wx.ALL, border=10)
        section_panel.SetSizer(section_sizer)
        return section_panel, form_grid

    def _create_form_grid(self):
        form_grid = wx.FlexGridSizer(0, 2, 8, 12)
        form_grid.AddGrowableCol(1, 1)
        return form_grid

    def _add_section_row(self, parent, form_grid, label_text, field_builder, helper_text=''):
        label = wx.StaticText(parent, wx.ID_ANY, label_text)
        field_container = wx.Panel(parent, wx.ID_ANY)
        field_sizer = wx.BoxSizer(wx.VERTICAL)
        field_container.SetSizer(field_sizer)
        field_control = field_builder(field_container)
        field_sizer.Add(field_control, flag=wx.EXPAND)
        if helper_text:
            helper_label = wx.StaticText(field_container, wx.ID_ANY, helper_text)
            field_sizer.Add(helper_label, flag=wx.TOP, border=4)
        form_grid.Add(label, flag=wx.ALIGN_CENTER_VERTICAL)
        form_grid.Add(field_container, flag=wx.EXPAND)
        return label, field_container, field_control

    def _build_media_player_dropdown(self, parent):
        control = wx.ComboBox(
            parent,
            wx.ID_ANY,
            value=self.BeamSettings.getSelectedModuleName(),
            choices=self.BeamSettings._moduleNames,
            size=(233, -1),
            style=wx.CB_READONLY,
        )
        control.Bind(wx.EVT_COMBOBOX, self.OnSelectMediaPlayer)
        return normalizeMacControlHeight(control, default_width=233)

    def _build_refresh_interval_field(self, parent):
        panel = wx.Panel(parent, wx.ID_ANY)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        panel.SetSizer(sizer)
        self.RefreshTime = wx.Slider(panel, -1, int(self.BeamSettings.getUpdtime()), 500, 10000, (0, 0), (233, -1), wx.SL_HORIZONTAL)
        self.RefreshTime.Bind(wx.EVT_SCROLL, self.OnRefreshTimerScroll)
        self.RefreshTimeLabel = wx.StaticText(panel, -1, "")
        sizer.Add(self.RefreshTime, 1, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 8)
        sizer.Add(self.RefreshTimeLabel, 0, wx.ALIGN_CENTER_VERTICAL)
        return panel

    def _build_tanda_length_field(self, parent):
        panel = wx.Panel(parent, wx.ID_ANY)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        panel.SetSizer(sizer)
        self.TandaLength = wx.Slider(panel, -1, self.BeamSettings.getMaxTandaLength(), 0, 10, (0, 0), (233, -1), wx.SL_HORIZONTAL)
        self.TandaLength.Bind(wx.EVT_SCROLL, self.OnTandaLengthScroll)
        self.TandaLengthLabel = wx.StaticText(panel, -1, "")
        sizer.Add(self.TandaLength, 1, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 8)
        sizer.Add(self.TandaLengthLabel, 0, wx.ALIGN_CENTER_VERTICAL)
        return panel

    def _build_text_field(self, parent, value, handler, style=0):
        control = wx.TextCtrl(parent, wx.ID_ANY, value=value, size=(233, -1), style=style)
        control.Bind(wx.EVT_TEXT, handler)
        return normalizeMacControlHeight(control, default_width=233)

    def _build_combo_field(self, parent, value, choices, handler):
        control = wx.ComboBox(parent, wx.ID_ANY, value=value, choices=choices, size=(233, -1), style=wx.CB_READONLY)
        control.Bind(wx.EVT_COMBOBOX, handler)
        return normalizeMacControlHeight(control, default_width=233)

    def _build_spin_field(self, parent, value, handler, minimum, maximum):
        control = wx.SpinCtrl(parent, wx.ID_ANY, min=minimum, max=maximum, initial=int(value), size=(100, -1))
        control.Bind(wx.EVT_SPINCTRL, handler)
        control.Bind(wx.EVT_TEXT, handler)
        return control

    def _build_checkbox_field(self, parent, label, value, handler):
        control = wx.CheckBox(parent, wx.ID_ANY, label)
        control.SetValue(value)
        control.Bind(wx.EVT_CHECKBOX, handler)
        return control

    def _build_button_field(self, parent, label, handler):
        control = wx.Button(parent, wx.ID_ANY, label=label)
        control.Bind(wx.EVT_BUTTON, handler)
        return control

    def _build_auto_numeric_field(self, parent, value, handler):
        control = wx.ComboBox(
            parent,
            wx.ID_ANY,
            value=self._get_auto_numeric_display_value(value),
            choices=['auto'],
            size=(120, -1),
        )
        control.Bind(wx.EVT_TEXT, handler)
        control.Bind(wx.EVT_COMBOBOX, handler)
        return normalizeMacControlHeight(control, default_width=120)

    def _style_collapsible_pane_header(self, collapsible_pane):
        toggle_button = collapsible_pane.GetChildren()[0] if collapsible_pane.GetChildren() else None
        if toggle_button is None:
            return

        current_font = toggle_button.GetFont()
        styled_font = wx.Font(
            13,
            current_font.GetFamily(),
            current_font.GetStyle(),
            wx.FONTWEIGHT_BOLD,
            current_font.GetUnderlined(),
            current_font.GetFaceName(),
        )
        toggle_button.SetFont(styled_font)

    def _get_auto_numeric_display_value(self, value):
        if str(value).strip().lower() == 'auto':
            return 'auto'
        return str(value)

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
