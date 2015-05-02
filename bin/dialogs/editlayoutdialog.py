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



import wx, wx.html
import os



#
# LAYOUT WINDOW-CLASS
#
#
class EditLayoutDialog(wx.Dialog):
    def __init__(self, parent, RowSelected, mode, LayoutList):
        self.EditLayoutDialog   = wx.Dialog.__init__(self, parent, title=mode)
        self.EditLayoutPanel    = wx.Panel(self)
        self.parent             = parent
        self.RowSelected        = RowSelected
        self.mode               = mode
        self.LayoutList         = LayoutList

        self.ButtonSaveLayout   = wx.Button(self.EditLayoutPanel, label="Save")
        self.ButtonCancelLayout     = wx.Button(self.EditLayoutPanel, label="Cancel")
        self.ButtonSaveLayout.Bind(wx.EVT_BUTTON, self.OnSaveLayoutItem)
        self.ButtonCancelLayout.Bind(wx.EVT_BUTTON, self.OnCancelLayoutItem)

        Fonts   = ["Decorative","Default","Modern","Roman","Script","Swiss","Teletype"]
        
        e = wx.FontEnumerator()
        e.EnumerateFacenames()
        elist= e.GetFacenames()
 
        elist.sort()
 
        Weights     = ["Bold","Light","Normal"]
        Styles  = ["Italic","Normal","Slant"]
        Align = ["Left","Center","Right"]
        
        HideLayoutTags = [  '','%Artist','%Album','%Title','%Genre','%Comment','%Composer',
                            '%Year','%Singer','%AlbumArtist','%Performer','%IsCortina',
                            '%PreviousArtist','%PreviousAlbum','%PreviousTitle','%PreviousGenre','%PreviousComment','%PreviousComposer',
                            '%PreviousYear','%PreviousSinger','%PreviousAlbumArtist','%PreviousPerformer','%PreviousIsCortina',
                            '%NextArtist','%NextAlbum','%NextTitle','%NextGenre','%NextComment','%NextComposer',
                            '%NextYear','%NextSinger','%NextAlbumArtist','%NextPerformer','%NextIsCortina',
                            '%NextTandaArtist','%NextTandaAlbum','%NextTandaTitle','%NextTandaGenre','%NextTandaComment','%NextTandaComposer',
                            '%NextTandaYear','%NextTandaSinger','%NextTandaAlbumArtist','%NextTandaPerformer']
                
        # Check if it is a new line
        if self.RowSelected<len(self.LayoutList):
            # Get the properties of the selected item
            self.Settings   = LayoutList[self.RowSelected]
        else:
            # Create a new default setting
            self.Settings   = ({"Field": "%Artist", "Font": "Default","Style": "Normal", "Weight": "Bold", "Size": 20, "FontColor": "(255,255,255,255)", "HideControl": "", "Position": [50,50], "Alignment": "Center", "Active": "yes"})

        
        # Define fields
        self.LabelText          = wx.TextCtrl(self.EditLayoutPanel, size=(250,-1), value=self.Settings[u'Field'])
        self.FontDropdown       = wx.ComboBox(self.EditLayoutPanel, size=(150,-1), value=self.Settings[u'Font'], choices=elist, style=wx.CB_READONLY)
        self.StyleDropdown      = wx.ComboBox(self.EditLayoutPanel, size=(80,-1), value=self.Settings[u'Style'], choices=Styles, style=wx.CB_READONLY)
        self.WeightDropdown     = wx.ComboBox(self.EditLayoutPanel, size=(80,-1), value=self.Settings[u'Weight'], choices=Weights, style=wx.CB_READONLY)
        self.SizeText           = wx.TextCtrl(self.EditLayoutPanel, size=(80,-1), value=str(self.Settings[u'Size']))
        self.ColorField         = wx.ColourPickerCtrl(self.EditLayoutPanel, size=(80,-1))
        self.HideText           = wx.ComboBox(self.EditLayoutPanel, size=(250,-1), value=self.Settings[u'HideControl'], choices=HideLayoutTags, style=wx.CB_READONLY)
        self.VerticalPos        = wx.TextCtrl(self.EditLayoutPanel, size=(80,-1), value=str(self.Settings[u'Position'][0]))
        self.HorizontalPos      = wx.TextCtrl(self.EditLayoutPanel, size=(80,-1), value=str(self.Settings[u'Position'][1]))
        self.Alignment          = wx.ComboBox(self.EditLayoutPanel, size=(150,-1), value=self.Settings[u'Alignment'], choices=Align, style=wx.CB_READONLY)
        self.ColorField.SetColour(eval(self.Settings[u'FontColor']))
        
        if self.Settings[u'Alignment']=="Center":
            self.HorizontalPos.Enable(False)
        self.Alignment.Bind(wx.EVT_COMBOBOX, self.DisableHorizontalBox)
        # Information area
        InfoGrid    =   wx.FlexGridSizer(4, 5, 5, 5)
        InfoGrid.AddMany ( [(wx.StaticText(self.EditLayoutPanel, label="Label"), 0, wx.EXPAND),
                        (wx.StaticText(self.EditLayoutPanel, label="Font"), 0, wx.EXPAND),
                        (wx.StaticText(self.EditLayoutPanel, label="Style"), 0, wx.EXPAND),
                        (wx.StaticText(self.EditLayoutPanel, label="Weight"), 0, wx.EXPAND),
                        (wx.StaticText(self.EditLayoutPanel, label="Size"), 0,wx.EXPAND),
                        (self.LabelText, 0),
                        (self.FontDropdown, 0),
                        (self.StyleDropdown, 0),
                        (self.WeightDropdown, 0),
                        (self.SizeText, 0, wx.EXPAND),
                        (wx.StaticText(self.EditLayoutPanel, label="Hide if following tag is empty:"), 0, wx.EXPAND),
                        (wx.StaticText(self.EditLayoutPanel, label="Alignment"), 0, wx.EXPAND),
                        (wx.StaticText(self.EditLayoutPanel, label="Vertical"), 0, wx.EXPAND),
                        (wx.StaticText(self.EditLayoutPanel, label="Horizontal"), 0, wx.EXPAND),
                        (wx.StaticText(self.EditLayoutPanel, label="Color"), 0, wx.EXPAND),
                        (self.HideText, 0),
                        (self.Alignment, 0),
                        (self.VerticalPos, 0),
                        (self.HorizontalPos, 0),
                        (self.ColorField, 0)
                        ])

        self.vboxLayout = wx.BoxSizer(wx.VERTICAL)
        self.hboxLayout = wx.BoxSizer(wx.HORIZONTAL)
        
        self.hboxLayout.Add(self.ButtonSaveLayout, 0, flag=wx.ALL | wx.ALIGN_RIGHT, border=10)
        self.hboxLayout.Add(self.ButtonCancelLayout, 0, flag=wx.ALL | wx.ALIGN_RIGHT, border=10)
        
        self.vboxLayout.Add(InfoGrid, 0, flag=wx.ALL, border=10)
        self.vboxLayout.Add(self.hboxLayout, 0, flag=wx.ALL | wx.ALIGN_RIGHT)

        self.EditLayoutPanel.SetSizer(self.vboxLayout)
        self.vboxLayout.SetSizeHints(self)
        
    def DisableHorizontalBox(self, event):
        print "TEST"
        if self.Alignment.GetValue()=="Center":
            self.HorizontalPos.Enable(False)
        else:
            self.HorizontalPos.Enable(True)

