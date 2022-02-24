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
import os
import sys
import logging


#
# Linux ~, $HOME
# Windows %HOMEPATH%
#
def getUserHomePath():
    userhomepath = os.path.expanduser("~")

    return userhomepath


#
# directory where beam got started from
#
def getBeamHomePath():
    if getattr(sys, 'frozen', False):
        # PyInstaller one-file
        # application_path = os.path.dirname(sys.executable)
        apphomepath = sys._MEIPASS
        # print("Path PyInstaller: " + application_path)
    else:
        apphomepath = os.getcwd()
        # print("Path Python: " + appPath)

    # print(os.listdir(appPath))
    return apphomepath

def getBeamResourcesPath():
   return os.path.join(getBeamHomePath(), "resources")

#
# config directory in user ~/.beam/"
def getBeamConfigPath():
    userhomepath = getUserHomePath()
    beamconfigpath = os.path.join(os.path.expanduser("~"), ".beam")

    return beamconfigpath

def getLogLevel(loglevelname):
    loglevel = None
    try:
        logLevelDict = {
            'Debug': logging.DEBUG,
            'Info': logging.INFO,
            'Warning': logging.WARNING,
            'Error': logging.ERROR,
            'Critical': logging.CRITICAL
        }
        # set now loglevelname from configfile
        loglevel = logLevelDict[loglevelname]
    except Exception as e:
        logging.error("beam: unknown loglevelname: '" + loglevelname + "' using Debug'")
        loglevel = logging.DEBUG

    return loglevel
