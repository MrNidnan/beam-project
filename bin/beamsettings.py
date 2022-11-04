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
from bin.DMX.dmxmodule import DMXlibrary
from copy import deepcopy

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


    def __init__(self):
        # protected variables
        # get initialized empty
        # later on set from config file
        # self._selectedModuleName    = None
        # self._allModulesNames    = None
        # self._rules                 = None
        # self._moods                 = None

        # self._maxTandaLength    = None
        # module run() interval in milliseconds
        # self._updtime       = None
        # self._moodTransition       = None
        # self._moodTransitionSpeed  = None
        # self._logging              = True
        # self._logPath              = None
        # self._loglevel              = None
        # not in use, kept for configfile
        # self.__showStatusbar        = None
        # self.applicationpath = getBeamHomePath()

        # load strings from strings.json
        stringsfilename = os.path.join(getBeamResourcesPath(), 'json', 'strings.json')
        self._beamStrings = BeamStrings(stringsfilename)

        # load dmx device definitions from dmxdevicedefs.json
        dmxdevdefsfilename = os.path.join(getBeamResourcesPath(), 'json', 'dmxdevicedefs.json')
        self._dmxDefinitions = DMXlibrary(dmxdevdefsfilename)

    def getString(self, key):
        return self._beamStrings.getString(key)
    def getDMXdeviceDict(self):
        return self._dmxDefinitions
    def getDMXdeviceList(self):
        return self._dmxDefinitions.getDeviceList()

    def getSelectedModuleName(self):
        return self._beamConfigData['Module']

    def setSelectedModuleName(self, moduleName):
        self._beamConfigData['Module'] = moduleName

    def getMoods(self):
        return self._beamConfigData['Moods']

    def getRules(self):
        return self._beamConfigData['Rules']

    def getMaxTandaLength(self):
        return self._beamConfigData['MaxTandaLength']
    def setMaxTandaLength(self, maxtandalength):
        self._beamConfigData['MaxTandaLength'] = maxtandalength

    def getUpdtime(self):
        return self._beamConfigData['Updtime']
    def setUpdtime(self, updtime):
        self._beamConfigData['Updtime'] = updtime

    def getMoodTransition(self):
        return self._beamConfigData['MoodTransition']
    def setMoodTransition(self, moodTransition):
        self._beamConfigData['MoodTransition'] = moodTransition

    def getMoodTransitionSpeed(self):
        return self._beamConfigData['MoodTransitionSpeed']
    def setMoodTransitionSpeed(self, moodTransition):
        self._beamConfigData['MoodTransitionSpeed'] = moodTransition

    def getLogging(self):
        return self._beamConfigData['Logging']
    def setLogging(self, logging):
        self._beamConfigData['Logging'] = logging

    def getLogPath(self):
        return self._beamConfigData['LogPath']
    def setLogPath(self, logPath):
        self._beamConfigData['LogPath'] = logPath

    def getLogLevel(self):
        return self._beamConfigData['LogLevel']
    def setLogLevel(self, loglevel):
        self._beamConfigData['LogLevel'] = loglevel

    def getShowStatusbar(self):
        return self._beamConfigData['ShowStatusbar']

    # def getDMXdeviceName(self):
    #     return self._dmxDefinitions.
    #
    # def setSelectedDMXdeviceName(self, deviceName):
    #     self._beamConfigData['DMXdevice'] = deviceName

    def getSelectedU1DMXdeviceName(self):
        return self._beamConfigData['U1_DMXdevice']

    def setSelectedU1DMXdeviceName(self, deviceName):
        self._beamConfigData['U1_DMXdevice'] = deviceName

    def getSelectedU2DMXdeviceName(self):
        return self._beamConfigData['U2_DMXdevice']

    def setSelectedU2DMXdeviceName(self, deviceName):
        self._beamConfigData['U2_DMXdevice'] = deviceName

    # def getDMXuniverse(self):
    #     return self._beamConfigData['DMXuniverse']
    #
    # def setdDMXuniverse(self, universe):
    #     self._beamConfigData['DMXuniverse'] = universe

    def getBeamConfigFilePath(self):
        configfilepath = os.path.join(getBeamConfigPath(), self.getString("configfilename"))

        return configfilepath

    def getDefaultConfigFilePath(self):
        defaultfilepath = os.path.join(getBeamHomePath(), 'resources', 'json', self.getString("configfilename"))

        return defaultfilepath


    def loadConfigData(self, configFileName):
        configFile = open(configFileName, 'r')
        try:
            configData = json.load(configFile)
        finally:
            configFile.close()

        return configData


    def dumpConfigData(self, configFileName, configData):

        beamconfigpath = getBeamConfigPath()
        if not os.path.isdir(beamconfigpath):
            logging.warning("BeamSettings.dumpConfigData(): '" + beamconfigpath + "' does not exist, creating it.")
            os.mkdir(beamconfigpath)

        if not os.path.isfile(configFileName):
            # if the file does not exist use default from beam home
            logging.info("BeamSettings.dumpConfigData(): configfile does not exist '" + configFileName + "'")

        configFile = open(configFileName, 'w')
        try:
            json.dump(configData, configFile, indent=2)
        finally:
            configFile.close()

        return

    def dumpConfig(self):

        '''
# replace by dump of _beamConfigData
# when access functions are implemented
        output = {}

        output['Configname']       = "Default Configuration"
        output['Comment']          = "This is a configuration file for Beam"
        output['Author']           = "Mikael Holber & Horia Uifaleanu - 2015"
        output['Module']           = self._selectedModuleName
        output['MaxTandaLength']   = self._maxTandaLength
        output['Updtime']          = self._updtime
        output['MoodTransition']           = self._moodTransition
        output['MoodTransitionSpeed']      = self._moodTransitionSpeed
        output['Logging']              = self._logging
        output['LogPath']              = self._logPath
        output['LogLevel']              = self._loglevel
        output['ShowStatusbar']        = self.__showStatusbar

        # Dictionaries
        output['AllModules']           = self._allModulesNames
        output['Rules']                = self._rules
        output['Moods']                = self._moods
                '''

        beamconfigfile = self.getBeamConfigFilePath()
        self.dumpConfigData(beamconfigfile, self._beamConfigData)
        logging.info("BeamSettings.dumpConfig(): configfile '" + beamconfigfile + "'")

        return


    #
    # Initializes protected variables by copying from ConfigData or DefaultConfigData
    #
    def __setConfigData(self, beamConfigData, defaultConfigData):

        self._beamConfigData = deepcopy(beamConfigData)
        # copies new properties and dicts from default config to beam config, but but not lists
        complementDict(defaultConfigData, self._beamConfigData)

        # take module names always from default config
        self._beamConfigData['AllModules'] = deepcopy(defaultConfigData['AllModules'])
        self._beamConfigData['DMX'] = deepcopy(defaultConfigData['DMX'])

        # self._allModulesNames    = self._beamConfigData['AllModules']
        # self._rules                 = self.__extractSetting(beamConfigData, defaultConfigData, 'Rules')
        # self._rules                 = self._beamConfigData['Rules']
        # self._moods                 = self.__extractSetting(beamConfigData, defaultConfigData, 'Moods')

        # add new properties from default mood to all moods
        defMood = defaultConfigData['Moods'][0]
        for idx in range(0, len(beamConfigData['Moods'])):
            idxMood = self._beamConfigData['Moods'][idx]
            complementDict(defMood, idxMood)
        # self._moods = self._beamConfigData['Moods']