#
# SAVE
#
    def OnSaveLayoutItem(self, event):
        self.Settings[u'Field']         = self.LabelText.GetValue()
        self.Settings[u'Font']      = self.FontDropdown.GetValue()
        self.Settings[u'Style']         = self.StyleDropdown.GetValue()
        self.Settings[u'Weight']        = self.WeightDropdown.GetValue()
        self.Settings[u'Size']      = int(self.SizeText.GetValue())
        self.Settings[u'HideControl']   = self.HideText.GetValue()
        self.Settings[u'FontColor']     = str(self.ColorField.GetColour())
        self.Settings[u'Position']  = [int(self.VerticalPos.GetValue()), int(self.HorizontalPos.GetValue())]
        self.Settings[u'Alignment'] = self.Alignment.GetValue()

        # Remove old item from dictionary
        if self.mode == "Edit layout item":
            self.LayoutList.pop(self.RowSelected)

        # Save item into dictionary
        xpos = self.Settings['Position']
        newposition = len(self.LayoutList)

        for i in range(0, len(self.LayoutList)):
            pos = self.LayoutList[i]['Position']
            if xpos[0] < pos[0]:
                newposition = i
                break
        
        # Decide where Layout goes into the vector self.Settings
        if self.mode == "Add layout item":
            if  newposition < len(self.LayoutList):
                self.LayoutList.insert(newposition, self.Settings) #Insert in at position
            else:
                self.LayoutList.append(self.Settings) # Append in the end
        else: #Edit layout
                self.LayoutList.insert(newposition, self.Settings)
        self.parent.BuildLayoutList()
        self.Destroy()

#
# CANCEL
#
    def OnCancelLayoutItem(self, event):
        self.Destroy()

