import wx


#
# Small modal dialog to show a temporary centered message on the display.
#
class ShowMessageDialog(wx.Dialog):

    DEFAULT_DURATION = 15
    MIN_DURATION = 5
    MAX_DURATION = 60

    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, title="Show Message")

        panel = wx.Panel(self)

        messageLabel = wx.StaticText(panel, label="Message")
        self.messageInput = wx.TextCtrl(panel, size=(320, 120), style=wx.TE_MULTILINE)

        durationLabel = wx.StaticText(panel, label="Duration (seconds)")
        self.durationInput = wx.SpinCtrl(
            panel,
            min=self.MIN_DURATION,
            max=self.MAX_DURATION,
            initial=self.DEFAULT_DURATION,
        )

        self.showButton = wx.Button(panel, wx.ID_OK, label="Show")
        self.cancelButton = wx.Button(panel, wx.ID_CANCEL, label="Cancel")
        self.showButton.SetDefault()

        durationSizer = wx.BoxSizer(wx.HORIZONTAL)
        durationSizer.Add(durationLabel, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        durationSizer.Add(self.durationInput, 0)

        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        buttonSizer.Add(self.showButton, 0, wx.RIGHT, 10)
        buttonSizer.Add(self.cancelButton, 0)

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(messageLabel, 0, wx.ALL, 10)
        vbox.Add(self.messageInput, 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        vbox.Add(durationSizer, 0, wx.ALL, 10)
        vbox.Add(buttonSizer, 0, wx.ALL | wx.ALIGN_RIGHT, 10)

        panel.SetSizer(vbox)
        vbox.SetSizeHints(self)

        self.messageInput.SetFocus()

    def getMessageText(self):
        return self.messageInput.GetValue()

    def getDurationSeconds(self):
        return int(self.durationInput.GetValue())
