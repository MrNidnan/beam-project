#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    Copyright (C) 2022 Piotr R. Sidorowicz http://http://www.beam-project.com
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


import os
import json
import logging
from bin.beamutils import getBeamResourcesPath, getBeamConfigPath
from copy import deepcopy

class DMXlibrary:

    def __init__(self, dmxdevdefsfilename, dmxdevcustfilename):
        self._dmxdefaultfilename = dmxdevdefsfilename
        self._dmxcustomfilename = dmxdevcustfilename
        self._dmxdevDict = self.loadDMXdevDefinitions()

    def getDictionary(self):
        return self._dmxdevDict

    def getDeviceList(self):
        return list(self._dmxdevDict.keys())

    def getDMXdeviceDict(self, dmxfixture):
        if '' == dmxfixture: dmxfixture = 'None'
        return self._dmxdevDict[dmxfixture]

    def loadDMXdevDefinitions(self):
        if os.path.isfile(self._dmxcustomfilename):
            dmxdevfilename = self._dmxcustomfilename
        else:
            dmxdevfilename = self._dmxdefaultfilename

        dmxdevdefsFile = open(dmxdevfilename, 'r', encoding='utf-8')
        try:
            dmxdevDict = json.load(dmxdevdefsFile)
        finally:
            dmxdevdefsFile.close()

        return dmxdevDict

    def addDeviceToLibrary(self, newdmxfixture, newpalette):
        self._dmxdevDict[newdmxfixture] = newpalette
        with open(self._dmxcustomfilename, "w", encoding="utf-8") as dmxdevdefsFile:
            try:
                json.dump(self._dmxdevDict, dmxdevdefsFile, indent=4)
            finally:
                dmxdevdefsFile.close()

    def delDeviceFromLibrary(self, dmxfixture):
        self._dmxdevDict.pop(dmxfixture)
        with open(self._dmxcustomfilename, "w", encoding="utf-8") as dmxdevdefsFile:
            try:
                json.dump(self._dmxdevDict, dmxdevdefsFile, indent=4)
            finally:
                dmxdevdefsFile.close()

    def libraryIsModified(self):
        return os.path.isfile(self._dmxcustomfilename)

    def restoreDefaultLibrary(self):
        os.remove(self._dmxcustomfilename)
        self._dmxdevDict = self.loadDMXdevDefinitions()

class DMXdevice:

    def __init__(self, dmxfixture):

        dmxdevdefsfilename = os.path.join(getBeamResourcesPath(), 'json', 'dmxdevicedefs.json')
        dmxdevcustfilename = os.path.join(getBeamConfigPath(), 'dmxdevicedefs.json')

        self._dmxDefinitions = DMXlibrary(dmxdevdefsfilename, dmxdevcustfilename )
        #self._dmxDefinitions = dmxdictionary

        if '' == dmxfixture: dmxfixture = 'None'
        self.palette = deepcopy(self._dmxDefinitions.getDMXdeviceDict(dmxfixture)['Palette'])
        self.name = dmxfixture
        self.colour = 'None'
        logging.debug("... Palette: " + str(self.palette))

    def GetPalette (self):
        return self.palette

    def GetPaletteList (self):
        return list(self.palette.keys())

    def SetColour (self, patternkey):
        self.colour = patternkey
    def GetCurrentColour (self):
        return self.colour
    def GetCurrentPattern (self):
        return list(self.palette[self.colour])

    def GetPattern (self, patternkey):
        return list(self.palette[patternkey])

    def GetFixtureAddressOffset (self):
        return len(list(self.palette['None']))

class Universe:
    def __init__(self):
        self.fixturelist = [] # names of devices

    def AddFixture (self, dmxfixture):
        if '' == dmxfixture: dmxfixture = 'None'
        self.fixturelist.append(DMXdevice(dmxfixture))

    def DelFixture (self, fixtureidx):
        if 0 < self.FixtureCount():
            self.fixturelist.pop(fixtureidx)

    def FixtureCount (self):
        return len(self.fixturelist)

    def FixtureAddresses (self):
        addrlist = []
        currentaddr = 1
        for fixture in self.fixturelist:
            addrlist.append(str(currentaddr))
            currentaddr += fixture.GetFixtureAddressOffset()
            #currentaddr += 1
            logging.debug("... currentaddr: " + str(currentaddr))
        return addrlist

    def FixtureNames (self):
        list = []
        for fixture in self.fixturelist:
            list.append(fixture.name)
        return list

    def FixtureColours (self):
        list = []
        for fixture in self.fixturelist:
            list.append(fixture.colour)
        return list
    def setFixtureColours (self, colour, indices):
        logging.debug("... desired indices: " + str(indices))
        logging.debug("... desired colour: " + str(colour))
        for idx, fixture in enumerate(self.fixturelist):
            if (idx in indices): fixture.SetColour(colour)
            logging.debug("... new colour: " + str(fixture.colour))

    def setAllFixtureColours (self, colourlist):
        logging.debug("... desired colour list: " + str(colourlist))
        clrlstlength = len(colourlist)
        logging.debug("... desired colour list length: " + str(clrlstlength))
        lastcolour = 'None'
        for idx, fixture in enumerate(self.fixturelist):
            if idx < clrlstlength :
                lastcolour = colourlist[idx]
            fixture.SetColour(lastcolour)
            logging.debug("... new colour: ("+str(idx)+") " + str(fixture.colour))


    def FixturePatterns (self):
        pattern = []
        for fixture in self.fixturelist:
            pattern += fixture.GetPattern(fixture.colour)
        return pattern