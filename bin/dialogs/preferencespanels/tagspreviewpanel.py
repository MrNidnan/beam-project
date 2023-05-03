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

import wx, os, platform
import logging
import numpy

########################################################
#                   TagsPreview                        #
########################################################
class TagsPreviewPanel(wx.Panel):
    def __init__(self, parent, BeamSettings, nowPlayingDataModel):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
        self.Bind(wx.EVT_PAINT, self.OnPaint)

        font = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        Tags = []
        self.nowPlayingDataModel = nowPlayingDataModel

        # Caption
        tagpreview = wx.StaticText(self, -1, "Tags preview               ")
        tagpreview.SetFont(font)
        description = wx.StaticText(self, -1, "Here are all available tags and their values displayed.")
        description.Wrap(380)

        # REFRESH BUTTON
        self.refreshButton = wx.Button(self, label="Refresh")
        self.refreshButton.Bind(wx.EVT_BUTTON, self.DoRefresh)

        # Tag type selector
        self.TagDropdown = wx.ComboBox(self,value="Current Song", choices=["Current Song","Previous Song","Next Song","Next Tanda", "Misc"], style=wx.CB_READONLY)
        self.TagDropdown.Bind(wx.EVT_COMBOBOX, self.DoRefresh)

        # List of tags
        #self.TagsList = wx.ListBox(self, -1, size=wx.DefaultSize, choices=Tags, style= wx.LB_NEEDED_SB)
        self.TagsList = wx.ListCtrl(self, -1, size=wx.DefaultSize, style= wx.LC_REPORT)
        bgcolour = self.TagsList.GetBackgroundColour()
        logging.debug("... bgcolour: " + str(bgcolour))
        fgcolour = tuple(numpy.subtract((255,255,255,510),bgcolour))
        logging.debug("... fgcolour: " + str(fgcolour))
        self.TagsList.SetForegroundColour(fgcolour)
        self.TagsList.InsertColumn(0, 'Tag', width=240)
        self.TagsList.InsertColumn(1, 'Value', width=500)
        self.DoRefresh(None)

        # Sizers
        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        vbox.Add(tagpreview, flag=wx.LEFT | wx.TOP | wx.BOTTOM, border=10)
        vbox.Add(description, flag=wx.LEFT, border=20)
        hbox.Add(self.TagDropdown)
        hbox.Add(self.refreshButton, flag=wx.LEFT, border=20)
        vbox.Add(hbox, flag=wx.LEFT, border=20)
        vbox.Add(self.TagsList, proportion=1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=20)

        self.SetSizer(vbox)

    def OnPaint(self, event):
        TagsSelected = self.TagDropdown.GetValue()
        self.BuildTagsList(TagsSelected)


    def DoRefresh(self, event):
        TagsSelected = self.TagDropdown.GetValue()
        self.BuildTagsList(TagsSelected)


    def BuildTagsList(self, TagsSelected):
        self.TagsList.DeleteAllItems()
        attributes = ['Artist', 'Album', 'AlbumArtist','Title','Genre','Comment','Composer','Year', 'Singer'
                      ,'Performer','IsCortina']
        additionalTags = ['%Hour','%Min','%DateDay','%DateMonth','%DateYear','%LongDate','%ShortDate','%SongsSinceLastCortina'
                        ,'%CurrentTandaSongsRemaining','%CurrentTandaLength']
        displayList = []

        if TagsSelected == "Current Song":
            preTag = '%'
        elif TagsSelected == "Previous Song":
            preTag = '%Previous'
        elif TagsSelected == "Next Song":
            preTag = '%Next'
        elif TagsSelected == "Next Tanda":
            preTag = '%NextTanda'
        else:
            for i in range(0, len(additionalTags)):
                try:
                    index = self.TagsList.InsertItem(i, additionalTags[i])
                    self.TagsList.SetItem(index, 1, self.nowPlayingDataModel.convDict[additionalTags[i]])
                except:
                    index = self.TagsList.InsertItem(i, additionalTags[i])
                    self.TagsList.SetItem(index, 1, str(' '))


        if not TagsSelected == 'Misc':
            #try:
            for i in range(0,len(attributes)):
                try:
                    index = self.TagsList.InsertItem(i, preTag+attributes[i])
                    self.TagsList.SetItem(index, 1, self.nowPlayingDataModel.convDict[preTag+attributes[i]])
                except:
                    index = self.TagsList.InsertItem(i, preTag+attributes[i])
                    self.TagsList.SetItem(index, 1, str(' '))


        #self.TagsList.Set(displayList)
