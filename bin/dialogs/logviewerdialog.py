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
# This Python file uses the following encoding: utf-8

#
# A self-contained "tail -f" style viewer for the Beam log file. Deliberately
# independent from the logging system: it only reads the file at the path it is
# given, so nothing it does can affect what gets logged. It tails by remembering
# the byte offset it has already shown and reading only the new bytes on each
# poll, so the whole file is never re-read.
#

import logging
import os
import platform
import subprocess

import wx

# How much of the file to show on first open (tail, not the whole file).
INITIAL_TAIL_BYTES = 256 * 1024
INITIAL_MAX_LINES = 1000

# Upper bound on what the text control holds, to cap memory. When exceeded the
# oldest text is trimmed from the top on a line boundary.
MAX_VIEW_CHARS = 1024 * 1024

POLL_INTERVAL_MS = 750

FILE_NOT_FOUND_MESSAGE = 'Log file not found yet.'


class LogViewerDialog(wx.Frame):
    def __init__(self, parent, log_file_path):
        wx.Frame.__init__(self, parent, title='Beam Log', size=(900, 600))

        self._log_file_path = log_file_path
        # Byte offset up to which file content has already been displayed.
        self._offset = 0
        # True once the initial tail has been loaded (file existed at least once).
        self._initialized = False
        # Avoid repainting the "not found" placeholder on every poll.
        self._showing_not_found = False

        panel = wx.Panel(self)
        outer = wx.BoxSizer(wx.VERTICAL)

        self.logText = wx.TextCtrl(
            panel,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2 | wx.TE_DONTWRAP,
        )
        monospace = wx.Font(
            10,
            wx.FONTFAMILY_TELETYPE,
            wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_NORMAL,
        )
        self.logText.SetFont(monospace)
        outer.Add(self.logText, 1, wx.EXPAND | wx.ALL, 6)

        controls = wx.BoxSizer(wx.HORIZONTAL)
        self.autoScrollCheckBox = wx.CheckBox(panel, label='Auto-scroll')
        self.autoScrollCheckBox.SetValue(True)
        controls.Add(self.autoScrollCheckBox, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 12)
        controls.AddStretchSpacer()

        self.copyButton = wx.Button(panel, label='Copy')
        self.clearButton = wx.Button(panel, label='Clear View')
        self.openFolderButton = wx.Button(panel, label='Open Log Folder')
        self.closeButton = wx.Button(panel, label='Close')
        for button in (self.copyButton, self.clearButton, self.openFolderButton, self.closeButton):
            controls.Add(button, 0, wx.LEFT, 6)
        outer.Add(controls, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 6)

        panel.SetSizer(outer)

        self.copyButton.Bind(wx.EVT_BUTTON, self.OnCopy)
        self.clearButton.Bind(wx.EVT_BUTTON, self.OnClearView)
        self.openFolderButton.Bind(wx.EVT_BUTTON, self.OnOpenLogFolder)
        self.closeButton.Bind(wx.EVT_BUTTON, self.OnCloseButton)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)

        self._loadInitial()
        self.timer.Start(POLL_INTERVAL_MS)

    #
    # Initial load: show the tail of the file (last lines) rather than the whole
    # thing, and set the offset to the current end so polling only appends what
    # is written from now on.
    #
    def _loadInitial(self):
        if not os.path.isfile(self._log_file_path):
            self._showNotFound()
            return

        try:
            with open(self._log_file_path, 'rb') as handle:
                handle.seek(0, os.SEEK_END)
                size = handle.tell()
                read_size = min(size, INITIAL_TAIL_BYTES)
                handle.seek(size - read_size)
                data = handle.read()
            self._offset = size
        except OSError as error:
            # File exists but is momentarily locked/unavailable; try again on
            # the next poll instead of failing to open the viewer.
            logging.error(error, exc_info=True)
            self._showNotFound()
            return

        text = data.decode('utf-8', errors='replace')
        lines = text.splitlines()
        # If the tail started mid-line (file larger than the chunk), drop the
        # leading partial line so the first visible line is complete.
        if read_size < size and lines:
            lines = lines[1:]
        if len(lines) > INITIAL_MAX_LINES:
            lines = lines[-INITIAL_MAX_LINES:]

        self._initialized = True
        self._showing_not_found = False
        self.logText.ChangeValue('\n'.join(lines))
        if lines:
            self.logText.AppendText('\n')
        self._scrollIfNeeded(force=True)

    def _showNotFound(self):
        if self._showing_not_found:
            return
        self._showing_not_found = True
        self.logText.ChangeValue(FILE_NOT_FOUND_MESSAGE + '\n')

    def OnTimer(self, event):
        try:
            self._poll()
        except Exception as error:
            # Never let a polling hiccup take down the timer or the app.
            logging.error(error, exc_info=True)

    def _poll(self):
        if not os.path.isfile(self._log_file_path):
            self._showNotFound()
            return

        # File (re)appeared after being missing, or was never loaded.
        if not self._initialized:
            self._loadInitial()
            return

        try:
            size = os.path.getsize(self._log_file_path)
        except OSError:
            # Temporarily unavailable/locked - retry next tick.
            return

        # Truncation or rotation: file shrank below where we last read, so the
        # old offset is meaningless. Reset and read from the start.
        if size < self._offset:
            self._offset = 0

        if size == self._offset:
            return

        try:
            with open(self._log_file_path, 'rb') as handle:
                handle.seek(self._offset)
                data = handle.read()
                self._offset += len(data)
        except OSError:
            return

        if not data:
            return

        new_text = data.decode('utf-8', errors='replace')
        self._appendText(new_text)

    def _appendText(self, text):
        # Preserve the user's scroll position when auto-scroll is off.
        auto_scroll = self.autoScrollCheckBox.GetValue()
        insertion_point = self.logText.GetInsertionPoint()

        self.logText.AppendText(text)
        self._trimIfNeeded()

        if auto_scroll:
            self._scrollIfNeeded(force=True)
        else:
            self.logText.SetInsertionPoint(min(insertion_point, self.logText.GetLastPosition()))
            self.logText.ShowPosition(self.logText.GetInsertionPoint())

    def _trimIfNeeded(self):
        last_position = self.logText.GetLastPosition()
        if last_position <= MAX_VIEW_CHARS:
            return

        excess = last_position - MAX_VIEW_CHARS
        value = self.logText.GetValue()
        # Trim on a line boundary so we never leave a half line at the top.
        newline_index = value.find('\n', excess)
        cut_to = newline_index + 1 if newline_index != -1 else excess
        self.logText.Remove(0, cut_to)

    def _scrollIfNeeded(self, force=False):
        if not (force or self.autoScrollCheckBox.GetValue()):
            return
        self.logText.SetInsertionPointEnd()
        self.logText.ShowPosition(self.logText.GetLastPosition())

    def OnCopy(self, event):
        selection = self.logText.GetStringSelection()
        text = selection if selection else self.logText.GetValue()
        if not text:
            return
        if wx.TheClipboard.Open():
            try:
                wx.TheClipboard.SetData(wx.TextDataObject(text))
            finally:
                wx.TheClipboard.Close()

    #
    # Clears only the on-screen text. The offset is left untouched so polling
    # keeps appending new lines from the current file position; the real log
    # file is never modified.
    #
    def OnClearView(self, event):
        self.logText.ChangeValue('')

    def OnOpenLogFolder(self, event):
        folder = os.path.dirname(self._log_file_path)
        try:
            system = platform.system()
            if system == 'Windows':
                os.startfile(folder)
            elif system == 'Darwin':
                subprocess.Popen(['open', folder])
            else:
                subprocess.Popen(['xdg-open', folder])
        except Exception as error:
            logging.error(error, exc_info=True)
            wx.MessageBox(
                'Could not open the log folder:\n{0}'.format(folder),
                'Beam Log',
                wx.OK | wx.ICON_WARNING,
            )

    def OnCloseButton(self, event):
        self.Close()

    def OnClose(self, event):
        if self.timer.IsRunning():
            self.timer.Stop()
        self.Destroy()
