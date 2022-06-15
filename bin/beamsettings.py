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

import json
import wx
import platform
import logging
import os
from bin.beamutils import *
from bin.beamstrings import BeamStrings

#
# On start created as global object beamsettings.beamSettings
# stringResources[] must be initialized before
#
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


###############################################################
#
# Init
#
###############################################################
    def __init__(self):
        # protected variables
        # get initialized empty
        # later on set from config file
        self._moduleSelected    = None
        self._maxTandaLength    = None
        # module run() interval in milliseconds
        self._updtime       = None
        self._moodTransition       = None
        self._moodTransitionSpeed  = None
        self._logging              = True
        self._logPath              = None
        self._loglevel              = None
        # not in use, kept for configfile
        self.__showStatusbar        = None
        self._allModulesSettings    = None
        self._rules                 = None

        # self.applicationpath = getBeamHomePath()
        stringsfilename = os.path.join(getBeamResourcesPath(), 'json', 'strings.json')
        self._beamStrings = BeamStrings(stringsfilename)

    def getString(self, key):
        value = self._beamStrings.getString(key)

        return value

    def loadConfig(self):
        # configfilename="beamconfig.json"

        beamconfigfile = self.__getConfigFilePath()
        if not os.path.isfile(beamconfigfile):
            # if there is no configfile yet
            logging.warning("BeamSettings.loadConfig(): configfile does not exist '" + beamconfigfile + "'")
            oldconfigfile = os.path.join(getUserHomePath(), "BeamConfig.json")
            if os.path.isfile(oldconfigfile):
                logging.warning("BeamSettings.loadConfig(): using configfile in old directory: '" + oldconfigfile + "'")
                beamconfigfile = oldconfigfile
            else:
                # beamconfigpath = getBeamHomePath()
                beamconfigfile = self.__getDefaultConfigFilePath()
                logging.warning("BeamSettings.loadConfig(): loading default configfile '" + beamconfigfile + "'")
                # Use original configfile which is the settingsfile below
        beamConfigData = self.__loadConfigData(beamconfigfile)

        # Also load the default configfile
        defaultconfigfile = os.path.join(getBeamResourcesPath(), "json", self.getString("configfilename"))
        defaultConfigData = self.__loadConfigData(defaultconfigfile)

        # merges new properties from defaultConfigData into beamConfigData
        self.__readConfig(beamConfigData, defaultConfigData)
        return

    def saveConfig(self):
        output = {}

        output['Configname']       = "Default Configuration"
        output['Comment']          = "This is a configuration file for Beam"
        output['Author']           = "Mikael Holber & Horia Uifaleanu - 2015"
        output['Module']           = self._moduleSelected
        output['MaxTandaLength']   = self._maxTandaLength
        output['Updtime']          = self._updtime
        output['MoodTransition']           = self._moodTransition
        output['MoodTransitionSpeed']      = self._moodTransitionSpeed
        output['Logging']              = self._logging
        output['LogPath']              = self._logPath
        output['LogLevel']              = self._loglevel
        output['ShowStatusbar']        = self.__showStatusbar

        # Dictionaries
        output['AllModules']           = self._allModulesSettings
        output['Rules']                = self._rules
        output['Moods']                = self._moods

        beamconfigfile = self.__getConfigFilePath()
        self.__dumpConfigFile(beamconfigfile, output)
        logging.info("BeamSettings.saveConfig(): configfile '" + beamconfigfile + "'")

        return


    #
    # Returns the value of ConfigData
    # and if that does not exist
    # replaced by the value of ConfigDataOriginal
    #
    '''
    def __extractSetting(self, beamConfigData, defaultConfigData, key):
        try:
            output = beamConfigData[key]
        except:
            output = defaultConfigData[key]
        return output
    '''

    def __getConfigFilePath(self):

        configfilepath = os.path.join(getBeamConfigPath(), self.getString("configfilename"))

        return configfilepath

    def __getDefaultConfigFilePath(self):

        defaultfilepath = os.path.join(getBeamHomePath(), 'resources', 'json', self.getString("configfilename"))

        return defaultfilepath


    def __loadConfigData(self, inputconfigfile):
        configFile = open(inputconfigfile, 'r')
        try:
            configData = json.load(configFile)
        finally:
            configFile.close()

        return configData



    #
    # Initializes protected variables by copying from ConfigData or ConfigDataOriginal
    #
    def __readConfig(self, beamConfigData, defaultConfigData):

        # copies values and dicts from user config to default config, but not lists
        # so new values in lists get created on apply/save of user config
        mergeDict(beamConfigData, defaultConfigData)

        self._moduleSelected        = defaultConfigData['Module']         # Player to read from
        self._maxTandaLength        = defaultConfigData['MaxTandaLength'] # Longest tandas, optimize for performance
        self._updtime               = defaultConfigData['Updtime']        # mSec between reading
        self._moodTransition        = defaultConfigData['MoodTransition']
        self._moodTransitionSpeed   = defaultConfigData['MoodTransitionSpeed']
        self.__showStatusbar         = defaultConfigData['ShowStatusbar']
        self._logging               = defaultConfigData['Logging']
        self._logPath               = defaultConfigData['LogPath']
        if self._logPath == '':
            self._logPath = getBeamConfigPath()
        self._loglevel           = defaultConfigData['LogLevel']

        # does not work
        # mergedConfigData = beamConfigData.expand(defaultConfigData)
        # AttributeError: 'dict' object has no attribute 'expand'

        # mergedConfigData = mergeDict(defaultConfigData, beamConfigData)
        # mergedConfigData = mergeDict(beamConfigData, defaultConfigData)
        # Dictionaries
        # ModulesSettings from default config
        # does not work properly
        # self._allModulesSettings    = defaultConfigData['AllModules']

        self._allModulesSettings    = defaultConfigData['AllModules']
        # self._rules                 = self.__extractSetting(beamConfigData, defaultConfigData, 'Rules')
        self._rules                 = beamConfigData['Rules']
        # self._moods                 = self.__extractSetting(beamConfigData, defaultConfigData, 'Moods')
        self._moods                 = beamConfigData['Moods']

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

        self._currentModules = [s for s in tmp['Modules']]

        if self._moduleSelected == '':
            self._moduleSelected = [s for s in tmp['Modules']][0]

        return


    def __dumpConfigFile(self, outputConfigFile, output):

        beamconfigpath = getBeamConfigPath()
        if not os.path.isdir(beamconfigpath):
            logging.warning("BeamSettings.__dumpConfigFile(): '" + beamconfigpath + "' does not exist, creating it.")
            os.mkdir(beamconfigpath)

        if not os.path.isfile(outputConfigFile):
            # if the file does not exist use default from beam home
            logging.info("BeamSettings.__dumpConfigFile(): configfile does not exist '" + outputConfigFile + "'")

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



#
# On start create as global object
#

# initialized on first importin beam.py
# __init__  and initializes protected variables stringResources
beamSettings = BeamSettings()
