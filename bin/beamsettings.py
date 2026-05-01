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
from bin.beamutils import complementDict, getBeamConfigPath, getBeamHomePath, getBeamResourcesPath
from bin.beamstrings import BeamStrings
from bin.profilesettings import ProfileSettingsStore
from bin.DMX.dmxmodule import DMXlibrary, Universe
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
        # load strings from strings.json
        stringsfilename = os.path.join(getBeamResourcesPath(), 'json', 'strings.json')
        self._beamStrings = BeamStrings(stringsfilename)

        # load dmx device definitions from dmxdevicedefs.json
        dmxdevdefsfilename = os.path.join(getBeamResourcesPath(), 'json', 'dmxdevicedefs.json')
        self._dmxDefinitions = DMXlibrary(dmxdevdefsfilename)
        self._profileSettings = ProfileSettingsStore(
            self.getString("configfilename"),
            self.getDefaultConfigFilePath,
            self.getBeamConfigFilePath,
            self.loadConfigData,
            self.dumpConfigData,
        )
        self._isDirty = False
        self._suspendDirtyTracking = False

    def _markDirty(self):
        if not self._suspendDirtyTracking:
            self._isDirty = True

    def markDirty(self):
        self._markDirty()

    def clearDirty(self):
        self._isDirty = False

    def isDirty(self):
        return self._isDirty

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
        self._markDirty()

    def getMoods(self):
        return self._beamConfigData['Moods']

    def getRules(self):
        return self._beamConfigData['Rules']

    def getMaxTandaLength(self):
        return self._beamConfigData['MaxTandaLength']
    def setMaxTandaLength(self, maxtandalength):
        self._beamConfigData['MaxTandaLength'] = maxtandalength
        self._markDirty()

    def getUpdtime(self):
        return self._beamConfigData['Updtime']
    def setUpdtime(self, updtime):
        self._beamConfigData['Updtime'] = updtime
        self._markDirty()

    def getMoodTransition(self):
        return self._beamConfigData['MoodTransition']
    def setMoodTransition(self, moodTransition):
        self._beamConfigData['MoodTransition'] = moodTransition
        self._markDirty()

    def getMoodTransitionSpeed(self):
        return self._beamConfigData['MoodTransitionSpeed']
    def setMoodTransitionSpeed(self, moodTransition):
        self._beamConfigData['MoodTransitionSpeed'] = moodTransition
        self._markDirty()

    def getLogging(self):
        return self._beamConfigData['Logging']
    def setLogging(self, logging):
        self._beamConfigData['Logging'] = logging
        self._markDirty()

    def getLogPath(self):
        return self._beamConfigData['LogPath']
    def setLogPath(self, logPath):
        self._beamConfigData['LogPath'] = logPath
        self._markDirty()

    def getLogLevel(self):
        return self._beamConfigData['LogLevel']
    def setLogLevel(self, loglevel):
        self._beamConfigData['LogLevel'] = loglevel
        self._markDirty()

    def getShowStatusbar(self):
        return self._beamConfigData['ShowStatusbar']

    def getNetworkService(self):
        return self._beamConfigData['NetworkService']

    def getNetworkServiceEnabled(self):
        return str(self.getNetworkService().get('Enabled', 'False')).lower() == 'true'

    def setNetworkServiceEnabled(self, enabled):
        self.getNetworkService()['Enabled'] = 'True' if enabled else 'False'
        self._markDirty()

    def getNetworkServiceHost(self):
        return str(self.getNetworkService().get('Host', '0.0.0.0'))

    def setNetworkServiceHost(self, host):
        normalized_host = str(host).strip()
        if normalized_host == '':
            normalized_host = '0.0.0.0'
        self.getNetworkService()['Host'] = normalized_host
        self._markDirty()

    def getNetworkServicePort(self):
        return int(self.getNetworkService().get('Port', 8765))

    def setNetworkServicePort(self, port):
        self.getNetworkService()['Port'] = int(port)
        self._markDirty()

    def getNetworkServiceWebRoot(self):
        return self.getNetworkService().get('WebRoot', os.path.join('resources', 'web', 'tablet'))

    def getFoobar2000(self):
        return self._beamConfigData['Foobar2000']

    def getVirtualDJ(self):
        return self._beamConfigData['VirtualDJ']

    def getVirtualDJHost(self):
        return str(self.getVirtualDJ().get('Host', '127.0.0.1')).strip()

    def setVirtualDJHost(self, host):
        normalized_host = str(host).strip()
        if normalized_host == '':
            normalized_host = '127.0.0.1'
        self.getVirtualDJ()['Host'] = normalized_host
        self._markDirty()

    def getVirtualDJPort(self):
        return int(self.getVirtualDJ().get('Port', 80))

    def setVirtualDJPort(self, port):
        self.getVirtualDJ()['Port'] = int(port)
        self._markDirty()

    def getVirtualDJBearerToken(self):
        return str(self.getVirtualDJ().get('BearerToken', ''))

    def setVirtualDJBearerToken(self, token):
        self.getVirtualDJ()['BearerToken'] = str(token)
        self._markDirty()

    def getVirtualDJQueryMode(self):
        query_mode = str(self.getVirtualDJ().get('QueryMode', 'Master')).strip()
        if query_mode == '':
            query_mode = 'Master'
        return query_mode

    def setVirtualDJQueryMode(self, query_mode):
        normalized_query_mode = str(query_mode).strip()
        if normalized_query_mode == '':
            normalized_query_mode = 'Master'
        self.getVirtualDJ()['QueryMode'] = normalized_query_mode
        self._markDirty()

    def getFoobarBeefwebUrl(self):
        return str(self.getFoobar2000().get('BeefwebUrl', 'http://localhost:8880/')).strip()

    def setFoobarBeefwebUrl(self, url):
        normalized_url = str(url).strip()
        if normalized_url == '':
            normalized_url = 'http://localhost:8880/'
        self.getFoobar2000()['BeefwebUrl'] = normalized_url
        self._markDirty()

    def getFoobarBeefwebUser(self):
        return str(self.getFoobar2000().get('BeefwebUser', ''))

    def setFoobarBeefwebUser(self, user):
        self.getFoobar2000()['BeefwebUser'] = str(user)
        self._markDirty()

    def getFoobarBeefwebPassword(self):
        return str(self.getFoobar2000().get('BeefwebPassword', ''))

    def setFoobarBeefwebPassword(self, password):
        self.getFoobar2000()['BeefwebPassword'] = str(password)
        self._markDirty()

    def getSelectedU1DMXdeviceName(self):
        return self._beamConfigData.get('U1_DMXdevice', 'None')

    def setSelectedU1DMXdeviceName(self, deviceName):
        self._beamConfigData['U1_DMXdevice'] = deviceName
        self._markDirty()

    def getSelectedU2DMXdeviceName(self):
        return self._beamConfigData.get('U2_DMXdevice', 'None')

    def setSelectedU2DMXdeviceName(self, deviceName):
        self._beamConfigData['U2_DMXdevice'] = deviceName
        self._markDirty()

    def getDMXuniverse1(self):
        uv1 = Universe()
        try:
            flist = self._beamConfigData['DMXuniverse1']
            logging.debug("... DMXuniverse1: " + str(flist))
            for f in flist:
                uv1.AddFixture(f)
        except:
            f = self._beamConfigData['U1_DMXdevice']
            logging.debug("... U1_DMXdevice: " + str(f))
            uv1.AddFixture(f)
            self.setDMXuniverse1(uv1)
        return uv1

    def setDMXuniverse1(self, u1):
        self._beamConfigData['DMXuniverse1'] = u1.FixtureNames()
        if len(u1.FixtureNames()) == 0 :
            self.setSelectedU1DMXdeviceName('NONE')
        else:
            self.setSelectedU1DMXdeviceName(u1.FixtureNames()[0])
        self._markDirty()
    def getDMXuniverse2(self):
        uv2 = Universe()
        try:
            flist = self._beamConfigData['DMXuniverse2']
            logging.debug("... DMXuniverse2: " + str(flist))
            for f in flist:
                uv2.AddFixture(f)
        except:
            f = self._beamConfigData['U2_DMXdevice']
            logging.debug("... U2_DMXdevice: " + str(f))
            uv2.AddFixture(f)
            self.setDMXuniverse2(uv2)
        return uv2

    def setDMXuniverse2(self, u2):
        self._beamConfigData['DMXuniverse2'] = u2.FixtureNames()
        if len(u2.FixtureNames()) == 0:
            self.setSelectedU2DMXdeviceName('NONE')
        else:
            self.setSelectedU2DMXdeviceName(u2.FixtureNames()[0])
        self._markDirty()

    def getBeamConfigFilePath(self):
        configfilepath = os.path.join(getBeamConfigPath(), self.getString("configfilename"))

        return configfilepath

    def getProfiles(self):
        return self._profileSettings.getProfiles()

    def getActiveProfileId(self):
        return self._profileSettings.getActiveProfileId()

    def getActiveProfileName(self):
        return self._profileSettings.getActiveProfileName()

    def hasActiveProfileBeenPersisted(self):
        return self._profileSettings.hasActiveProfileBeenPersisted()

    def getDefaultConfigFilePath(self):
        defaultfilepath = os.path.join(getBeamHomePath(), 'resources', 'json', self.getString("configfilename"))

        return defaultfilepath


    def loadConfigData(self, configFileName):
        with open(configFileName, 'r', encoding='utf-8') as configFile:
            return json.load(configFile)


    def dumpConfigData(self, configFileName, configData):

        beamconfigpath = getBeamConfigPath()
        if not os.path.isdir(beamconfigpath):
            logging.warning("BeamSettings.dumpConfigData(): '" + beamconfigpath + "' does not exist, creating it.")
            os.mkdir(beamconfigpath)

        if not os.path.isfile(configFileName):
            # if the file does not exist use default from beam home
            logging.info("BeamSettings.dumpConfigData(): configfile does not exist '" + configFileName + "'")

        with open(configFileName, 'w', encoding='utf-8') as configFile:
            json.dump(configData, configFile, indent=2, ensure_ascii=False)

        return

    def dumpConfig(self):
        self.saveActiveProfile()
        logging.info("BeamSettings.dumpConfig(): saved active profile '%s'", self.getActiveProfileId())

        return

    def loadProfiles(self):
        beamConfigData, defaultConfigData = self._profileSettings.loadProfiles()
        self.__setConfigData(beamConfigData, defaultConfigData)

        return

    def saveProfiles(self):
        self._profileSettings.saveProfiles()

    def saveActiveProfile(self):
        self._profileSettings.saveActiveProfile(self._beamConfigData)
        self.clearDirty()

    def saveActiveProfileAs(self, profileId):
        self._profileSettings.saveActiveProfileAs(profileId, self._beamConfigData)
        self.clearDirty()

    def switchProfile(self, profileId):
        beamConfigData, defaultConfigData = self._profileSettings.switchProfile(profileId)
        if beamConfigData is None:
            return
        self.__setConfigData(beamConfigData, defaultConfigData)

    def createProfile(self, name, source='current'):
        profile, configData, defaultConfigData = self._profileSettings.createProfile(name, self._beamConfigData, source)
        self.__setConfigData(configData, defaultConfigData)
        return deepcopy(profile)

    def renameProfile(self, profileId, newName):
        self._profileSettings.renameProfile(profileId, newName)

    def deleteProfile(self, profileId):
        beamConfigData, defaultConfigData = self._profileSettings.deleteProfile(profileId)
        if beamConfigData is not None:
            self.__setConfigData(beamConfigData, defaultConfigData)


    #
    # Initializes protected variables by copying from ConfigData or DefaultConfigData
    #
    def __setConfigData(self, beamConfigData, defaultConfigData):
        self._suspendDirtyTracking = True
        try:
            self._beamConfigData = deepcopy(beamConfigData)
            # Copy new properties and dicts from defaults without overwriting user lists.
            complementDict(defaultConfigData, self._beamConfigData)

            # take module names always from default config
            self._beamConfigData['AllModules'] = deepcopy(defaultConfigData['AllModules'])
            self._beamConfigData['DMX'] = deepcopy(defaultConfigData['DMX'])

            # add new properties from default mood to all moods
            defMood = defaultConfigData['Moods'][0]
            for idx in range(0, len(beamConfigData['Moods'])):
                idxMood = self._beamConfigData['Moods'][idx]
                complementDict(defMood, idxMood)

            has_trim_title_rule = False
            for rule in self._beamConfigData['Rules']:
                if rule.get('Type') == 'Trim () in Title':
                    has_trim_title_rule = True
                    if 'Field1' not in rule:
                        rule['Field1'] = '%Title'

            if not has_trim_title_rule:
                self._beamConfigData['Rules'].append({
                    'Active': 'no',
                    'Field1': '%Title',
                    'Type': 'Trim () in Title',
                })

            # Set OS-specific variables
            if platform.system() == 'Linux' or platform.system() == 'Darwin' :
                osIdx = 2
                if platform.system() == 'Linux': osIdx = 0
                osModuleNames = self._beamConfigData['AllModules'][osIdx]['Modules']
                osU1DMXdeviceName = self.getDMXdeviceList()
                osU2DMXdeviceName = self.getDMXdeviceList()
                self._preferencesSize = (500, 500)
                self._moodSize = (480,800)
            if platform.system() == 'Windows':
                osModuleNames = self._beamConfigData['AllModules'][1]['Modules']
                osU1DMXdeviceName = self._beamConfigData['DMX'][1]['U1_Device']
                osU2DMXdeviceName = self._beamConfigData['DMX'][1]['U2_Device']
                self._preferencesSize = (500, 500)
                self._moodSize = (420,800)

            self._moduleNames = osModuleNames
            self._U1DMXdeviceName = osU1DMXdeviceName
            self._U2DMXdeviceName = osU2DMXdeviceName
            self._Universe1 = self.getDMXuniverse1()
            self._Universe2 = self.getDMXuniverse2()

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

            if self.getLogPath() == '':
                self.setLogPath(getBeamConfigPath())
            self._oladIsRunning = 0
        finally:
            self._suspendDirtyTracking = False

        self.clearDirty()
        return


    def loadConfig(self):
        self.loadProfiles()

        return


#
# On start created as global object
# initialized on first import in beam.py
# and __init__  initializes protected stringResource variables
beamSettings = BeamSettings()
