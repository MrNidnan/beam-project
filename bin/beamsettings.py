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
import logging
import os

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
    defaultLogFileName = stringResources["defaultLogFileName"]
    defaultLogLevel = stringResources["defaultLogLevel"]
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
        self._moodTransition       = ''
        self._moodTransitionSpeed  = ''
        self._logging              = ''
        self._logPath              = ''
        self._logLevel              = ''
        self._showStatusbar        = ''
        self._allModulesSettings    = ''
        self._rules                 = ''
        self._beamVersion = BeamSettings.beamVersion

###############################################################
#
# LOAD Config
#
###############################################################
    def LoadConfig(self, inputConfigFile):
        try:
            #Try loading current config file in home directory
            configfile = os.path.join(os.path.expanduser("~"), inputConfigFile)
            ConfigData = self.OpenSetting(configfile)
        except Exception as e:
            logging.warning("BeamSettings.LoadConfig($HOME) not loaded")
            logging.warning(e)
            logging.warning("Loading default configfile")
            # Use original configfile which is the settingsfile below
            configfile = os.path.join(os.getcwd(), inputConfigFile)
            ConfigData = self.OpenSetting(configfile)

        # Also load the original settingsfile
        configfile = os.path.join(os.getcwd(), inputConfigFile)
        ConfigDataOriginal = self.OpenSetting(configfile)
        self.ReadConfig(ConfigData, ConfigDataOriginal)

        return


    def ReadConfig(self, ConfigData, ConfigDataOriginal):
        self._moduleSelected        = self.ExtractSetting(ConfigData,ConfigDataOriginal,'Module')         # Player to read from
        self._maxTandaLength        = self.ExtractSetting(ConfigData,ConfigDataOriginal,'MaxTandaLength') # Longest tandas, optimize for performance
        self._updateTimer           = self.ExtractSetting(ConfigData,ConfigDataOriginal,'Updtime')        # mSec between reading
        self._moodTransition        = self.ExtractSetting(ConfigData,ConfigDataOriginal,'MoodTransition')
        self._moodTransitionSpeed   = self.ExtractSetting(ConfigData,ConfigDataOriginal,'MoodTransitionSpeed')
        self._showStatusbar         = self.ExtractSetting(ConfigData,ConfigDataOriginal,'ShowStatusbar')
        self._logging               = self.ExtractSetting(ConfigData,ConfigDataOriginal,'Logging')
        self._logPath               = self.ExtractSetting(ConfigData,ConfigDataOriginal,'LogPath')
        if self._logPath == '':
            self._logPath = os.path.join(os.path.expanduser("~"), BeamSettings.defaultLogFileName)
        self._logLevel              = self.ExtractSetting(ConfigData, ConfigDataOriginal, 'LogLevel')
        if self._logLevel == '':
            self._logLevel = BeamSettings.defaultLogLevel

        # Dictionaries
        self._allModulesSettings        = ConfigDataOriginal['AllModules']
        self._rules                     = self.ExtractSetting(ConfigData,ConfigDataOriginal,'Rules')
        self._moods                     = self.ExtractSetting(ConfigData,ConfigDataOriginal,'Moods')

        # Set OS-specific variables
        if platform.system() == 'Linux':
            tmp = self._allModulesSettings[0]
            self._preferencesSize = (500, 500)
            self._moodSize = (480,600)
        if platform.system() == 'Windows':
            tmp = self._allModulesSettings[1]
            self._preferencesSize = (500, 500)
            self._moodSize = (420,550)
        if platform.system() == 'Darwin':
            tmp = self._allModulesSettings[2]
            self._preferencesSize = (400, 600)
            self._moodSize = (400,550)

        # self._currentModules = [s.encode('utf-8') for s in tmp['Modules']]
        self._currentModules = [s for s in tmp['Modules']]

        if self._moduleSelected == '':
            self._moduleSelected = [s for s in tmp['Modules']][0]

        return
#
# SUPPORTING FUNCTIONS
#
    def ExtractSetting(self, ConfigData, ConfigDataOriginal, key):
        try:
            output = ConfigData[key]
        except:
            output = ConfigDataOriginal[key]
        return output

    def OpenSetting(self, inputConfigFile):
        ConfigFile = open(inputConfigFile, 'r')

        try:
            ConfigData = json.load(ConfigFile)
            # Validate configfile version against string.txt version

            # Added since V0.4
            if len(ConfigData['AllModules'][0]['Modules']) == 5: # System: Linux
                ConfigData['AllModules'][0]['Modules'].append('Mixxx')
            if len(ConfigData['AllModules'][1]['Modules']) == 5: # System: Windows
                ConfigData['AllModules'][1]['Modules'].append('Mixxx')
            if len(ConfigData['AllModules'][2]['Modules']) == 6: # System: Mac
                ConfigData['AllModules'][2]['Modules'].append('Mixxx')

            if not ConfigData['ConfigVersion'] == self._beamVersion:
                logging.warning("Configfile version " + ConfigData['ConfigVersion'] + " differs from current " + self._beamVersion )
                # let the version untouched for beta tests
                # ConfigData['ConfigVersion'] = self._beamVersion;
        finally:
            ConfigFile.close()

        return ConfigData


###############################################################
#
# Save Config
#
###############################################################
    def SaveConfig(self, outputConfigFile):
        output = {}

        output['Configname']       = "Default Configuration"
        output['Comment']          = "This is a configuration file for Beam"
        output['Author']           = "Mikael Holber & Horia Uifaleanu - 2015"
        output['Module']           = self._moduleSelected
        output['MaxTandaLength']   = self._maxTandaLength
        output['Updtime']          = self._updateTimer
        output['MoodTransition']           = self._moodTransition
        output['MoodTransitionSpeed']      = self._moodTransitionSpeed
        output['Logging']              = self._logging
        output['LogPath']              = self._logPath
        output['LogLevel']              = self._logLevel
        output['ShowStatusbar']        = self._showStatusbar
        output['ConfigVersion']        = self._beamVersion

        # Dictionaries
        output['AllModules']           = self._allModulesSettings
        output['Rules']                = self._rules
        output['Moods']                = self._moods

        # Write config file to user home dir
        writepath = os.path.join(os.path.expanduser("~"), outputConfigFile)
        self.WriteSetting(writepath, output)

        return


    def WriteSetting(self, outputConfigFile, output):
        ConfigFile = open(outputConfigFile, 'w')
        try:
            # Writing different format depending on platform
            if platform.system() == 'Windows':
                # json.dump(output, ConfigFile, indent=2, encoding="latin-1")
                json.dump(output, ConfigFile, indent=2)
            else:
                # json.dump(output, ConfigFile, indent=2, encoding="utf-8")
                json.dump(output, ConfigFile, indent=2)
        finally:
            ConfigFile.close()

        return

###############################################################
#
# Create object
#
###############################################################

beamSettings = BeamSettings()
