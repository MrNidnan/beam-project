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
import os

from bin.beamsettings import *

#
# Edit Rule class
#
#
class EditRuleDialog(wx.Dialog):
    def __init__(self, parent, RowSelected, mode):
        self.EditRuleDialog     = wx.Dialog.__init__(self, parent, title=mode)
        self.EditRulePanel  = wx.Panel(self)
        self.parent             = parent
        self.RowSelected    = RowSelected
        self.mode           = mode

        self.ButtonSaveRule     = wx.Button(self.EditRulePanel, label="Save")
        self.ButtonCancelRule   = wx.Button(self.EditRulePanel, label="Cancel")
        self.ButtonSaveRule.Bind(wx.EVT_BUTTON, self.OnSaveRuleItem)
        self.ButtonCancelRule.Bind(wx.EVT_BUTTON, self.OnCancelRuleItem)
        self.InputFields    = ["%Artist","%Album","%Title","%Genre","%Comment","%Composer","%Year", "%AlbumArtist", "%Performer"]
        self.OutputFields   = ["%Artist","%Album","%Title","%Genre","%Comment","%Composer","%Year", "%AlbumArtist", "%Performer", "%Singer"]


    # Check if it is a new line
        if self.RowSelected<len(beamSettings._rules):
            # Get the properties of the selected item
            self.Settings   = beamSettings._rules[self.RowSelected]
        else:
            # Create a new default setting
            self.Settings   = ({"Type": "Copy", "Field1": "%Comment","Field2": "%Singer", "Active": "yes"})

        # Build the static elements
        self.InputID3Field      = wx.ComboBox(self.EditRulePanel, size=(150,-1), value=self.Settings[u'Field1'], choices=self.InputFields, style=wx.CB_READONLY)
        self.RuleSelectDropdown     = wx.ComboBox(self.EditRulePanel, size=(100,-1), value=self.Settings[u'Type'], choices=['Copy','Cortina','Parse'], style=wx.CB_READONLY)
        self.RuleSelectDropdown.Bind(wx.EVT_COMBOBOX, self.ChangeRuleType)
        self.RuleOrder          = wx.TextCtrl(self.EditRulePanel, value=str(self.RowSelected+1))

        # Dynamic fields (Changes depending on RuleSelectDropdown)
        self.DynamicFieldLabel1 = wx.StaticText(self.EditRulePanel, label="")
        self.DynamicFieldLabel2 = wx.StaticText(self.EditRulePanel, label="")
        self.DynamicFieldLabel3 = wx.StaticText(self.EditRulePanel, label="")
        self.DynamicFieldLabel4 = wx.StaticText(self.EditRulePanel, label="")

        self.OutputField3 = wx.TextCtrl(self.EditRulePanel, value="", size=(150,-1))

        self.sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer3 = wx.BoxSizer(wx.HORIZONTAL)

        InfoGrid    =   wx.FlexGridSizer(4, 4, 5, 5)
        InfoGrid.AddMany ( [(wx.StaticText(self.EditRulePanel, label="Rule type", size=(100,-1)), 0, wx.EXPAND),
                        (wx.StaticText(self.EditRulePanel, label="Input ID3 tag", size=(100,-1)), 0, wx.EXPAND),
                        (self.DynamicFieldLabel1, 0, wx.EXPAND),
                        (self.DynamicFieldLabel2, 0, wx.EXPAND),
                        (self.RuleSelectDropdown, 0, wx.EXPAND),
                        (self.InputID3Field, 0, wx.EXPAND),
                        (self.sizer1, 0, wx.EXPAND),
                        (self.sizer2, 0, wx.EXPAND),
                        (wx.StaticText(self.EditRulePanel, label="Rule order"), 0, wx.EXPAND),
                        (self.DynamicFieldLabel3, 0, wx.EXPAND  ),
                        (self.DynamicFieldLabel4, 0, wx.EXPAND  ),
                        (wx.StaticText(self.EditRulePanel, label=""), 0, wx.EXPAND),
                        (self.RuleOrder, 0, wx.EXPAND),
                        (self.OutputField3, 0, wx.EXPAND ),
                        (self.sizer3, 0, wx.EXPAND)
                        ])

        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.hbox = wx.BoxSizer(wx.HORIZONTAL)

        self.hbox.Add(self.ButtonSaveRule, 0, flag=wx.ALL | wx.ALIGN_RIGHT, border=10)
        self.hbox.Add(self.ButtonCancelRule, 0, flag=wx.ALL | wx.ALIGN_RIGHT, border=10)

        self.vbox.Add(InfoGrid, flag=wx.ALL, border=10)
        self.vbox.Add(self.hbox, flag=wx.ALL | wx.ALIGN_RIGHT)

        self.ChangeRuleType(self)
        self.EditRulePanel.SetSizer(self.vbox)
        self.vbox.SetSizeHints(self)  
        
#
# RULE TYPES
#

    def ChangeRuleType(self, event):
        RuleSelected = self.RuleSelectDropdown.GetValue()
###########################################
        if RuleSelected == 'Copy':
            self.DynamicFieldLabel1.SetLabel('Output field')
            self.DynamicFieldLabel2.SetLabel('')
            self.DynamicFieldLabel3.SetLabel('')
            self.DynamicFieldLabel4.SetLabel('')
            # Remove fields that are not to be shown
            self.RemoveDynamicElements()

            self.DynamicFieldLabel3.Hide()
            self.OutputField3.Hide()

            #Add correct fields
            self.OutputField1       = wx.ComboBox(self.EditRulePanel, size=(150,-1), value="%Artist", choices=self.OutputFields, style=wx.CB_READONLY)
            self.sizer1.Add(self.OutputField1)

            if self.Settings[u'Type'] == 'Copy':
                self.OutputField1.SetStringSelection(self.Settings[u'Field2'])
            else:
                self.OutputField1.SetStringSelection("%Artist")

