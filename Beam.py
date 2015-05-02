#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    Copyright (C) 2014 Mikael Holber http://mywebsite.com
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
import wx.html
import platform
import os
import sys

from bin.beamsettings import *
from bin.dialogs.beammainframe import beamMainFrame

#app = wx.App(redirect=True)    # Error messages go to popup window
app = wx.App(False) # Error messages go to terminal, for debugging purposes

########################################################
# Load Settings (global object)
########################################################
beamSettings.LoadConfig(beamSettings.defaultConfigFileName)

#Send error-log to file
if platform.system() == 'Windows' or platform.system() == 'Darwin':
    sys.stderr = open(os.path.join(os.path.expanduser("~"), "Beam-log.txt"),"w")
print (beamSettings.mainFrameTitle)

########################################################
# Start the main window
########################################################
top = beamMainFrame()       # Creates the main frame
top.Show()                      # Shows the main frame

########################################################
# Start the timer used to update the displayed data
########################################################

    # If the configuration have a timer on how often to update the data
try:
    # There is not timer, so create and start it
    timer = wx.Timer(top)
    top.Bind(wx.EVT_TIMER, top.updateData, timer)
    timer.Start(beamSettings._updateTimer)
except:
    # There is already a timer restart with new update timing
    timer.Stop()
    timer.Start(beamSettings._updateTimer)

app.MainLoop()                  # Start the main loop which handles events
