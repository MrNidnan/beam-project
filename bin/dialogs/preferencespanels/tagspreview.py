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

########################################################
#                   TagsPreview                        #
########################################################
class TagsPreview(wx.Panel):
    def __init__(self, parent, BeamSettings):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        #############
        # VARIABLES #
        #############
        font = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD)

        ###############
        # DESCRIPTION #
        ###############
        tagpreview = wx.StaticText(self, -1, "Tags preview")
        tagpreview.SetFont(font)
        description = wx.StaticText(self, -1, "Here are all available tags and their values displayed for")
        
        #################
        # TAGS SELECTOR #
        #################
        self.TagDropdown = wx.ComboBox(self,value="Current Song", choices=["Current Song","Previous Song","Next Song","Next Tanda", "Misc"], style=wx.CB_READONLY)
        self.TagDropdown.Bind(wx.EVT_COMBOBOX, self.onTagDropdown)
        
        #############
        # TAGS LIST #
        #############
        
        ##############
        # SET SIZERS #
        ##############
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(tagpreview, flag=wx.LEFT | wx.TOP | wx.BOTTOM, border=10)
        vbox.Add(description, flag=wx.LEFT, border=20)
        vbox.Add(self.TagDropdown, flag=wx.LEFT, border=20)

        self.SetSizer(vbox)
    
    
###################################################################
#                           EVENTS                                #
###################################################################

    def onTagDropdown(self, event):
        selected = self.TagDropdown.GetValue()
        print selected