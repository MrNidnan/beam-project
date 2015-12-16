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

import wx, os
from bin.dialogs.editruledialog import EditRuleDialog

########################################################
#                      Rules                           #
########################################################
class Rules(wx.Panel):
    def __init__(self, parent, BeamSettings):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
        
        #############
        # VARIABLES #
        #############
        self.BeamSettings = BeamSettings
        self.parent = parent
        self.DisplayRows = []
        font = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD)