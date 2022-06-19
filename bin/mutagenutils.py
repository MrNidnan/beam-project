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
import logging
import os

import wx
from io import BytesIO

from bin.songclass import SongObject
from mutagen import File
from mutagen.apev2 import APEv2
from mutagen.flac import FLAC
from mutagen.id3 import ID3
from mutagen.mp4 import MP4
from mutagen.mp4 import MP4Cover


###############################################################
#
# Building from URL with mutagen
#
###############################################################

def readSongObject(filePath):
    logging.debug("readSongObject(" + filePath + ")")
    songObject = SongObject()

    audio = File(filePath, easy=True)
    audioRaw = File(filePath, easy=False)

    if audio == {} or audioRaw == {}:
        songObject.ModuleMessage = "Error reading file", filePath
        raise NameError("Error reading file", filePath)

    if "artist" in audio:
        # MP3, MP4, FLAC
        songObject.Artist = audio["artist"][0]
    else:
        # AIF
        if "TPE1" in audio:
            songObject.Artist = audio["TPE1"][0]

    if "album" in audio:
        songObject.Album = audio["album"][0]
    else:
        if "TALB" in audio:
            songObject.Album = audio["TALB"][0]

    if "title" in audio:
        songObject.Title = audio["title"][0]
    else:
        if "TIT2" in audio:
            songObject.Title = audio["TIT2"][0]

    if "genre" in audio:
        songObject.Genre = audio["genre"][0]
    else:
        if "TCON" in audio:
            songObject.Genre = audio["TCON"][0]

    if "comment" in audio:
        songObject.Comment = audio["comment"][0]
    else:
        if 'COMM::eng' in audioRaw:
            songObject.Comment = audioRaw['COMM::eng'][0]

    if "composer" in audio:
        songObject.Composer = audio["composer"][0]
    else:
        if "TCOM" in audio:
            songObject.Composer = audio["TCOM"][0]

    # ??? year
    if "date" in audio:
        songObject.Year = audio["date"][0]
    else:
        if "TDRC" in audio:
            songObject.Year = audio["TDRC"][0]

    if "albumartist" in audio:
        songObject.AlbumArtist = audio["albumartist"][0]
    else:
        if "TPE2" in audio:
            songObject.AlbumArtist = audio["TPE2"][0]

    if "performer" in audio:
        songObject.Performer = audio["performer"][0]

    songObject.FilePath = filePath

    return songObject


