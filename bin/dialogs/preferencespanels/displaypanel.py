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
import wx.html
import wx.lib.delayedresult
import time
from bin.beamsettings import *


#
# Panel that gets displayt as preview in mainFrame
# and to disply on beamer in displayFrame
#
class DisplayPanel(wx.Panel):

    # Called by beam.py
    def __init__(self, parentFrame, displayData):

        # wx.Panel.__init__(self, parentFrame, -1, size=(100, 100), style = wx.BORDER_RAISED)
        wx.Panel.__init__(self, parent=parentFrame)

        # !!! Display to be moved to a panel

        ###################
        # CLASS VARIABLES #
        ###################
        # self.BeamSettings = BeamSettings
        # Do not use parent for threading
        self.displayData = displayData
        self.nowPlayingData = displayData.nowPlayingData

        self.SetDoubleBuffered(True)

        # Background
        self.modifiedBitmap = None
        self.SetBackgroundColour(wx.BLACK)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)

        ########################## END FRAME INITIALIZATION #########################


########################################################
# Events
########################################################

    def OnSize(self, size):
        # self.SetSize(self.GetParent().GetCientSize() );
        self.displayData.triggerResizeBackground = True
        self.Refresh()

    def OnEraseBackground(self, evt):
        pass

    def OnPaint(self, event):
        pdc = wx.BufferedPaintDC(self)
        try:
            dc = wx.GCDC(pdc)
        except:
            dc = pdc
        self.Draw(dc)


########################################################
# Draw background
########################################################
    def drawBackgroundBitmap(self, dc):
        cliWidth, cliHeight = self.GetClientSize()
        if not cliWidth or not cliHeight:
            return

        try:
            # Image = wx.ImageFromBitmap(self.backgroundImage)
            Image = wx.Bitmap.ConvertToImage(self.displayData.backgroundImage)
            #resize current background picture - currently used at main frame resizing

            aspectRatioWindow = float(cliHeight) / float(cliWidth)
            aspectRatioBackground = float(self.displayData.BackgroundImageHeight) / float(self.displayData.BackgroundImageWidth)
            if aspectRatioWindow >= aspectRatioBackground:
                # Window is too tall, scale to height
                Image = Image.Scale(cliHeight*self.displayData.BackgroundImageWidth / self.displayData.BackgroundImageHeight, cliHeight, wx.IMAGE_QUALITY_NORMAL)
            else:
                # Window is too wide, scale to width
                Image = Image.Scale(cliWidth, cliWidth*self.displayData.BackgroundImageHeight / self.displayData.BackgroundImageWidth, wx.IMAGE_QUALITY_NORMAL)
            # Fader
            if self.displayData.alpha <1 or self.displayData.red <1 or self.displayData.blue <1 or self.displayData.green <1:
                Image = Image.AdjustChannels(self.displayData.red, self.displayData.green, self.displayData.blue, self.displayData.alpha)
            
            self.displayData.triggerResizeBackground = False
            # self.modifiedBitmap = wx.BitmapFromImage(Image)
            self.modifiedBitmap = wx.Bitmap(Image)
        except Exception as e:
            logging.info(e, exc_info=True)
            self.modifiedBitmap = self.displayData.backgroundImage
            pass

            
        # Position the image and draw it
        resizedWidth, resizedHeight = self.modifiedBitmap.GetSize()
        self.xPosResized = (cliWidth - resizedWidth)/2
        self.yPosResized = (cliHeight - resizedHeight)/2
        dc.DrawBitmap(self.modifiedBitmap, self.xPosResized, self.yPosResized, True)

