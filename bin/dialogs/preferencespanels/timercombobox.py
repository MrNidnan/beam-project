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
#    XX/XX/2014 Version 1.0
#       - Initial release
#
# This Python file uses the following encoding: utf-8

import wx

class TimerComboBox(wx.ComboBox):
    def __init__(self, parent):
        wx.ComboBox.__init__(self, parent=parent,
                          choices=['Every 15 seconds','Every 30 seconds', 'Every 1 minute', 'Every 2 minutes',
                                   'Every 3 minutes', 'Every 5 minutes','Every 10 minutes','Every 20 minutes'],
                          style=wx.CB_READONLY)

    def setTimeSelection(self, value):
        if value == 15:
            self.SetSelection(0)
        elif value == 30:
            self.SetSelection(1)
        elif value == 60:
            self.SetSelection(2)
        elif value == 120:
            self.SetSelection(3)
        elif value == 180:
            self.SetSelection(4)
        elif value == 300:
            self.SetSelection(5)
        elif value == 600:
            self.SetSelection(6)
        elif value == 1200:
            self.SetSelection(7)
        else:
            self.SetSelection(2)

    def getTimeSelection(self):
        timerVector = [15, 30, 60, 120, 180, 300, 600, 1200]
        index = int(self.GetSelection())
        value = timerVector[index]
        return value