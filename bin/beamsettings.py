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
import sys, os


###############################################################
#
# BeamSettings
#
###############################################################
from bin.beamutils import getBeamHomePath, getBeamConfigPath


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

    # public variables, initialized empty
    # on fist import from beam.py

    # then __init__ gets called from the global beamSettings
    # and variables read from string ressources

    # then read from configfile
    configfilename = ''
    logfilename = ''
    loglevel = ''
    mainframetitle = ''
    aboutdialogdescription = ''
    aboutdialoglicense = ''
    aboutcopyright = ''
    aboutwebsite = ''
    aboutdeveloper = ''
    aboutartist = ''
    beamVersion = ''

###############################################################
#
# Init
#
###############################################################
    def __init__(self):
        # protected variables
        # get initialized empty
        self._moduleSelected    = ''
        self._maxTandaLength    = ''
        self._updateTimer       = ''
        self._moodTransition       = ''
        self._moodTransitionSpeed  = ''
        self._logging              = ''
        self._logPath              = ''
        self._loglevel              = ''
        self._showStatusbar        = ''
        self._allModulesSettings    = ''
        self._rules                 = ''
        self._beamVersion = BeamSettings.beamVersion

        self.applicationpath = getBeamHomePath()
        stringsfile = os.path.join(self.applicationpath, 'resources', 'text', 'strings.txt')
        # Linux ./resources/text/strings.txt
        # Windows .\resources\text\strings.txt
        # strings resources in simple JSON format
        self.stringResources = json.load(open(stringsfile, "r"))

        # fill public virables from string ressources
        self.configfilename = self.stringResources["defaultconfigfilename"]
        self.logfilename = self.stringResources["defaultlogfilename"]
        self.loglevel = self.stringResources["defaultloglevel"]
        self.mainframetitle = self.stringResources["mainframetitle"]
        self.aboutdialogdescription = self.stringResources["aboutdialogdescription"]
        self.aboutdialoglicense = self.stringResources["aboutdialoglicense"]
        self.aboutcopyright = self.stringResources["aboutcopyright"]
        self.aboutwebsite = self.stringResources["aboutwebsite"]
        self.aboutdeveloper = self.stringResources["aboutdeveloper"]
        self.aboutartist = self.stringResources["aboutartist"]
        self.beamVersion = self.stringResources["version"]


    ###############################################################
    #
    # LOAD Config
    #
    ###############################################################
    def loadConfig(self):
        # configfilename="BeamConfig.json"

        try:
            beamconfigfile = os.path.join(getBeamConfigPath(), self.configfilename)
            if not os.path.isfile(beamconfigfile):
                # if the file does not exist use default from beam home
                logging.warning("BeamSettings.loadConfig(): configfile does not exist '" + beamconfigfile + "'")
                beamconfigpath = getBeamHomePath()
                beamconfigfile = os.path.join(beamconfigpath, self.configfilename)
                logging.warning("BeamSettings.loadConfig(): loading default configfile '" + beamconfigfile + "'")
                # Use original configfile which is the settingsfile below
            ConfigData = self.openSetting(beamconfigfile)

            # Also load the original settingsfile from Home into Original
            beamconfigpath = getBeamHomePath()
            beamconfigfile = os.path.join(beamconfigpath, self.configfilename)
            ConfigDataOriginal = self.openSetting(beamconfigfile)
            # ???
            self.readConfig(ConfigData, ConfigDataOriginal)
        except Exception as e:
            logging.error(e)

        return

    # Initializes protected variables by copying from ConfigData or ConfigDataOriginal
    def readConfig(self, ConfigData, ConfigDataOriginal):
        self._moduleSelected        = self.extractSetting(ConfigData, ConfigDataOriginal, 'Module')         # Player to read from
        self._maxTandaLength        = self.extractSetting(ConfigData, ConfigDataOriginal, 'MaxTandaLength') # Longest tandas, optimize for performance
        self._updateTimer           = self.extractSetting(ConfigData, ConfigDataOriginal, 'Updtime')        # mSec between reading
        self._moodTransition        = self.extractSetting(ConfigData, ConfigDataOriginal, 'MoodTransition')
        self._moodTransitionSpeed   = self.extractSetting(ConfigData, ConfigDataOriginal, 'MoodTransitionSpeed')
        self._showStatusbar         = self.extractSetting(ConfigData, ConfigDataOriginal, 'ShowStatusbar')
        self._logging               = self.extractSetting(ConfigData, ConfigDataOriginal, 'Logging')
        self._logPath               = self.extractSetting(ConfigData, ConfigDataOriginal, 'LogPath')
        if self._logPath == '':
            self._logPath = os.path.join(getBeamConfigPath())
        # plus self.logfilename
        self._loglevel              = self.extractSetting(ConfigData, ConfigDataOriginal, 'LogLevel')
        if self._loglevel == '':
            logging.error("BeamConfig.readConfig(): _loglevel is empty")
            self._loglevel = "Warning"

        # Dictionaries
        self._allModulesSettings        = ConfigDataOriginal['AllModules']
        self._rules                     = self.extractSetting(ConfigData, ConfigDataOriginal, 'Rules')
        self._moods                     = self.extractSetting(ConfigData, ConfigDataOriginal, 'Moods')

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
    def extractSetting(self, ConfigData, ConfigDataOriginal, key):
        try:
            output = ConfigData[key]
        except:
            output = ConfigDataOriginal[key]
        return output


    def openSetting(self, inputconfigfile):

        ConfigFile = open(inputconfigfile, 'r')
        try:
            ConfigData = json.load(ConfigFile)
            # Validate configfile version against string.txt version

            # Added since V0.4
            if len(ConfigData['AllModules'][0]['Modules']) == 5: # System: Linux
                ConfigData['AllModules'][0]['Modules'].append('Mixxx')
            if len(ConfigData['AllModules'][0]['Modules']) == 6: # System: Windows
                ConfigData['AllModules'][0]['Modules'].append('Icecast')

            if len(ConfigData['AllModules'][1]['Modules']) == 5: # System: Windows
                ConfigData['AllModules'][1]['Modules'].append('Mixxx')
            if len(ConfigData['AllModules'][1]['Modules']) == 6: # System: Windows
                ConfigData['AllModules'][1]['Modules'].append('Icecast')

            if len(ConfigData['AllModules'][2]['Modules']) == 6: # System: Mac
                ConfigData['AllModules'][2]['Modules'].append('Mixxx')
            if len(ConfigData['AllModules'][2]['Modules']) == 7: # System: Windows
                ConfigData['AllModules'][2]['Modules'].append('Icecast')

            # Funktioniert so nicht, muss gegen Default verglichen werden
            # if not ConfigData['ConfigVersion'] == self._beamVersion:
                # logging.warning("Configfile version " + ConfigData['ConfigVersion'] + " differs from current " + self._beamVersion )
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
    def saveConfig(self, outputfilename):
        try:
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
            output['LogLevel']              = self._loglevel
            output['ShowStatusbar']        = self._showStatusbar
            output['ConfigVersion']        = self._beamVersion

            # Dictionaries
            output['AllModules']           = self._allModulesSettings
            output['Rules']                = self._rules
            output['Moods']                = self._moods

            beamconfigpath = getBeamConfigPath()
            if not os.path.isdir(beamconfigpath):
                logging.warning("BeamSettings.safeConfig(): '" + beamconfigpath + "' does not exist, creating it.")
                os.mkdir(beamconfigpath)

            # Write config file to user ~/.beamconfig/
            beamconfigfile = os.path.join(beamconfigpath, self.configfilename)
            self.writeSetting(beamconfigfile, output)
            logging.info("BeamSettings.saveConfig(): configfile '" + beamconfigfile + "'")
        except Exception as e:
            logging.error(e)

        return


    def writeSetting(self, outputConfigFile, output):

        beamconfigpath = getBeamConfigPath()
        if not os.path.isdir(beamconfigpath):
            logging.warning("BeamSettings.writeSetting(): '" + beamconfigpath + "' does not exist, creating it.")
            os.mkdir(beamconfigpath)

        if not os.path.isfile(outputConfigFile):
            # if the file does not exist use default from beam home
            logging.info("BeamSettings.writeSetting(): configfile does not exist '" + outputConfigFile + "'")

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
