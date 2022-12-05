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


import array


class DMXdevice:

    def __init__(self):
        #                             1    2    3    4    5    6    7    8    9   10   11   12
        self.palette = { 'None'   :[  0,   0,   0,   0,   0,   0,   0,   0, 255, 255, 255,  40],
                         'Red'    :[255,   0,   0,   0,   0,   0,   0,   0, 255, 255, 255,  40],
                         'Green'  :[  0, 255,   0,   0,   0,   0,   0,   0, 255, 255, 255,  40],
                         'Blue'   :[  0,   0, 255,   0,   0,   0,   0,   0, 255, 255, 255,  40],
                         'White'  :[  0,   0,   0, 255,   0,   0,   0,   0, 255, 255, 255,  40],
                         'Amber'  :[  0,   0,   0,   0, 255,   0,   0,   0, 255, 255, 255,  40],
                         'Black'  :[  0,   0,   0,   0,   0, 255,   0,   0, 255, 255, 255,  40],
                         'Sound1' :[  0,   0,   0,   0,   0,   0,   0, 255, 255, 255, 255,   0],
                         'Sound2' :[  0,   0,   0,   0,   0,   0,   0, 255, 128, 255, 255,   0],
                         'Auto0'  :[  0,   0,   0,   0,   0,   0,   0,  16,   0, 255, 255,   0],
                         'Auto1'  :[  0,   0,   0,   0,   0,   0,   0, 240, 128, 255, 255,   0],
                         'Auto2'  :[  0,   0,   0,   0,   0,   0,   0, 120, 255, 255, 255,   0],
                         'Strobe' :[  0,   0,   0, 255,   0,   0,   0,   0, 255,  95, 255,   0],
                       }
        self.universe = 1

    def GetUniverse (self):
        return self.universe

    def GetPalette (self):
        return self.palette

    def GetPaletteList (self):
        return list(self.palette.keys())