########################################################
# DRAW TEXT & CoverArt
########################################################
def readCoverArtImage(filePath):
    logging.debug("readCoverArtImage(" + filePath + ")")
    coverArtImage = None
    bitmapType = None

    iswxlog = wx.Log.IsEnabled
    if iswxlog:
        wx.Log.EnableLogging(enable=False)

    if not coverArtImage:
        try:
            id3Frame = ID3(filePath)
            apicTag = id3Frame.get("APIC:")
            data = apicTag.data
            if data:
                if (apicTag.mime.lower() == 'image/jpeg') or (apicTag.mime.lower() == 'image/jpg'):
                    bitmapType = wx.BITMAP_TYPE_JPEG
                if apicTag.mime.lower() == 'image/png':
                    bitmapType = wx.BITMAP_TYPE_PNG
                if apicTag.mime.lower() == 'image/gif':
                    bitmapType = wx.BITMAP_TYPE_GIF
                if apicTag.mime.lower() == 'image/bmp':
                    bitmapType = wx.BITMAP_TYPE_BMP
                if not bitmapType:
                    logging.warning("Unkown mime type: " + apicTag.mime.lower())
                    bitmapType = wx.BITMAP_TYPE_ANY
                coverArtImage = wx.Image(BytesIO(data), bitmapType)
        except Exception as e:
            pass

    if not coverArtImage:
        try:
            mp4Frame = MP4(filePath);
            tags = mp4Frame.tags;
            covr = tags['covr'][0];

            if covr.imageformat == MP4Cover.FORMAT_JPEG:
                bitmapType = wx.BITMAP_TYPE_JPEG
            if covr.imageformat == MP4Cover.FORMAT_PNG:
                bitmapType = wx.BITMAP_TYPE_PNG
            if not bitmapType:
                logging.warning("Unkown MP4Cover.FORMAT: " + covr.imageformat)
                bitmapType = wx.BITMAP_TYPE_ANY

            coverArtImage = wx.Image(BytesIO(covr), bitmapType);
        except Exception as e:
            pass

    if not coverArtImage:
        try:
            flac = FLAC(filePath)
            pict = flac.pictures[0]
            if pict is not None:
                if (pict.mime.lower() == 'image/jpeg') or (pict.mime.lower() == 'image/jpg'):
                    bitmapType = wx.BITMAP_TYPE_JPEG
                if pict.mime.lower() == 'image/png':
                    bitmapType = wx.BITMAP_TYPE_PNG
                if pict.mime.lower() == 'image/gif':
                    bitmapType = wx.BITMAP_TYPE_GIF
                if pict.mime.lower() == 'image/bmp':
                    bitmapType = wx.BITMAP_TYPE_BMP
                if not bitmapType:
                    logging.warning("Unkown mime type: " + pict.mime.lower())
                    bitmapType = wx.BITMAP_TYPE_ANY
                # Suppress warning diaglog(!) "iCCP: known incorrect sRGB profile"
                # from libpng on Tango Tunes cover art in debugger
                coverArtImage = wx.Image(BytesIO(pict.data), bitmapType)
        except Exception as e:
            pass

    if not coverArtImage:
        try:
            apeFrame = APEv2(filePath)
            logging.debug("APEv2 not implemented yet")
            logging.debug(apeFrame.pprint())
            # keys = fileFrame.keys()
            # logging.debug(keys)
            # dict_keys = keys.dict_keys
            # logging.debug(dict_keys)
            # apicTag = id3Tags.get("APIC:")
            # for apicTag in id3Tags.getall("APIC"):
            #    print(apicTag.pprint())
            # pictures = fileFrame.pictures
            # apicTag = fileFrame.get("APIC:")
            # if apicTag:
            #    pict = apicTag.data
            #    image = wx.Image(BytesIO(pict), wx.BITMAP_TYPE_JPEG)
        except Exception as e:
            pass

        if not coverArtImage:
            try:
                # AlbumArt_{GUID}.* ?
                # PRIV=WM/WMCollectionID ?
                # in 'WM/WMCollectionID' or WM/WMCollectionGroupID'
                #
                # easyFrame = EasyID3(filePath)
                # logging.debug(type(easyFrame))
                # logging.debug(easyFrame)
                # for key in easyFrame.valid_keys:
                #     try:
                #         valueArr = easyFrame.get(key)
                #         for value in valueArr:
                #             logging.debug("Key: " + key + "Value: " + value)
                #     except:
                #         pass
                pass
            except:
                pass

        if not coverArtImage:
            try:
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
                pass
            except:
                pass

        # read jpg with the same name
        if not coverArtImage:
            try:
                pathFileName, fileExt = os.path.splitext(filePath)
                imagePath = pathFileName + ".jpg"
                if os.path.isfile(imagePath):
                    coverArtImage = wx.Image(imagePath, wx.BITMAP_TYPE_JPEG)
            except:
                pass

        # read fist file that is jpg
        if not coverArtImage:
            try:
                fileDir, fileName = os.path.split(filePath)
                for fileName in os.listdir(fileDir):
                    if fileName.endswith(".jpg"):
                        imagePath = os.path.join(fileDir, fileName)
                        if os.path.isfile(imagePath):
                            coverArtImage = wx.Image(imagePath, wx.BITMAP_TYPE_JPEG)
                            break
            except:
                pass

        if iswxlog:
            wx.Log.EnableLogging(enable=True)

    return coverArtImage

