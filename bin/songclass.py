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

#import platform, os, sys
import logging

###############################################################
#
# INIT
#
###############################################################


def alwaysStr(curr_str):
    if curr_str:
        ret_str = curr_str
    else:
        ret_str = ""
    return ret_str


class SongObject(object):

    def __init__(self, p_artist="", p_album="", p_title="", p_genre="",
                 p_comment="", p_composer="", p_year="", p_singer="",
                 p_albumArtist="", p_performer = "", p_isCortina = "no",
                 p_filePath="", p_moduleMessage="", p_ignoreSong="no"):
        self.Artist        = alwaysStr(p_artist)
        self.Album         = alwaysStr(p_album)
        self.Title         = alwaysStr(p_title)
        self.Genre         = alwaysStr(p_genre)
        self.Comment       = alwaysStr(p_comment)
        self.Composer      = alwaysStr(p_composer)
        self.Year          = alwaysStr(p_year)
        self.Singer        = alwaysStr(p_singer)
        self.AlbumArtist   = alwaysStr(p_albumArtist)
        self.Performer     = alwaysStr(p_performer)
        self.IsCortina     = alwaysStr(p_isCortina)
        self.FilePath       = alwaysStr(p_filePath)
        self.ModuleMessage = alwaysStr(p_moduleMessage)
        self.IgnoreSong    = alwaysStr(p_ignoreSong)

    def __eq__(self, other):
        if isinstance(other, SongObject):
            return (self.Artist == other.Artist and
                    self.Album == other.Album and
                    self.Title == other.Title and
                    self.Genre == other.Genre and
                    self.Comment == other.Comment and
                    self.Composer == other.Composer and
                    self.Year == other.Year and
                    self.AlbumArtist == other.AlbumArtist and
                    self.Performer == other.Performer and
                    self.FilePath == other.FilePath)
        else:
            return False
            
    
    def __ne__(self, other):
        if isinstance(other, SongObject):
            return (self.Artist != other.Artist or
                    self.Album != other.Album or
                    self.Title != other.Title or
                    self.Genre != other.Genre or
                    self.Comment != other.Comment or
                    self.Composer != other.Composer or
                    self.Year != other.Year or
                    self.AlbumArtist != other.AlbumArtist or
                    self.Performer != other.Performer or
                    self.FilePath != other.FilePath)
        else:
            return False


    def sanitizeFields(self):
        self.Artist        = alwaysStr(self.Artist)
        self.Album         = alwaysStr(self.Album)
        self.Title         = alwaysStr(self.Title)
        self.Genre         = alwaysStr(self.Genre)
        self.Composer      = alwaysStr(self.Composer)
        self.Year          = alwaysStr(self.Year)
        self.Singer        = alwaysStr(self.Singer)
        self.AlbumArtist   = alwaysStr(self.AlbumArtist)
        self.Performer     = alwaysStr(self.Performer)
        self.IsCortina     = alwaysStr(self.IsCortina)
        self.FilePath       = alwaysStr(self.FilePath)
        self.ModuleMessage = alwaysStr(self.ModuleMessage)
        self.IgnoreSong    = alwaysStr(self.IgnoreSong)



###############################################################
#
# Song rules
#
###############################################################

    def applySongRules(self, rulesArray):
        for i in range(0, len(rulesArray)):
            currentRule = rulesArray[i]
            try:
                #
                # IGNORE
                #
                if currentRule['Type'] == 'Ignore' and currentRule['Active'] == 'yes':
                    # Rule[u'Field2'] == is: IgnoreSong[j] shall be 'yes' if Rule[u'Field1'] is Rule[u'Field3']
                    if currentRule['Field2'] == 'is':
                        if getattr(self, currentRule['Field1'].replace("%","")).lower() == str(currentRule['Field3']).lower():
                            self.IgnoreSong = "yes"
                    # Rule[u'Field2'] == is not: IgnoreSong[j] shall be 1 if Rule[u'Field1'] not in Rule[u'Field3']
                    if currentRule['Field2'] == 'is not':
                        if getattr(self, currentRule['Field1'].replace("%","")).lower() not in str("["+currentRule['Field3'].lower()+"]"):
                            self.IgnoreSong = "yes"
                    # Rule[u'Field2'] == contains: IgnoreSong[j] shall be 1 if Rule[u'Field1'] contains any of Rule[u'Field3']
                    if currentRule['Field2'] == 'contains':
                        if str(currentRule['Field3']).lower() in getattr(self, currentRule['Field1'].replace("%","")).lower():
                            self.IgnoreSong = "yes"
                #
                # PARSE
                #
                if currentRule['Type'] == 'Parse' and currentRule['Active'] == 'yes':
                    # Find currentRule[u'Field2'] in currentRule[u'Field1'],
                    # split currentRule[u'Field1'] and save into Rule[u'Field3 and 4]
                    if str(currentRule['Field2'].replace("%"," self.")) in eval(str(currentRule['Field1'].replace("%"," self."))):
                        splitStrings = eval(str(currentRule['Field1']).replace("%"," self.")).split(str(currentRule['Field2']))
                        setattr(self, currentRule['Field3'].replace("%",""), splitStrings[0])
                        setattr(self, currentRule['Field4'].replace("%",""), splitStrings[1])
                #
                # CORTINA
                #
                if currentRule['Type'] == 'Cortina' and currentRule['Active'] == 'yes':
                    # Rule[u'Field2'] == is: IsCortina[j] shall be 1 if Rule[u'Field1'] is Rule[u'Field3']
                    if currentRule['Field2'] == 'is':
                        if getattr(self, currentRule['Field1'].replace("%","")).lower() == str(currentRule['Field3']).lower():
                            self.IsCortina = "yes"
                    # Rule[u'Field2'] == is not: IsCortina[j] shall be 1 if Rule[u'Field1'] not in Rule[u'Field3']
                    if currentRule['Field2'] == 'is not':
                        if getattr(self, currentRule['Field1'].replace("%","")).lower() not in str("["+currentRule['Field3'].lower()+"]"):
                            self.IsCortina = "yes"
                    # Rule[u'Field2'] == contains: IsCortina[j] shall be 1 if Rule[u'Field1'] contains any of Rule[u'Field3']
                    if currentRule['Field2'] == 'contains':
                        if str(currentRule['Field3']).lower() in getattr(self, currentRule['Field1'].replace("%","")).lower():
                            self.IsCortina = "yes"
                #
                # COPY
                #
                if currentRule['Type'] == 'Copy' and currentRule['Active'] == 'yes':
                    # Rule[u'Field1'] shall be Rule[u'Field2']
                    # Example:
                    # Singer(j) = Comment(j)
                    setattr(self, currentRule['Field2'].replace("%",""), getattr(self, currentRule['Field1'].replace("%","")) )
                #
                # Replace
                #
                if currentRule['Type'] == 'Replace' and currentRule['Active'] == 'yes':
                    # Rule[u'Field1'] shall be Rule[u'Field2']
                    # Example:
                    # Artist(j) = 'Desired string'
                    if str(currentRule['Field3']).lower() in getattr(self, currentRule['Field1'].replace("%","")).lower():
                        setattr(self, currentRule['Field1'].replace("%",""), str(currentRule['Field2']))
            except:
                logging.error("Error at Rule: " + str(i) + " Type: " + currentRule['Type'] + "  First Field " + currentRule['Field1'])
                break
    
    