########################################################
# DRAW TEXT & CoverArt
########################################################
    def drawCoverArt(self, dc, cliWidth, cliHeight, j):
        image = None;
        #Text and settings
        # filePath = self.currentDisplayRows[j]
        # Windows "file:///C:"
        # filePath = urllib.request.url2pathname(fileUrl[5:])
        # filePath = Path(fileUrl[8:])
        # filePath = self.currentDisplayRows[j]

        Settings = self.displayData.currentDisplaySettings[j]

        # Get (text) size and position
        size = Settings['Size']*cliHeight/100
        verticalPosition = int(Settings['Position'][0] * cliHeight / 100)

        # Alignment position
        if Settings['Alignment'] == 'Left':
            horizontalPosition = int(Settings['Position'][1] * cliWidth / 100)
        elif Settings['Alignment'] == 'Right':
            horizontalPosition = cliWidth - (int(Settings['Position'][1] * cliWidth / 100) + size)
        elif Settings['Alignment'] == 'Center':
            horizontalPosition = (cliWidth - size) / 2
        else:
            raise Exception("Unknown alignment" + Settings['Alignment'])


        if self.displayData.currentCoverArtImage:
            try:
                image = self.displayData.currentCoverArtImage.Scale(size, size, wx.IMAGE_QUALITY_HIGH)
                bitmap = wx.Bitmap(image)
                dc.DrawBitmap(bitmap, horizontalPosition, verticalPosition)
            except Exception as e:
                pass

            # file_ = OggVorbis(path)
            # b64_pictures = file_.get("metadata_block_picture", [])
            # for n, b64_data in enumerate(b64_pictures):
            #     try:
            #         data = base64.b64decode(b64_data)
            #     except (TypeError, ValueError):
            #         continue
            #     try:
            #         picture = Picture(data)
            #     except FLACError:
            #         continue


    def drawTextItem(self, dc, cliWidth, cliHeight, j):

        # Text and settings
        text = self.displayData.currentDisplayRows[j]
        Settings = self.displayData.currentDisplaySettings[j]

        # Get text size and position
        Size = Settings['Size'] * cliHeight / 100
        HeightPosition = int(Settings['Position'][0] * cliHeight / 100)

        # Set font from settings
        face = Settings['Font']

        try:
            dc.SetFont(wx.Font(Size,
                               wx.ROMAN,
                               beamSettings.FontStyleDictionary[Settings['Style']],
                               beamSettings.FontWeightDictionary[Settings['Weight']],
                               False,
                               face))
        except:
            dc.SetFont(wx.Font(Size,
                               wx.ROMAN,
                               beamSettings.FontStyleDictionary[Settings['Style']],
                               beamSettings.FontWeightDictionary[Settings['Weight']],
                               False,
                               "Liberation Sans"))

        # Set font color, in the future, drawing a shadow ofsetted with the same text first might make a shadow!
        dc.SetTextForeground(eval(Settings['FontColor']))

        # Check if the text fits, cut it and add ...
        # if platform.system() == 'Darwin':
        #     try:
        #         text = text.decode('utf-8')
        #     except:
        #         pass
        TextWidth, TextHeight = dc.GetTextExtent(text)

        #
        # Find length and position of text
        #
        if Settings['Alignment'] == 'Center':
            TextSpaceAvailable = cliWidth
        else:
            TextSpaceAvailable = int((100 - Settings['Position'][1]) * cliWidth)

        #
        # TEXT FLOW = CUT
        #
        if Settings['TextFlow'] == 'Cut':
            while TextWidth > TextSpaceAvailable:
                try:
                    text = text[:-1]
                    TextWidth, TextHeight = dc.GetTextExtent(text)
                except:
                    text = text[:-2]
                    TextWidth, TextHeight = dc.GetTextExtent(text)
                if TextWidth < TextSpaceAvailable:
                    try:
                        text = text[:-2]
                        TextWidth, TextHeight = dc.GetTextExtent(text)
                    except:
                        text = text[:-3]
                        TextWidth, TextHeight = dc.GetTextExtent(text)
                    text = text + '...'
            TextWidth, TextHeight = dc.GetTextExtent(text)
        #
        # TEXT FLOW = SCALE
        #

        if Settings['TextFlow'] == 'Scale':
            while TextWidth > int(TextSpaceAvailable * 0.95):
                # 10% Scaling each time
                Size = int(Size * 0.9)
                try:
                    dc.SetFont(wx.Font(Size,
                                       wx.ROMAN,
                                       beamSettings.FontStyleDictionary[Settings['Style']],
                                       beamSettings.FontWeightDictionary[Settings['Weight']],
                                       False,
                                       face))
                except:
                    dc.SetFont(wx.Font(Size,
                                       wx.ROMAN,
                                       beamSettings.FontStyleDictionary[Settings['Style']],
                                       beamSettings.FontWeightDictionary[Settings['Weight']],
                                       False,
                                       "Liberation Sans"))
                TextWidth, TextHeight = dc.GetTextExtent(text)

        # Alignment position
        if Settings['Alignment'] == 'Left':
            WidthPosition = int(Settings['Position'][1] * cliWidth / 100)
        elif Settings['Alignment'] == 'Right':
            WidthPosition = cliWidth - (int(Settings['Position'][1] * cliWidth / 100) + TextWidth)
        elif Settings['Alignment'] == 'Center':
            WidthPosition = (cliWidth - TextWidth) / 2
        else:
            raise Exception("Unknown alignment" + Settings['Alignment'])

        # Draw the text
        dc.DrawText(text, WidthPosition, HeightPosition)


    def drawItems(self, dc):

        if self.displayData.textsAreVisible == False:
            return

        cliWidth, cliHeight = self.GetClientSize()
        if not cliWidth or not cliHeight:
            return

        # Draw images
        for j in range(0, len(self.displayData.currentDisplaySettings)):
            field = self.displayData.currentDisplaySettings[j]["Field"]
            if field.strip() == "%CoverArt":
                self.drawCoverArt(dc, cliWidth, cliHeight, j)

        # Draw text after/over image
        for j in range(0, len(self.displayData.currentDisplaySettings)):
            field = self.displayData.currentDisplaySettings[j]["Field"]
            if field.strip() != "%CoverArt":
                self.drawTextItem(dc, cliWidth, cliHeight, j)


########################################################
# DRAW
########################################################
    def Draw(self, dc):
    # Get width and height of window
        cliWidth, cliHeight = self.GetClientSize()
        if not cliWidth or not cliHeight:
            return
        dc.Clear()
        self.drawBackgroundBitmap(dc)

        if not self.nowPlayingData.isDisplayTimeExpired():
            self.drawItems(dc)


