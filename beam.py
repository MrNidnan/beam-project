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
import logging
from logging import *

from bin.beamutils import *

# initializes public variables of beamsettings.beamSettings
# from stringResuorces by BeamSettings() __init__
from bin.beamsettings import *
from bin.dialogs.mainframe import MainFrame

try:
    # beam config did not get loaded here
    logformat = "%(asctime)s : %(levelname)s : %(message)s"
    dateformat = "%Y-%m-%d %H:%M:%S"
    # there is a preliminary log level in the strings.json
    loglevel = getLogLevel(beamSettings.loglevel)
    logging.basicConfig(format=logformat, datefmt=dateformat, level=loglevel, stream=sys.stdout)
    # logging and stringResources default is WARNING
    rootLogger = logging.getLogger()
    # for further logging configuration
except Exception as e:
    logging.error(e, exc_info=True)

try:
    app = wx.App(False)  # Error messages go to terminal

    # apply
    # beamconfig.json
    # Reads into ConfigData (beamconfig) and OriginalConfigData (beamhome)
    beamSettings.loadConfig()
    # now beamconfig.json is read, from config or home dir
except Exception as e:
    logging.error(e, exc_info=True)

# handle logging related exceptions in a separae block
try:
    rootLogger.setLevel(logging.INFO)
    # To publish sume start infos

    logpath = beamSettings._logPath
    try:
        if not os.path.isdir(logpath):
            logging.info("Beam: '" + logpath + "' does not exist, creating it for logging.")
            os.mkdir(logpath)
    except Exception as e:
        # show must go on, try logging to $USERHOME instead
        logPath = getUserHomePath()
        logging.error(e, exc_info=True)

    logfilepath = os.path.join(logpath, beamSettings.logfilename)
    if os.path.isdir(logpath):
        # set up additional logging to file
        fileHandler = logging.FileHandler(logfilepath,  mode='w')
        # w=overwrwrite
        logFormatter = logging.Formatter(logformat, dateformat)
        fileHandler.setFormatter(logFormatter)
        # fileHandler.setLevel(loglevel)
        # level set by rootLogger
        rootLogger.addHandler(fileHandler)
    else:
        logging.error("Beam: Directory '" + logpath + "' does not exist, logging to stdout only", exc_info=True)
        # no logging at the first call because it reads the logpath

    logging.info("Beam version: V" + beamSettings.beamversion)
    logging.info("Beam home dir: '" + getBeamHomePath() + "'")
    logging.info("Beam config dir: " + getBeamConfigPath() + "'")
    logging.info("Beam logfile: '" + logpath + "'")

    loglevel = getLogLevel(beamSettings._loglevel)
    rootLogger.setLevel(loglevel)
except Exception as e:
    logging.error(e, exc_info=True)

try:
    ########################################################
    # Start the main window
    ########################################################
    # mainFrame = beamMainFrame()       # Creates the main frame
    # Main Window now with preferences and preview
    mainFrame = MainFrame()       # Creates the main frame

    # __init__() starts timer for updating, transition, first updateData()
    mainFrame.Show()                  # Shows the main frame

    ########################################################
    # Start the main loop
    ########################################################

    app.MainLoop()              # Start the main loop which handles events
except Exception as e:
    logging.error(e, exc_info=True)

