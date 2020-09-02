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

from bin.beamsettings import *
from bin.dialogs.beammainframe import beamMainFrame


app = wx.App(False) # Error messages go to terminal

########################################################
# Load Settings (global object)
########################################################
beamSettings.LoadConfig(beamSettings.defaultConfigFileName)

########################################################
# Select logging method (terminal or file)
########################################################

logPath = beamSettings._logPath
logFormat = '%(asctime)s : %(levelname)s : %(message)s'

try:
    logLevelDict = {
        'Debug': logging.DEBUG,
        'Info': logging.INFO,
        'Warning': logging.WARNING,
        'Error': logging.ERROR,
        'Critical': logging.CRITICAL
    }

    logLevel = logLevelDict[beamSettings._logLevel]
except Exception as e:
    print(e)
    logLevel = logging.DEBUG
    pass


# set up logging to file
logging.basicConfig(format=logFormat, level=logLevel , filename=logPath, filemode='w')

# set up logging to console also
console = logging.StreamHandler()
console.setLevel(logLevel)
logging.getLogger("").addHandler(console)

# if beamSettings._logging == 'True':
#    sys.stdout = open(beamSettings._logPath,"w")

print(beamSettings.mainFrameTitle + " logging to " + logPath)


########################################################
# Start the main window
########################################################
top = beamMainFrame()       # Creates the main frame
# __init__() starts timer for updating, transition, first updateData()
top.Show()                  # Shows the main frame

########################################################
# Start the main loop
########################################################

app.MainLoop()              # Start the main loop which handles events
