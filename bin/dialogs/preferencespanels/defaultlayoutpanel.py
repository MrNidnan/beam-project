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

import wx, os
from bin.backgroundassets import import_background_asset, resolve_background_reference, to_persisted_background_reference
from bin.dialogs.editlayoutitemdialog import EditLayoutItemDialog
from bin.dialogs.preferencespanels.timercombobox import TimerComboBox

BACKGROUND_FILE_WILDCARD = "Image files(*.png,*.jpg)|*.png;*.jpg"
BACKGROUND_EXTENSIONS = ('.jpg', '.jpeg', '.png')

###################################################################
#                      DefaultLayout                              #
###################################################################


def _get_background_picker_path(background_reference):
    resolved_background = resolve_background_reference(background_reference)
    return resolved_background['absolutePath'] or str(background_reference or '')


def _get_background_label_path(background_reference):
    resolved_background = resolve_background_reference(background_reference)
    return resolved_background['absolutePath'] or resolved_background['relativePath'] or str(background_reference or '')


class DefaultLayoutPanel(wx.Panel):
    def __init__(self, parent, BeamSettings):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        # uses self.BeamSettings._moods[0]
        
        #############
        # VARIABLES #
        #############
        self.BeamSettings = BeamSettings
        self.parent = parent
        self.DisplayRows = []
        font = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        
        ###############
        # Description #
        ###############
        description = wx.StaticText(self, -1, "The default Layout is the layout configuration which will be shown when no Mood is applied.")
        description.Wrap(380)
        
        ####################
        # BACKGROUND IMAGE #
        ####################
        background = wx.StaticText(self, -1, "Background")
        background.SetFont(font)
        backdescription = wx.StaticText(self, -1, "Select background image (1920x1080 recommended)")
        self.browse = wx.Button(self, label="Browse")
        self.browse.Bind(wx.EVT_BUTTON, self.BrowseBackgroundImage)
        (path,backgroundfile) = os.path.split(self.BeamSettings.getMoods()[0]['Background'])
        self.currentBackground = wx.StaticText(self, -1, "")
        hboxBackground = wx.BoxSizer(wx.HORIZONTAL)
        hboxBackground.Add(self.browse, flag=wx.RIGHT | wx.TOP, border=5)
        hboxBackground.Add(self.currentBackground, flag=wx.LEFT | wx.TOP, border=5)
        
        #######################
        # BACKGROUND ROTATION #
        #######################
        self.ChangeBackgroundBox = wx.CheckBox(self, label='Change Background: ')
        self.BackgroundTimerBox = TimerComboBox(self)
        timevalue = int(self.BeamSettings.getMoods()[0]['RotateTimer'])
        self.BackgroundTimerBox.setTimeSelection(timevalue)
        # sets BackgroundTimerBox selection
        # self.rotateBackgroundFunction()

        self.RandomBackgroundBox = wx.CheckBox(self, label='Random order')
        self.ChangeBackgroundBox.Bind(wx.EVT_CHECKBOX, self.OnRotateBackground)
        self.RandomBackgroundBox.Bind(wx.EVT_CHECKBOX, self.OnRotateBackground)
        self.BackgroundTimerBox.Bind(wx.EVT_COMBOBOX, self.OnRotateBackground)
        if self.BeamSettings.getMoods()[0]['RotateBackground'] == "linear":
            self.ChangeBackgroundBox.SetValue(True)
            self.RandomBackgroundBox.SetValue(False)
        elif self.BeamSettings.getMoods()[0]['RotateBackground'] == "random":
            self.ChangeBackgroundBox.SetValue(True)
            self.RandomBackgroundBox.SetValue(True)
        else:
            self.ChangeBackgroundBox.SetValue(False)
            self.RandomBackgroundBox.SetValue(False)
            self.RandomBackgroundBox.Disable()
            self.BackgroundTimerBox.Disable()
        RandomSizer = wx.BoxSizer(wx.HORIZONTAL)
        RandomSizer.Add(self.ChangeBackgroundBox, flag=wx.RIGHT | wx.LEFT, border=10)
        RandomSizer.Add(self.BackgroundTimerBox)

        self.OnRotateBackground()

        ###############
        # LAYOUT LIST #
        ###############
        LayoutText = wx.StaticText(self, -1, "Layout")
        LayoutText.SetFont(font)
        self.LayoutList = wx.CheckListBox(self,-1, choices=[], style= wx.LB_NEEDED_SB)
        self.LayoutList.SetBackgroundColour(wx.Colour(128, 128, 128))
        self.LayoutList.Bind(wx.EVT_LISTBOX_DCLICK, self.OnEditLayout)
        self.LayoutList.Bind(wx.EVT_CHECKLISTBOX, self.OnCheckLayout)
        self.BuildLayoutList()

        ##################
        # LAYOUT BUTTONS #
        ##################
        self.AddLayout  = wx.Button(self, label="Add")
        self.DelLayout  = wx.Button(self, label="Delete")
        self.EditLayout = wx.Button(self, label="Edit")
        self.AddLayout.Bind(wx.EVT_BUTTON, self.OnAddLayout)
        self.EditLayout.Bind(wx.EVT_BUTTON, self.OnEditLayout)
        self.DelLayout.Bind(wx.EVT_BUTTON, self.OnDelLayout)
        sizerbuttons    = wx.BoxSizer(wx.HORIZONTAL)
        sizerbuttons.Add(self.AddLayout, flag=wx.RIGHT, border=10)
        sizerbuttons.Add(self.DelLayout, flag=wx.RIGHT, border=10)
        sizerbuttons.Add(self.EditLayout, flag=wx.RIGHT, border=10)

        ##############
        # SET SIZERS #
        ##############
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(description, flag=wx.ALIGN_TOP | wx.ALL, border=10)
        sizer.Add(background, flag=wx.LEFT | wx.TOP | wx.BOTTOM, border=10)
        sizer.Add(backdescription, flag=wx.LEFT, border=20)
        sizer.Add(hboxBackground, flag=wx.LEFT, border=20)
        sizer.Add(RandomSizer, flag=wx.LEFT | wx.TOP, border=10)
        sizer.Add(self.RandomBackgroundBox, flag=wx.LEFT, border=20)
        sizer.Add(LayoutText, flag= wx.LEFT| wx.TOP, border=10)
        sizer.Add(self.LayoutList, proportion=1, flag= wx.EXPAND| wx.ALL, border=10 )
        sizer.Add(sizerbuttons, flag=wx.LEFT | wx.BOTTOM, border=10)
        self.SetSizer(sizer)


