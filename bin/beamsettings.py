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
    beamversion = ''

###############################################################
#
# Init
#
###############################################################
    def __init__(self):
        # protected variables
        # get initialized empty
        # later on set from config file
        self._moduleSelected    = ''
        self._maxTandaLength    = 4
        self._updateTimer       = 5000
        self._moodTransition       = ''
        self._moodTransitionSpeed  = ''
        self._logging              = True
        self._logPath              = ''
        self._loglevel              = "Debug"
        self._showStatusbar        = ''
        self._allModulesSettings    = ''
        self._rules                 = ''
        self._configversion = ''

        # self.applicationpath = getBeamHomePath()
        stringsfile = os.path.join(getBeamResourcesPath(), 'json', 'strings.json')
        # Linux ./resources/text/strings.json
        # Windows .\resources\text\strings.json
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
        self.beamversion = self.stringResources["version"]


    def loadConfig(self):
        # configfilename="beamconfig.json"

        try:
            beamconfigfile = os.path.join(getBeamConfigPath(), self.configfilename)
            if not os.path.isfile(beamconfigfile):
                # if there is no configfile yet
                logging.warning("BeamSettings.loadConfig(): configfile does not exist '" + beamconfigfile + "'")
                oldconfigfile = os.path.join(getUserHomePath(), "BeamConfig.json")
                if os.path.isfile(oldconfigfile):
                    logging.warning("BeamSettings.loadConfig(): using configfile in old directory: '" + oldconfigfile + "'")
                    beamconfigfile = oldconfigfile
                else:
                    # beamconfigpath = getBeamHomePath()
                    beamconfigfile = os.path.join(getBeamResourcesPath(), "json", self.configfilename)
                    logging.warning("BeamSettings.loadConfig(): loading default configfile '" + beamconfigfile + "'")
                    # Use original configfile which is the settingsfile below
            beamConfigData = self.loadConfigFile(beamconfigfile)

            # Also load the default configfile
            defaultconfigfile = os.path.join(getBeamResourcesPath(), "json", self.configfilename)
            defaultConfigData = self.loadConfigFile(defaultconfigfile)

            # beamconfigversion = beamConfigData['ConfigVersion'];
            # defaultconfigversion = defaultConfigData['ConfigVersion']
            # ??? readConfig() handles this
            # if beamconfigversion != defaultconfigversion:
                # merge the dictionaries
                # logging.error("Default configfile version '" + defaultconfigversion +
                #              "' differs from '" + beamconfigversion + "' in '" + beamconfigfile + "'")

            # merges new properties from defaultConfigData into beamConfigData
            self.readConfig(beamConfigData, defaultConfigData)
        except Exception as e:
            logging.error(e, exc_info=True)

        return


    def loadConfigFile(self, inputconfigfile):

        ConfigFile = open(inputconfigfile, 'r')
        try:
            ConfigData = json.load(ConfigFile)
            # Validate configfile version against string.txt version

            # Added since V0.4
            # But however, modules are always teken from default config
            # if len(ConfigData['AllModules'][0]['Modules']) == 5: # System: Linux
            #     ConfigData['AllModules'][0]['Modules'].append('Mixxx')
            # if len(ConfigData['AllModules'][0]['Modules']) == 6: # System: Windows
            #     ConfigData['AllModules'][0]['Modules'].append('Icecast')

            # if len(ConfigData['AllModules'][1]['Modules']) == 5: # System: Windows
            #     ConfigData['AllModules'][1]['Modules'].append('Mixxx')
            # if len(ConfigData['AllModules'][1]['Modules']) == 6: # System: Windows
            #     ConfigData['AllModules'][1]['Modules'].append('Icecast')

            # if len(ConfigData['AllModules'][2]['Modules']) == 6: # System: Mac
            #     ConfigData['AllModules'][2]['Modules'].append('Mixxx')
            # if len(ConfigData['AllModules'][2]['Modules']) == 7: # System: Windows
            #     ConfigData['AllModules'][2]['Modules'].append('Icecast')
        except Exception as e:
            logging.error(e, exc_info=True)
        finally:
            ConfigFile.close()

        return ConfigData



    #
    # Initializes protected variables by copying from ConfigData or ConfigDataOriginal
    #
    def readConfig(self, beamConfigData, defaultConfigData):

        # save ConfigVersion from default which is final
        configversion = defaultConfigData['ConfigVersion']
        # copies values and dicts from beam to default config, but not lists
        mergeDict(beamConfigData, defaultConfigData)
        # restore ConfigVersion
        defaultConfigData['ConfigVersion'] = configversion

        self._configversion         = defaultConfigData['ConfigVersion']
        self._moduleSelected        = defaultConfigData['Module']         # Player to read from
        self._maxTandaLength        = defaultConfigData['MaxTandaLength'] # Longest tandas, optimize for performance
        self._updateTimer           = defaultConfigData['Updtime']        # mSec between reading
        self._moodTransition        = defaultConfigData['MoodTransition']
        self._moodTransitionSpeed   = defaultConfigData['MoodTransitionSpeed']
        self._showStatusbar         = defaultConfigData['ShowStatusbar']
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
        # self._rules                 = self.extractSetting(beamConfigData, defaultConfigData, 'Rules')
        self._rules                 = beamConfigData['Rules']
        # self._moods                 = self.extractSetting(beamConfigData, defaultConfigData, 'Moods')
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

    #
    # Returns the value of ConfigData
    # and if that does not exist
    # replaced by the value of ConfigDataOriginal
    #
    def extractSetting(self, beamConfigData, defaultConfigData, key):
        try:
            output = beamConfigData[key]
        except:
            output = defaultConfigData[key]
        return output


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
            output['ConfigVersion']        = self._configversion

            # Dictionaries
            output['AllModules']           = self._allModulesSettings
            output['Rules']                = self._rules
            output['Moods']                = self._moods

            beamconfigpath = getBeamConfigPath()
            # Write config file to user ~/.beamconfig/
            beamconfigfile = os.path.join(beamconfigpath, self.configfilename)
            self.dumpConfigFile(beamconfigfile, output)
            logging.info("BeamSettings.saveConfig(): configfile '" + beamconfigfile + "'")
        except Exception as e:
            logging.error(e, exc_info=True)

        return


    def dumpConfigFile(self, outputConfigFile, output):

        beamconfigpath = getBeamConfigPath()
        if not os.path.isdir(beamconfigpath):
            logging.warning("BeamSettings.dumpConfigFile(): '" + beamconfigpath + "' does not exist, creating it.")
            os.mkdir(beamconfigpath)

        if not os.path.isfile(outputConfigFile):
            # if the file does not exist use default from beam home
            logging.info("BeamSettings.dumpConfigFile(): configfile does not exist '" + outputConfigFile + "'")

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
