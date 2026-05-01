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

import wx, os, numpy
from bin.dialogs.editruledialog import EditRuleDialog

########################################################
#                      Rules                           #
########################################################
class RulesPanel(wx.Panel):
    def __init__(self, parent, mainFrame, BeamSettings):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
        
        #############
        # VARIABLES #
        #############
        self.BeamSettings = BeamSettings
        self.mainFrame = mainFrame
        self.RuleRows = []
        font = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD)

        ###############
        # Description #
        ###############
        description = wx.StaticText(self, -1, "Rules are used to:\n - Copy information from one tag to another.\n - Define Cortinas.\n - Split tags, such tags with both artist and title.\n - Ignore songs completely, such as silent tracks.\n - Replace tag value with static content when a criterion is met.\n - Trim trailing (...) from song titles.\n\nRules can be activated and deactivated with the check box.")
        description.Wrap(380)

        #############
        # RULE LIST #
        #############
        self.RuleList = wx.CheckListBox(self,-1, size=wx.DefaultSize, choices=self.RuleRows, style= wx.LB_NEEDED_SB)
        bgcolour = self.RuleList.GetBackgroundColour()
        fgcolour = tuple(numpy.subtract((255,255,255,510),bgcolour))
        self.RuleList.SetForegroundColour(fgcolour)
        self.RuleList.Bind(wx.EVT_LISTBOX_DCLICK, self.OnEditRule)
        self.RuleList.Bind(wx.EVT_CHECKLISTBOX, self.OnCheckRule)
        self.BuildRuleList()

        ################
        # RULE BUTTONS #
        ################
        self.AddRule    = wx.Button(self, label="Add")
        self.DelRule    = wx.Button(self, label="Delete")
        self.EditRule   = wx.Button(self, label="Edit")
        self.AddRule.Bind(wx.EVT_BUTTON, self.OnAddRule)
        self.EditRule.Bind(wx.EVT_BUTTON, self.OnEditRule)
        self.DelRule.Bind(wx.EVT_BUTTON, self.OnDelRule)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizerbuttons    = wx.BoxSizer(wx.HORIZONTAL)
        sizerbuttons.Add(self.AddRule, flag=wx.RIGHT | wx.TOP, border=10)
        sizerbuttons.Add(self.DelRule, flag=wx.RIGHT | wx.TOP, border=10)
        sizerbuttons.Add(self.EditRule, flag=wx.RIGHT | wx.TOP, border=10)
        sizer.Add(description, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        sizer.Add(self.RuleList, proportion=1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        sizer.Add(sizerbuttons, flag=wx.LEFT | wx.BOTTOM | wx.TOP, border=10)
        self.SetSizer(sizer)


    def updateSettings(self):
        self.mainFrame.updateSettings();

    def reloadFromSettings(self):
        self.BuildRuleList()

###################################################################
#                           EVENTS                                #
###################################################################

    ################
    # RULE BUTTONS #
    ################
    def OnAddRule(self, event):
        self.EditRule = EditRuleDialog(self, self.RuleList.GetCount(), "Add rule")
        self.EditRule.Show()
    
    def OnEditRule(self, event):
        RowSelected = self.RuleList.GetSelection()
        if RowSelected>-1:
            self.EditRule = EditRuleDialog(self, RowSelected, "Edit rule")
            self.EditRule.Show()

    def OnDelRule(self, event):
        RowSelected = self.RuleList.GetSelection()
        if RowSelected>-1:
            LineToDelete = self.RuleList.GetString(RowSelected)
            dlg = wx.MessageDialog(self,
                    "Do you really want to delete '"+LineToDelete+"' ?",
                    "Confirm deletion", wx.OK|wx.CANCEL|wx.ICON_QUESTION)
            result = dlg.ShowModal()
            dlg.Destroy()
            if result == wx.ID_OK:
                self.BeamSettings.getRules().pop(RowSelected)
                self.BeamSettings.markDirty()
                self.BuildRuleList()


    #####################
    # LAYOUT CHECKBOXES #
    #####################
    def OnCheckRule(self, event):
        for i in range(0, len(self.BeamSettings.getRules())):
            rule = self.BeamSettings.getRules()[i]
            if self.RuleList.IsChecked(i):
                rule['Active'] = "yes"
            else:
                rule['Active'] = "no"
        self.BeamSettings.markDirty()
        self.BuildRuleList()

    #####################
    # BUILD RULELIST #
    #####################
    def BuildRuleList(self):
        self.RuleRows = []
        for i in range(0, len(self.BeamSettings.getRules())):
            rule = self.BeamSettings.getRules()[i]
            if rule['Type'] == "Copy":
                self.RuleRows.append(str('Copy '+rule['Field1']+' to '+rule['Field2']))
            
            if rule['Type'] == "Cortina":
                if rule['Field2'] =="is":
                    self.RuleRows.append(str("It's a Cortina when: "+rule['Field1']+' is '+rule['Field3']))
                if rule['Field2'] =="is not":
                    self.RuleRows.append(str("It's a Cortina when: "+rule['Field1']+' is not '+rule['Field3']))
                if rule['Field2'] =="contains":
                    self.RuleRows.append(str("It's a Cortina when: "+rule['Field1']+' contains '+rule['Field3']))
        
            if rule['Type'] == "Parse":
                self.RuleRows.append(str('Parse/split '+rule['Field1']+' containing '+rule['Field2']+' into '+rule['Field3']+' and '+rule['Field4']))

            if rule['Type'] == "Replace":
                self.RuleRows.append(
                    str('Replace ' + rule['Field1'] + ' containing ' + rule['Field3'] + ' with ' + rule[
                        'Field2']))

            if rule['Type'] == "Ignore":
                if rule['Field2'] =="is":
                    self.RuleRows.append(str("Ignore song if "+rule['Field1']+' is '+rule['Field3']))
                if rule['Field2'] =="is not":
                    self.RuleRows.append(str("Ignore song if "+rule['Field1']+' is not '+rule['Field3']))
                if rule['Field2'] =="contains":
                    self.RuleRows.append(str("Ignore song if "+rule['Field1']+' contains '+rule['Field3']))

            if rule['Type'] == "Trim () in Title":
                self.RuleRows.append("Trim () in the Title")
        self.RuleList.Set(self.RuleRows)
        # Check the rules
        for i in range(0, len(self.BeamSettings.getRules())):
            rule = self.BeamSettings.getRules()[i]
            if rule['Active'] == "yes":
                self.RuleList.Check(i, check=True)
            else:
                self.RuleList.Check(i, check=False)