###################################################################
#                           EVENTS                                #
###################################################################

        #####################
        # BROWSE BACKGROUND #
        #####################
    def BrowseBackgroundImage(self, event):
        # appPath = getBeamHomePath()
# !!! current path as default?
        background_path = _get_background_picker_path(self.BeamSettings.getMoods()[0]['Background'])
        if self.BeamSettings.getMoods()[0]['RotateBackground'] == 'no':
            dialog_directory, dialog_file = os.path.split(background_path)
            open_dialog = wx.FileDialog(
                self,
                "Set new background image",
                dialog_directory,
                dialog_file,
                BACKGROUND_FILE_WILDCARD,
                wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
            )
        else:
            dialog_directory = background_path
            if os.path.splitext(os.path.basename(background_path))[1].lower() in BACKGROUND_EXTENSIONS:
                dialog_directory = os.path.dirname(background_path)
            open_dialog = wx.DirDialog(
                self,
                "Select background folder",
                dialog_directory,
                wx.DD_DIR_MUST_EXIST
            )

        try:
            if open_dialog.ShowModal() == wx.ID_OK:
                selected_path = open_dialog.GetPath()
                persisted_reference = to_persisted_background_reference(selected_path, 'moods')
                if persisted_reference is None:
                    message = (
                        "Copy the selected background into Beam's managed background library?\n\n"
                        "Yes: import into ~/.beam/backgrounds/moods\n"
                        "No: keep an unmanaged external path\n"
                        "Cancel: keep the current background"
                    )
                    decision_dialog = wx.MessageDialog(
                        self,
                        message,
                        "Import background",
                        wx.YES_NO | wx.CANCEL | wx.ICON_QUESTION,
                    )
                    try:
                        decision = decision_dialog.ShowModal()
                    finally:
                        decision_dialog.Destroy()

                    if decision == wx.ID_CANCEL:
                        return
                    if decision == wx.ID_YES:
                        import_result = import_background_asset(selected_path, 'moods')
                        if import_result['status'] == 'failed':
                            error_dialog = wx.MessageDialog(
                                self,
                                import_result['message'],
                                "Background import failed",
                                wx.OK | wx.ICON_ERROR,
                            )
                            try:
                                error_dialog.ShowModal()
                            finally:
                                error_dialog.Destroy()
                            return
                        persisted_reference = import_result['reference']
                    else:
                        persisted_reference = os.path.normpath(selected_path)

                self.BeamSettings.getMoods()[0]['Background'] = persisted_reference
                self.BeamSettings.markDirty()
                # change current background
                self.OnRotateBackground()
        finally:
            open_dialog.Destroy()

        #####################
        # ROTATE BACKGROUND #
        #####################
    def OnRotateBackground(self, event=wx.EVT_CHECKBOX):
        if self.ChangeBackgroundBox.IsChecked() and not self.RandomBackgroundBox.IsChecked():
            self.BeamSettings.getMoods()[0]['RotateBackground'] = "linear"
            self.RandomBackgroundBox.Enable()
            self.BackgroundTimerBox.Enable()
        elif self.ChangeBackgroundBox.IsChecked() and self.RandomBackgroundBox.IsChecked():
            self.BeamSettings.getMoods()[0]['RotateBackground'] = "random"
            self.RandomBackgroundBox.Enable()
            self.BackgroundTimerBox.Enable()
        else:
            self.BeamSettings.getMoods()[0]['RotateBackground'] = "no"
            self.RandomBackgroundBox.Disable()
            self.BackgroundTimerBox.Disable()

        self.BeamSettings.getMoods()[0]['RotateTimer'] = self.BackgroundTimerBox.getTimeSelection()
        self.rotateBackgroundFunction()


    def rotateBackgroundFunction(self):
        timevalue = int(self.BeamSettings.getMoods()[0]['RotateTimer'])
        self.BackgroundTimerBox.setTimeSelection(timevalue)

        label_path = _get_background_label_path(self.BeamSettings.getMoods()[0]['Background'])
        path, backgroundfile = os.path.split(os.path.normpath(label_path))
        if self.BeamSettings.getMoods()[0]['RotateBackground'] == "no":
            self.currentBackground.SetLabel("Image: " + backgroundfile)
        else:
            if os.path.splitext(backgroundfile)[1].lower() in BACKGROUND_EXTENSIONS:
                folder_name = os.path.split(path)[1]
            else:
                folder_name = backgroundfile
            self.currentBackground.SetLabel("Images from folder: " + folder_name)

        ##################
        # LAYOUT BUTTONS #
        ##################
    def OnAddLayout(self, event):
        self.EditLayout = EditLayoutItemDialog(self, len(self.DisplayRows), "Add layout item", self.BeamSettings.getMoods()[0]['Display'])
        self.EditLayout.Show()
    
    def OnEditLayout(self, event):
        RowSelected = self.LayoutList.GetSelection()
        if RowSelected>-1:
            self.EditLayout = EditLayoutItemDialog(self, RowSelected, "Edit layout item", self.BeamSettings.getMoods()[0]['Display'])
            self.EditLayout.Show()
    def OnDelLayout(self, event):
        RowSelected = self.LayoutList.GetSelection()
        if RowSelected >= 0:
            LineToDelete = self.LayoutList.GetString(RowSelected)
            dlg = wx.MessageDialog(self,
            "Do you really want to delete '"+LineToDelete+"' ?",
            "Confirm deletion", wx.OK|wx.CANCEL|wx.ICON_QUESTION)
            result = dlg.ShowModal()
            dlg.Destroy()
            if result == wx.ID_OK:
                self.BeamSettings.getMoods()[0]['Display'].pop(RowSelected)
                self.BuildLayoutList()

        #####################
        # LAYOUT CHECKBOXES #
        #####################
    def OnCheckLayout(self, event):
        for i in range(0, len(self.BeamSettings.getMoods()[0]['Display'])):
            layout = self.BeamSettings.getMoods()[0]['Display'][i]
            if self.LayoutList.IsChecked(i):
                layout['Active'] = "yes"
            else:
                layout['Active'] = "no"
        self.BuildLayoutList()

        ####################
        # BUILD LAYOUTLIST #
        ####################
    def BuildLayoutList(self):
        self.DisplayRows = []
        for i in range(0, len(self.BeamSettings.getMoods()[0]['Display'])):
            Settings = self.BeamSettings.getMoods()[0]['Display'][i]
            self.DisplayRows.append(Settings['Field'])
        self.LayoutList.Set(self.DisplayRows)
        for i in range(0, len(self.BeamSettings.getMoods()[0]['Display'])):
            Settings = self.BeamSettings.getMoods()[0]['Display'][i]
            if Settings['Active'] == "yes":
                self.LayoutList.Check(i, check=True)
            else:
                self.LayoutList.Check(i, check=False)