# ??? complement rules?

        # Set OS-specific variables
        if platform.system() == 'Linux' or platform.system() == 'Darwin' :
            osModuleNames = self._beamConfigData['AllModules'][0]['Modules']
            osU1DMXdeviceName = self.getDMXdeviceList()
            osU2DMXdeviceName = self.getDMXdeviceList()
            self._preferencesSize = (500, 500)
            self._moodSize = (480,800)
        if platform.system() == 'Windows':
            osModuleNames = self._beamConfigData['AllModules'][1]['Modules']
            # osDMXdeviceNames = self._beamConfigData['DMX'][1]['Devices']
            osU1DMXdeviceName = self._beamConfigData['DMX'][1]['U1_Device']
            osU2DMXdeviceName = self._beamConfigData['DMX'][1]['U2_Device']
            self._preferencesSize = (500, 500)
            self._moodSize = (420,800)

        # module names available for this OS
        # self._moduleNames = [s for s in osModuleNames['Modules']]
        self._moduleNames = osModuleNames
        self._U1DMXdeviceName = osU1DMXdeviceName
        self._U2DMXdeviceName = osU2DMXdeviceName

        # set "internal" variables
# !!! replace by access functions
        # self._selectedModuleName = self._beamConfigData['Module']         # Player to read from
        if self.getSelectedModuleName() not in self._moduleNames:
            logging.warning("BeamSettings.__setConfigData(): selected module '" + self.getSelectedModuleName() + "' does not exist")
            self.setSelectedModuleName(self._moduleNames[0])

        if self.getSelectedU1DMXdeviceName() not in self._U1DMXdeviceName:
            logging.warning(
                "BeamSettings.__setConfigData(): selected DMX device '" + self.getSelectedU1DMXdeviceName() + "' does not exist")
            self.setSelectedU1DMXdeviceName(self._U1DMXdeviceName[0])

        if self.getSelectedU2DMXdeviceName() not in self._U2DMXdeviceName:
            logging.warning(
                "BeamSettings.__setConfigData(): selected DMX device '" + self.getSelectedU2DMXdeviceName() + "' does not exist")
            self.setSelectedU2DMXdeviceName(self._U2DMXdeviceName[0])

        # self._updtime               = self._beamConfigData['Updtime']        # mSec between reading
        # self._moodTransition        = self._beamConfigData['MoodTransition']
        # self._moodTransitionSpeed   = self._beamConfigData['MoodTransitionSpeed']
        # self.__showStatusbar         = self._beamConfigData['ShowStatusbar']
        # self._logging               = self._beamConfigData['Logging']
        # self._logPath               = self._beamConfigData['LogPath']
        if self.getLogPath() == '':
            self.setLogPath(getBeamConfigPath())
        # self._loglevel           = self._beamConfigData['LogLevel']


        return


    def loadConfig(self):
        # configfilename="beamconfig.json"

        beamconfigfilepath = self.getBeamConfigFilePath()
        if not os.path.isfile(beamconfigfilepath):
            # if there is no configfile yet
            logging.warning("BeamSettings.loadConfig(): configfile does not exist '" + beamconfigfilepath + "'")
            oldconfigfile = os.path.join(getUserHomePath(), "BeamConfig.json")
            if os.path.isfile(oldconfigfile):
                logging.warning("BeamSettings.loadConfig(): using configfile in old directory: '" + oldconfigfile + "'")
                beamconfigfilepath = oldconfigfile
            else:
                # beamconfigpath = getBeamHomePath()
                beamconfigfilepath = self.getDefaultConfigFilePath()
                logging.warning("BeamSettings.loadConfig(): loading default configfile '" + beamconfigfilepath + "'")
                # Use original configfile which is the settingsfile below
        beamConfigData = self.loadConfigData(beamconfigfilepath)

        # Also load the default configfile
        defaultconfigfile = os.path.join(getBeamResourcesPath(), "json", self.getString("configfilename"))
        defaultConfigData = self.loadConfigData(defaultconfigfile)

        # merges new properties from defaultConfigData into beamConfigData
        # and sets the instance properties
        self.__setConfigData(beamConfigData, defaultConfigData)

        return


#
# On start created as global object
# initialized on first import in beam.py
# and __init__  initializes protected stringResource variables
beamSettings = BeamSettings()
