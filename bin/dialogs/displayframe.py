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
import wx.html
import wx.lib.delayedresult
from bin.beamsettings import *
from bin.dialogs.displaypanel import DisplayPanel


class DisplayFrame(wx.Frame):

    # Called by beam.py
    def __init__(self, displayData):

        # wx.DEFAULT_FRAME_STYLE
        # wx.CAPTION | wx.RESIZE_BORDER
        # wxFULLSCREEN_NOMENUBAR
        # wxFULLSCREEN_NOSTATUSBAR
        # wxFULLSCREEN_NOBORDER
        # wxFULLSCREEN_NOCAPTION
        # wx.FULLSCREEN_ALL
        # wx.RESIZE_BORDER
        framestyle = wx.DEFAULT_FRAME_STYLE & ~ (wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        wx.Frame.__init__(self, parent=None, title="F11: Full Screen", pos=(200,200), size=(800,600), style=framestyle)

        ###################
        # CLASS VARIABLES #
        ###################
        # self.BeamSettings = BeamSettings
        # Do not use parent for threading
        self.displayData = displayData
        self.nowPlayingData = displayData.nowPlayingData

        self.displayPanel = DisplayPanel(self, self.displayData)
        self.SetDoubleBuffered(True)

        # Events.
        self.Bind(wx.EVT_CHAR_HOOK, self.onKeyUP)

        self.Bind(wx.EVT_CLOSE, self.onClose)
        # !!! Funktioniert nicht, nur implizit on caption
        # self.Bind(wx.EVT_LEFT_DCLICK, self.onLeftDClick)
        self.Bind(wx.EVT_MAXIMIZE, self.onMaximize, self)

        # Background
        self.modifiedBitmap = None
        self.SetBackgroundColour(wx.BLACK)
        self.Bind(wx.EVT_SIZE, self.onSize)
        # self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)

        ########################## END FRAME INITIALIZATION #########################


########################################################
# Buttons and menues
########################################################


    def onKeyUP(self, event):
        try:
            keyCode = event.GetKeyCode()
            if keyCode == wx.WXK_ESCAPE:
                if self.IsFullScreen():
                    self.ShowFullScreen(False)
                else:
                    self.onClose(event)
                # event.Skip()
            if keyCode == wx.WXK_F11:
                self.ShowFullScreen(not self.IsFullScreen())
                # event.Skip()
        except Exception as e:
            logging.error(e, exc_info=True)


    def onMaximize(self, event):
        try:
            # ??? Needed for Mac
            # if platform.system() == 'Darwin':
            #   self.showStatusBar()
            if self.IsFullScreen():
                self.ShowFullScreen(False)
                self.Maximize(False)
            else:
                self.ShowFullScreen(True)
        except Exception as e:
            logging.error(e, exc_info=True)


    #
    # resize displayPanel
    #
    def onSize(self, size):
        try:
            cliWidth, cliHeight = self.GetClientSize()
            if not cliWidth or not cliHeight:
                return
            # size displayPanel to full frame
            self.displayPanel.SetSize(cliWidth,cliHeight);
            # Triggers displayPanel.OnSize()
        except Exception as e:
            logging.error(e, exc_info=True)

    #
    # Hide on close event
    #
    def onClose(self, event):
        try:
            self.Hide()
        except Exception as e:
            logging.error(e, exc_info=True)

