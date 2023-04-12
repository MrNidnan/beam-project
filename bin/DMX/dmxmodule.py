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
from bin.beamutils import *
from copy import deepcopy

class DMXlibrary:

    def __init__(self, dmxdevdefsfilename):

        self._dmxdevDict = self.loadDMXdevDefinitions(dmxdevdefsfilename)

    def getDeviceList(self):
        return list(self._dmxdevDict.keys())

    def getDMXdeviceDict(self, dmxfixture):
         return self._dmxdevDict[dmxfixture]
    def loadDMXdevDefinitions(self, dmxdevdefsfilename):
        dmxdevdefsFile = open(dmxdevdefsfilename, 'r')
        try:
            dmxdevDict = json.load(dmxdevdefsFile)
        finally:
            dmxdevdefsFile.close()

        return dmxdevDict


class DMXdevice:

    def __init__(self, dmxfixture):

        dmxdevdefsfilename = os.path.join(getBeamResourcesPath(), 'json', 'dmxdevicedefs.json')
        self._dmxDefinitions = DMXlibrary(dmxdevdefsfilename)
        self.palette = deepcopy(self._dmxDefinitions.getDMXdeviceDict(dmxfixture)['Palette'])

        logging.debug("... Palette: " + str(self.palette))

    def GetPalette (self):
        return self.palette

    def GetPaletteList (self):
        return list(self.palette.keys())


    def GetPattern (self, patternkey):
        return list(self.palette[patternkey])

    def GetFixtureAddressOffset (self):
        return len(list(self.palette['None']))