########################################
        if RuleSelected == 'Parse':
            self.DynamicFieldLabel1.SetLabel('Output field 1')
            self.DynamicFieldLabel2.SetLabel('Output field 2')
            self.DynamicFieldLabel3.SetLabel('Token')
            self.DynamicFieldLabel4.SetLabel('')
            # Remove fields that are not to be shown
            self.RemoveDynamicElements()

            #Add correct fields
            self.OutputField1       = wx.ComboBox(self.EditRulePanel,value="%Artist", size=(150,-1), choices=self.OutputFields,style=wx.CB_READONLY)
            self.sizer1.Add(self.OutputField1)
            self.OutputField2       = wx.ComboBox(self.EditRulePanel,value="%Artist", size=(150,-1), choices=self.OutputFields,style=wx.CB_READONLY)
            self.sizer2.Add(self.OutputField2)

            if self.Settings[u'Type'] == 'Parse':
                self.OutputField1.SetStringSelection(self.Settings[u'Field3'])
                self.OutputField2.SetStringSelection(self.Settings[u'Field4'])
                self.OutputField3.SetValue(self.Settings[u'Field2'])
            else:
                self.OutputField1.SetStringSelection("%Artist")
                self.OutputField2.SetStringSelection("%Title")
                self.OutputField3.SetValue("-")
            # Show Fields
            self.DynamicFieldLabel3.Show()
            self.OutputField3.Show()

##############################################
        if RuleSelected == 'Cortina':
            self.DynamicFieldLabel1.SetLabel('')
            self.DynamicFieldLabel2.SetLabel('Value(s)')
            self.DynamicFieldLabel3.SetLabel('')
            self.DynamicFieldLabel4.SetLabel('')

            # Remove fields that are not to be shown
            self.RemoveDynamicElements()

            self.DynamicFieldLabel3.Hide()
            self.OutputField3.Hide()

            #Add correct fields
            self.IsIsNot    = wx.ComboBox(self.EditRulePanel,value="is", choices=["is", "is not","contains"], style=wx.CB_READONLY)
            self.sizer1.Add(self.IsIsNot)
            self.OutputField2 = wx.TextCtrl(self.EditRulePanel, value="", size=(165,-1))
            self.sizer2.Add(self.OutputField2)

            if self.Settings[u'Type'] == 'Cortina':
                self.IsIsNot.SetStringSelection(self.Settings[u'Field2'])
                self.OutputField2.SetValue(self.Settings[u'Field3'])
            else:
                self.IsIsNot.SetStringSelection("is")
                self.OutputField2.SetValue("")

        self.vbox.SetSizeHints(self)  
        self.EditRulePanel.SetSizer(self.vbox)
        self.EditRulePanel.Layout()

#
# GUI REMOVE ELEMENTS
#
    def RemoveDynamicElements(self):
        try:
            self.sizer1.Remove(self.OutputField1)
            self.OutputField1.Hide()
        except: pass
        try:
            self.sizer2.Remove(self.OutputField2)
            self.OutputField2.Hide()
        except: pass
        try:
            self.sizer1.Remove(self.IsIsNot)
            self.IsIsNot.Hide()
        except: pass
        try:
            self.sizer2.Remove(self.OutputField3)
            self.OutputField3.Hide()
        except: pass
        try:
            self.sizer3.Remove(self.PlayingState)
            self.PlayingState.Hide()
        except: pass

#
# SAVE
#
    def OnSaveRuleItem(self, event):
        RuleOrderBox = int(self.RuleOrder.GetValue())-1
        RuleSelected = self.RuleSelectDropdown.GetValue()

        # Build NewRule
        NewRule = {}
        NewRule[u'Type']        = RuleSelected
        NewRule[u'Field1']      = self.InputID3Field.GetValue()
        NewRule[u'Active']      = self.Settings[u'Active']

        if RuleSelected == 'Copy':
            NewRule[u'Field2']      = self.OutputField1.GetValue()
        if RuleSelected == 'Parse':
            NewRule[u'Field2']      = self.OutputField3.GetValue()
            NewRule[u'Field3']      = self.OutputField1.GetValue()
            NewRule[u'Field4']      = self.OutputField2.GetValue()
        if RuleSelected == 'Cortina':
            NewRule[u'Field2']      = self.IsIsNot.GetValue()
            NewRule[u'Field3']      = self.OutputField2.GetValue()

        NewRule[u'Field1']      = self.InputID3Field.GetValue()
        # Decide where NewRule goes into the vector self.Settings
        if self.mode == "Add rule":
            if RuleOrderBox < self.RowSelected:
                beamSettings._rules.insert(RuleOrderBox, NewRule) #Insert in at position
            else:
                beamSettings._rules.append(NewRule) # Append in the end
        else: #Edit rule
            if RuleOrderBox == self.RowSelected:
                beamSettings._rules[RuleOrderBox] = NewRule # Overwrite
            else:
                beamSettings._rules.pop(self.RowSelected) #Move up and down in list
                beamSettings._rules.insert(RuleOrderBox, NewRule)
        self.Destroy()
        self.parent.BuildRuleList()
#
# CANCEL
#
    def OnCancelRuleItem(self, event):
        self.Destroy()

