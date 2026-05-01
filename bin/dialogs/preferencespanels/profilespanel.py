#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import wx


class ProfilesPanel(wx.Panel):
    def __init__(self, parent, mainFrame, BeamSettings):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        self.BeamSettings = BeamSettings
        self.mainFrame = mainFrame
        self.profileIds = []

        font = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD)

        title = wx.StaticText(self, wx.ID_ANY, "Profiles")
        title.SetFont(font)

        description = wx.StaticText(
            self,
            wx.ID_ANY,
            "Profiles store the full Beam configuration. Create a named profile, switch the active profile, or save the current settings back into it.",
        )
        description.Wrap(380)

        self.ActiveProfileLabel = wx.StaticText(self, wx.ID_ANY, "")
        self.ProfileList = wx.ListBox(self, wx.ID_ANY)
        self.ProfileList.Bind(wx.EVT_LISTBOX, self.OnProfileSelected)
        self.ProfileList.Bind(wx.EVT_LISTBOX_DCLICK, self.OnSwitchProfile)

        self.SwitchButton = wx.Button(self, label="Switch")
        self.SaveButton = wx.Button(self, label="Save")
        self.CreateButton = wx.Button(self, label="Create")
        self.RenameButton = wx.Button(self, label="Rename")
        self.DeleteButton = wx.Button(self, label="Delete")

        self.SwitchButton.Bind(wx.EVT_BUTTON, self.OnSwitchProfile)
        self.SaveButton.Bind(wx.EVT_BUTTON, self.OnSaveProfile)
        self.CreateButton.Bind(wx.EVT_BUTTON, self.OnCreateProfile)
        self.RenameButton.Bind(wx.EVT_BUTTON, self.OnRenameProfile)
        self.DeleteButton.Bind(wx.EVT_BUTTON, self.OnDeleteProfile)

        buttons = wx.BoxSizer(wx.HORIZONTAL)
        buttons.Add(self.SwitchButton, flag=wx.RIGHT | wx.TOP, border=10)
        buttons.Add(self.SaveButton, flag=wx.RIGHT | wx.TOP, border=10)
        buttons.Add(self.CreateButton, flag=wx.RIGHT | wx.TOP, border=10)
        buttons.Add(self.RenameButton, flag=wx.RIGHT | wx.TOP, border=10)
        buttons.Add(self.DeleteButton, flag=wx.RIGHT | wx.TOP, border=10)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(title, flag=wx.LEFT | wx.TOP, border=10)
        sizer.Add(description, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        sizer.Add(self.ActiveProfileLabel, flag=wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        sizer.Add(self.ProfileList, proportion=1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        sizer.Add(buttons, flag=wx.LEFT | wx.BOTTOM, border=10)
        self.SetSizer(sizer)

        self.reloadFromSettings()

    def reloadFromSettings(self):
        profiles = self.BeamSettings.getProfiles()
        activeProfileId = self.BeamSettings.getActiveProfileId()

        self.profileIds = []
        profileRows = []
        selectedIndex = wx.NOT_FOUND

        for index, profile in enumerate(profiles):
            profileId = profile.get('Id', '')
            profileName = profile.get('Name', profileId)
            rowLabel = profileName
            if profileId == activeProfileId:
                rowLabel += ' (active)'
            if profile.get('Locked'):
                rowLabel += ' [locked]'

            self.profileIds.append(profileId)
            profileRows.append(rowLabel)

            if profileId == activeProfileId:
                selectedIndex = index

        self.ProfileList.Set(profileRows)
        if selectedIndex != wx.NOT_FOUND:
            self.ProfileList.SetSelection(selectedIndex)

        activeProfileLabel = 'Active profile: ' + self.BeamSettings.getActiveProfileName()
        if self.BeamSettings.isDirty():
            activeProfileLabel += ' (unsaved changes)'
        self.ActiveProfileLabel.SetLabel(activeProfileLabel)
        self.updateButtonStates()
        self.Layout()

    def getSelectedProfileId(self):
        selection = self.ProfileList.GetSelection()
        if selection == wx.NOT_FOUND:
            return None
        if selection >= len(self.profileIds):
            return None
        return self.profileIds[selection]

    def getSelectedProfile(self):
        selectedProfileId = self.getSelectedProfileId()
        if selectedProfileId is None:
            return None

        for profile in self.BeamSettings.getProfiles():
            if profile.get('Id') == selectedProfileId:
                return profile

        return None

    def updateButtonStates(self):
        selectedProfile = self.getSelectedProfile()
        hasSelection = selectedProfile is not None
        isActive = hasSelection and selectedProfile.get('Id') == self.BeamSettings.getActiveProfileId()
        isLocked = hasSelection and selectedProfile.get('Locked')

        self.SwitchButton.Enable(hasSelection and not isActive)
        self.SaveButton.Enable(hasSelection and isActive)
        self.RenameButton.Enable(hasSelection and not isLocked)
        self.DeleteButton.Enable(hasSelection and not isLocked)

    def showError(self, message):
        dialog = wx.MessageDialog(self, message, 'Profiles', wx.OK | wx.ICON_ERROR)
        dialog.ShowModal()
        dialog.Destroy()

    def refreshAfterProfileChange(self):
        self.mainFrame.updateSettings()

    def confirmPendingChanges(self, actionLabel, willReplaceCurrentState):
        if not self.BeamSettings.isDirty():
            return True

        activeProfileName = self.BeamSettings.getActiveProfileName()
        hasBeenPersisted = self.BeamSettings.hasActiveProfileBeenPersisted()
        if hasBeenPersisted:
            message = "Save changes to '" + activeProfileName + "' before " + actionLabel + "?"
            yesLabel = 'Save changes'
        else:
            message = "Save the new profile '" + activeProfileName + "' before " + actionLabel + "?"
            yesLabel = 'Save current profile'

        dialog = wx.MessageDialog(self, message, 'Unsaved profile changes', wx.YES_NO | wx.CANCEL | wx.ICON_QUESTION)
        if hasattr(dialog, 'SetYesNoCancelLabels'):
            dialog.SetYesNoCancelLabels(yesLabel, 'Discard changes', 'Cancel')
        result = dialog.ShowModal()
        dialog.Destroy()

        if result == wx.ID_YES:
            self.BeamSettings.saveActiveProfile()
            return True

        if result == wx.ID_NO:
            if willReplaceCurrentState:
                self.BeamSettings.clearDirty()
            return True

        return False

    def OnProfileSelected(self, event):
        self.updateButtonStates()

    def OnSwitchProfile(self, event):
        selectedProfileId = self.getSelectedProfileId()
        if selectedProfileId is None:
            return

        try:
            if not self.confirmPendingChanges('switching profiles', True):
                return
            self.BeamSettings.switchProfile(selectedProfileId)
            self.refreshAfterProfileChange()
        except Exception as exc:
            logging.error(exc, exc_info=True)
            self.showError(str(exc))

    def OnSaveProfile(self, event):
        selectedProfileId = self.getSelectedProfileId()
        if selectedProfileId != self.BeamSettings.getActiveProfileId():
            return

        try:
            self.BeamSettings.saveActiveProfile()
            self.refreshAfterProfileChange()
        except Exception as exc:
            logging.error(exc, exc_info=True)
            self.showError(str(exc))

    def OnCreateProfile(self, event):
        dialog = wx.TextEntryDialog(self, 'Profile name', 'Create profile')
        result = dialog.ShowModal()
        profileName = dialog.GetValue()
        dialog.Destroy()

        if result != wx.ID_OK:
            return

        try:
            self.BeamSettings.createProfile(profileName)
            self.refreshAfterProfileChange()
        except Exception as exc:
            logging.error(exc, exc_info=True)
            self.showError(str(exc))

    def OnRenameProfile(self, event):
        selectedProfile = self.getSelectedProfile()
        if selectedProfile is None:
            return

        dialog = wx.TextEntryDialog(self, 'Profile name', 'Rename profile')
        dialog.SetValue(selectedProfile.get('Name', ''))
        result = dialog.ShowModal()
        profileName = dialog.GetValue()
        dialog.Destroy()

        if result != wx.ID_OK:
            return

        try:
            self.BeamSettings.renameProfile(selectedProfile.get('Id'), profileName)
            self.mainFrame.reloadPreferencesPanels()
        except Exception as exc:
            logging.error(exc, exc_info=True)
            self.showError(str(exc))

    def OnDeleteProfile(self, event):
        selectedProfile = self.getSelectedProfile()
        if selectedProfile is None:
            return

        message = "Do you really want to delete '" + selectedProfile.get('Name', '') + "'?"
        dialog = wx.MessageDialog(self, message, 'Confirm deletion', wx.OK | wx.CANCEL | wx.ICON_QUESTION)
        result = dialog.ShowModal()
        dialog.Destroy()

        if result != wx.ID_OK:
            return

        try:
            willReplaceCurrentState = selectedProfile.get('Id') == self.BeamSettings.getActiveProfileId()
            if not self.confirmPendingChanges('deleting a profile', willReplaceCurrentState):
                return
            self.BeamSettings.deleteProfile(selectedProfile.get('Id'))
            self.refreshAfterProfileChange()
        except Exception as exc:
            logging.error(exc, exc_info=True)
            self.showError(str(exc))
