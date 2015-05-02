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
#    Version 1.0
#       - Initial release
#
# This Python file uses the following encoding: utf-8

import json, wx, platform
import io, os, sys

###############################################################
#
# BeamSettings
#
###############################################################

class BeamSettings:
    # Define Dictionaries
    # these are static class variables
    FontTypeDictionary = {"Decorative":wx.DECORATIVE, 
                    "Default":wx.FONTFAMILY_DEFAULT,
                    "Modern":wx.FONTFAMILY_MODERN,
                    "Roman":wx.FONTFAMILY_ROMAN,
                    "Script":wx.FONTFAMILY_SCRIPT,
                    "Swiss":wx.FONTFAMILY_SWISS,
                    "Teletype":wx.FONTFAMILY_TELETYPE
                    }
    FontWeightDictionary = {"Bold":wx.BOLD,
                   "Light":wx.FONTWEIGHT_LIGHT,
                   "Normal":wx.FONTWEIGHT_NORMAL
                    }
    FontStyleDictionary = {"Italic":wx.ITALIC,
                  "Normal":wx.FONTSTYLE_NORMAL,
                  "Slant":wx.FONTSTYLE_SLANT
                    }

    # strings resources JSON format
    filename = os.path.join(os.getcwd(), 'resources', 'text', 'strings.txt')
    stringResources = json.load(open(filename, "r"))

    defaultConfigFileName = stringResources["defaultConfigFileName"]
    mainFrameTitle = stringResources["mainFrameTitle"]
    aboutDialogDescription = stringResources["aboutDialogDescription"]
    aboutDialogLicense = stringResources["aboutDialogLicense"]
    aboutCopyright = stringResources["aboutCopyright"]
    aboutWebsite = stringResources["aboutWebsite"]
    aboutDeveloper = stringResources["aboutDeveloper"]
    aboutArtist = stringResources["aboutArtist"]
    beamVersion = stringResources["version"]

###############################################################
#
# Init
#
###############################################################
    def __init__(self):
        self._moduleSelected    = ''
        self._maxTandaLength    = ''
        self._updateTimer       = ''
        self._DefaultBackground    = ''
        self._allModulesSettings    = ''
        self._DefaultDisplaySettings     = ''
        self._rules                 = ''

###############################################################
#
# LOAD Config
#
###############################################################
    def LoadConfig(self, inputConfigFile):
        try:
            #Try loading in home directory
            ConfigData = self.OpenSetting(os.path.join(os.path.expanduser("~"), inputConfigFile))
            self.ReadConfig(ConfigData)
        except:
            #Otherwise read default setting
            ConfigData = self.OpenSetting(os.path.join(os.getcwd(), inputConfigFile))
            self.ReadConfig(ConfigData)
        return


    def ReadConfig(self, ConfigData):
        self._moduleSelected        = ConfigData[u'Module']         # Player to read from
        self._maxTandaLength        = ConfigData[u'MaxTandaLength'] # Longest tandas, optimize for performance
        self._updateTimer           = ConfigData[u'Updtime']        # mSec between reading
        self._DefaultBackground   = ConfigData[u'DefaultBackgroundImage']# Relative path to background, use 1920x1080 for best performance

        # Dictionaries
        self._allModulesSettings    = ConfigData[u'AllModules']
        self._DefaultDisplaySettings     = ConfigData[u'DefaultDisplay']
        self._rules                 = ConfigData[u'Rules']
        self._moods                 = ConfigData[u'Moods']

        # Set modules for operating system
        if platform.system() == 'Linux':
            tmp = self._allModulesSettings[0]
        if platform.system() == 'Windows':
            tmp = self._allModulesSettings[1]
        if platform.system() == 'Darwin':
            tmp = self._allModulesSettings[2]

        self._currentModules = [s.encode('utf-8') for s in tmp[u'Modules']]

        if self._moduleSelected == '':
            self._moduleSelected = [s.encode('utf-8') for s in tmp[u'Modules']][0]
        return


    def OpenSetting(self, inputConfigFile):
        ConfigFile = open(inputConfigFile, 'r')
        ConfigData = json.load(ConfigFile)
        ConfigFile.close()
        return ConfigData

###############################################################
#
# Save Config
#
###############################################################
    def SaveConfig(self, outputConfigFile):

        output = {}

        output[u'Configname']       = "Default Configuration"
        output[u'Comment']          = "This is a configuration file for Beam"
        output[u'Author']           = "Mikael Holber & Horia Uifaleanu - 2015"
        output[u'Module']           = self._moduleSelected
        output[u'MaxTandaLength']   = self._maxTandaLength
        output[u'Updtime']          = self._updateTimer
        output[u'DefaultBackgroundImage']    = self._DefaultBackground

        # Dictionaries
        output[u'AllModules']           = self._allModulesSettings
        output[u'DefaultDisplay']              = self._DefaultDisplaySettings
        output[u'Rules']                = self._rules
        output[u'Moods']                = self._moods

        # Write config file to home dir
        self.WriteSetting(os.path.join(os.path.expanduser("~"),outputConfigFile), output)

        return


    def WriteSetting(self, outputConfigFile, output):
        ConfigFile = open(outputConfigFile, 'w')
        # Writing different format depending on platform
        if platform.system() == 'Windows':
            json.dump(output, ConfigFile, indent=2, encoding="latin-1")
        else:
            json.dump(output, ConfigFile, indent=2, encoding="utf-8")
        ConfigFile.close()
        return 

###############################################################
#
# Create object
#
###############################################################

beamSettings = BeamSettings()
