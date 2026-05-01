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
from collections import OrderedDict

import wx
import wx.html

from bin.beamsettings import beamSettings
from bin.beamutils import formatMemoryUsageMb, getProcessMemoryUsageBytes


#
# Panel that gets displayt as preview in mainFrame
# and to disply on beamer in displayFrame
#
class DisplayPanel(wx.Panel):

    _background_bitmap_cache_limit = 8
    _cover_art_corner_radius = 'auto'
    _cover_art_feather_amount = 'auto'
    _cover_art_outline_enabled = True
    _cover_art_outline_alpha = 56
    _cover_art_outline_width = 1

    def _log_background_debug(self, message, *args):
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            logging.debug(message, *args)

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
        self._refresh_display_tweaks()
        self._background_bitmap_cache = OrderedDict()
        self._cover_art_bitmap_cache = OrderedDict()
        self.SetBackgroundColour(wx.BLACK)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.Bind(wx.EVT_WINDOW_DESTROY, self.OnDestroy)

        ########################## END FRAME INITIALIZATION #########################


########################################################
# Events
########################################################

    def OnSize(self, size):
        # self.SetSize(self.GetParent().GetCientSize() );
        if self._background_bitmap_cache:
            self._log_background_debug(
                "DisplayPanel background cache cleared on resize: entries=%d memory=%s",
                len(self._background_bitmap_cache),
                formatMemoryUsageMb(getProcessMemoryUsageBytes()),
            )
        self._background_bitmap_cache.clear()
        self._cover_art_bitmap_cache.clear()
        self.displayData.triggerResizeBackground = True
        self.Refresh()

    def OnEraseBackground(self, evt):
        pass

    def OnDestroy(self, event):
        if getattr(event, 'GetWindow', None) is not None and event.GetWindow() is not self:
            event.Skip()
            return

        if self._background_bitmap_cache:
            self._log_background_debug(
                "DisplayPanel background cache cleared on destroy: entries=%d memory=%s",
                len(self._background_bitmap_cache),
                formatMemoryUsageMb(getProcessMemoryUsageBytes()),
            )
        self._background_bitmap_cache.clear()
        self._cover_art_bitmap_cache.clear()
        event.Skip()

    def OnPaint(self, event):
        pdc = wx.BufferedPaintDC(self)
        try:
            dc = wx.GCDC(pdc)
        except:
            dc = pdc
        self.Draw(dc)

    def reloadFromSettings(self):
        self._refresh_display_tweaks()
        if self._background_bitmap_cache:
            self._log_background_debug(
                "DisplayPanel background cache cleared on settings reload: entries=%d memory=%s",
                len(self._background_bitmap_cache),
                formatMemoryUsageMb(getProcessMemoryUsageBytes()),
            )
        self._background_bitmap_cache.clear()
        self._cover_art_bitmap_cache.clear()
        self.displayData.triggerResizeBackground = True
        self.Refresh()
        self.Update()

    def _refresh_display_tweaks(self):
        self._background_bitmap_cache_limit = beamSettings.getBackgroundBitmapCacheLimit()
        self._cover_art_corner_radius = beamSettings.getCoverArtCornerRadius()
        self._cover_art_feather_amount = beamSettings.getCoverArtFeatherAmount()
        self._cover_art_outline_enabled = beamSettings.getCoverArtOutlineEnabled()
        self._cover_art_outline_alpha = beamSettings.getCoverArtOutlineAlpha()
        self._cover_art_outline_width = beamSettings.getCoverArtOutlineWidth()


########################################################
# Draw background
########################################################
    def _get_runtime_background_layers(self):
        background_layers = getattr(self.displayData, 'backgroundLayers', None) or {}
        base_layer = background_layers.get('base') or {}
        overlay_layer = background_layers.get('overlay') or {}
        return base_layer, overlay_layer

    def _get_legacy_background_bitmap(self):
        legacy_background_bitmap_getter = getattr(self.displayData, 'getLegacyBackgroundBitmap', None)
        if callable(legacy_background_bitmap_getter):
            return legacy_background_bitmap_getter()
        return getattr(self.displayData, '_legacyBackgroundBitmap', None)

    def _get_layer_draw_path(self, layer):
        current_path = layer.get('currentPath', '')
        if current_path:
            return current_path

        source_path = layer.get('sourcePath', '')
        if not source_path:
            return ''

        rotate_mode = str(layer.get('rotate', 'no')).lower()
        return self.displayData._resolve_background_path(
            source_path,
            prefer_random=rotate_mode == 'random',
        ) or ''

    def _get_scaled_background_bitmap(self, source_path, cliWidth, cliHeight, opacity=1.0):
        if not source_path:
            return None

        cache_key = (
            source_path,
            int(cliWidth),
            int(cliHeight),
            round(float(self.displayData.red), 4),
            round(float(self.displayData.green), 4),
            round(float(self.displayData.blue), 4),
            round(float(self.displayData.alpha), 4),
            round(float(opacity), 4),
        )
        cached_bitmap = self._background_bitmap_cache.get(cache_key)
        if cached_bitmap is not None:
            self._background_bitmap_cache.move_to_end(cache_key)
            DisplayPanel._log_background_debug(
                self,
                "DisplayPanel background cache hit: path=%s size=%sx%s opacity=%.2f entries=%d memory=%s",
                source_path,
                cliWidth,
                cliHeight,
                float(opacity),
                len(self._background_bitmap_cache),
                formatMemoryUsageMb(getProcessMemoryUsageBytes()),
            )
            return cached_bitmap

        DisplayPanel._log_background_debug(
            self,
            "DisplayPanel background cache miss: path=%s size=%sx%s opacity=%.2f entries=%d memory=%s",
            source_path,
            cliWidth,
            cliHeight,
            float(opacity),
            len(self._background_bitmap_cache),
            formatMemoryUsageMb(getProcessMemoryUsageBytes()),
        )

        log_silencer = wx.LogNull()
        try:
            image = wx.Image(source_path)
        finally:
            del log_silencer
        if not image.IsOk():
            DisplayPanel._log_background_debug(
                self,
                "DisplayPanel background image load failed: path=%s memory=%s",
                source_path,
                formatMemoryUsageMb(getProcessMemoryUsageBytes()),
            )
            return None

        image_width = image.GetWidth()
        image_height = image.GetHeight()
        if image_width <= 0 or image_height <= 0:
            DisplayPanel._log_background_debug(
                self,
                "DisplayPanel background image has invalid size: path=%s width=%s height=%s memory=%s",
                source_path,
                image_width,
                image_height,
                formatMemoryUsageMb(getProcessMemoryUsageBytes()),
            )
            return None

        aspect_ratio_window = float(cliHeight) / float(cliWidth)
        aspect_ratio_background = float(image_height) / float(image_width)
        if aspect_ratio_window >= aspect_ratio_background:
            scaled_width = int(cliHeight * image_width / image_height)
            scaled_height = cliHeight
        else:
            scaled_width = cliWidth
            scaled_height = int(cliWidth * image_height / image_width)

        image = image.Scale(scaled_width, scaled_height, wx.IMAGE_QUALITY_HIGH)

        red = float(self.displayData.red)
        green = float(self.displayData.green)
        blue = float(self.displayData.blue)
        alpha = float(self.displayData.alpha) * float(opacity)
        if red < 1 or green < 1 or blue < 1 or alpha < 1:
            image = image.AdjustChannels(red, green, blue, alpha)

        bitmap = wx.Bitmap(image)
        self._background_bitmap_cache[cache_key] = bitmap
        self._background_bitmap_cache.move_to_end(cache_key)
        DisplayPanel._log_background_debug(
            self,
            "DisplayPanel background bitmap created: path=%s scaled=%sx%s opacity=%.2f entries=%d memory=%s",
            source_path,
            scaled_width,
            scaled_height,
            float(opacity),
            len(self._background_bitmap_cache),
            formatMemoryUsageMb(getProcessMemoryUsageBytes()),
        )
        del image
        while len(self._background_bitmap_cache) > self._background_bitmap_cache_limit:
            evicted_key, evicted_bitmap = self._background_bitmap_cache.popitem(last=False)
            DisplayPanel._log_background_debug(
                self,
                "DisplayPanel background bitmap evicted: path=%s size=%sx%s opacity=%.2f entries=%d memory=%s",
                evicted_key[0],
                evicted_key[1],
                evicted_key[2],
                float(evicted_key[-1]),
                len(self._background_bitmap_cache),
                formatMemoryUsageMb(getProcessMemoryUsageBytes()),
            )
            del evicted_bitmap
        return bitmap

    def _draw_bitmap_centered(self, dc, bitmap, cliWidth, cliHeight):
        if bitmap is None:
            return

        resized_width, resized_height = bitmap.GetSize()
        x_position = int((cliWidth - resized_width) / 2)
        y_position = int((cliHeight - resized_height) / 2)
        dc.DrawBitmap(bitmap, x_position, y_position, True)

    def drawBackgroundBitmap(self, dc):
        cliWidth, cliHeight = self.GetClientSize()
        if not cliWidth or not cliHeight:
            return

        base_layer, overlay_layer = self._get_runtime_background_layers()
        overlay_mode = str(overlay_layer.get('mode', '')).lower()
        overlay_opacity = max(0.0, min(1.0, float(overlay_layer.get('opacity', 100)) / 100.0))

        base_drawn = False
        if base_layer.get('available'):
            base_source_path = self._get_layer_draw_path(base_layer)
            base_bitmap = self._get_scaled_background_bitmap(base_source_path, cliWidth, cliHeight, 1.0)
            if base_bitmap is not None:
                self._draw_bitmap_centered(dc, base_bitmap, cliWidth, cliHeight)
                self.modifiedBitmap = base_bitmap
                base_drawn = True

        if overlay_layer.get('available'):
            overlay_source_path = self._get_layer_draw_path(overlay_layer)
            overlay_bitmap = self._get_scaled_background_bitmap(
                overlay_source_path,
                cliWidth,
                cliHeight,
                1.0 if overlay_mode == 'replace' else overlay_opacity,
            )
            if overlay_bitmap is not None:
                if overlay_mode == 'replace':
                    dc.SetBackground(wx.Brush(wx.BLACK))
                    dc.Clear()
                self._draw_bitmap_centered(dc, overlay_bitmap, cliWidth, cliHeight)
                self.modifiedBitmap = overlay_bitmap
                base_drawn = True

        if not base_drawn:
            try:
                image = wx.Bitmap.ConvertToImage(self._get_legacy_background_bitmap())
                bitmap = wx.Bitmap(image)
                self._draw_bitmap_centered(dc, bitmap, cliWidth, cliHeight)
                self.modifiedBitmap = bitmap
            except Exception as e:
                logging.info(e, exc_info=True)

        self.displayData.triggerResizeBackground = False

########################################################
# DRAW TEXT & CoverArt
########################################################
    def _get_cover_art_corner_radius(self, size):
        try:
            configured_radius = int(self._cover_art_corner_radius)
        except (TypeError, ValueError):
            configured_radius = max(4, int(round(size * 0.08)))
        return min(max(0, configured_radius), max(0, size // 2))

    def _get_cover_art_feather_amount(self, radius):
        try:
            configured_feather = int(self._cover_art_feather_amount)
        except (TypeError, ValueError):
            configured_feather = max(1, int(round(radius * 0.35)))
        return min(max(0, configured_feather), max(0, radius))

    def _supports_cover_art_outline(self, dc):
        if not self._cover_art_outline_enabled:
            return False

        if self._cover_art_outline_alpha <= 0 or self._cover_art_outline_width <= 0:
            return False

        if not hasattr(dc, 'DrawRoundedRectangle'):
            return False

        gcdc_type = getattr(wx, 'GCDC', None)
        if gcdc_type is None:
            return False

        return isinstance(dc, gcdc_type)

    def _get_cover_art_bitmap(self, size):
        source_image = self.displayData.currentCoverArtImage
        if not source_image:
            return None

        cache_key = (getattr(self.nowPlayingData, 'currentCoverArtPath', '') or '', int(size))
        cached_bitmap = self._cover_art_bitmap_cache.get(cache_key)
        if cached_bitmap is not None:
            self._cover_art_bitmap_cache.move_to_end(cache_key)
            return cached_bitmap

        image = source_image.Scale(size, size, wx.IMAGE_QUALITY_HIGH)
        radius = self._get_cover_art_corner_radius(size)
        feather = self._get_cover_art_feather_amount(radius)

        if radius > 0:
            image.InitAlpha()
            for x_pos in range(size):
                nearest_x = min(x_pos, size - 1 - x_pos)
                for y_pos in range(size):
                    nearest_y = min(y_pos, size - 1 - y_pos)
                    if nearest_x >= radius or nearest_y >= radius:
                        continue

                    corner_dx = radius - nearest_x - 0.5
                    corner_dy = radius - nearest_y - 0.5
                    distance = (corner_dx * corner_dx + corner_dy * corner_dy) ** 0.5
                    if distance >= radius:
                        image.SetAlpha(x_pos, y_pos, 0)
                    elif feather > 0 and distance > radius - feather:
                        alpha = int(255 * (radius - distance) / feather)
                        image.SetAlpha(x_pos, y_pos, max(0, min(255, alpha)))

        bitmap = wx.Bitmap(image)
        self._cover_art_bitmap_cache[cache_key] = bitmap
        while len(self._cover_art_bitmap_cache) > self._background_bitmap_cache_limit:
            self._cover_art_bitmap_cache.popitem(last=False)
        return bitmap

    def _draw_cover_art_outline(self, dc, horizontal_position, vertical_position, size):
        if size <= 2 or not self._supports_cover_art_outline(dc):
            return

        try:
            outline_size = max(1, size - 1)
            radius = max(2, self._get_cover_art_corner_radius(size) - 1)
            dc.SetPen(wx.Pen(wx.Colour(255, 255, 255, self._cover_art_outline_alpha), self._cover_art_outline_width))
            dc.SetBrush(wx.TRANSPARENT_BRUSH)
            dc.DrawRoundedRectangle(int(horizontal_position), int(vertical_position), int(outline_size), int(outline_size), int(radius))
        except Exception:
            pass

    def drawCoverArt(self, dc, cliWidth, cliHeight, j):
        #Text and settings
        # filePath = self.currentDisplayRows[j]
        # Windows "file:///C:"
        # filePath = urllib.request.url2pathname(fileUrl[5:])
        # filePath = Path(fileUrl[8:])
        # filePath = self.currentDisplayRows[j]

        Settings = self.displayData.currentDisplaySettings[j]

        # Get (text) size and position
        # wx.Image.Scale expects integer dimensions across platforms.
        size = max(1, int(Settings['Size'] * cliHeight / 100))
        verticalPosition = int(Settings['Position'][0] * cliHeight / 100)

        # Alignment position
        if Settings['Alignment'] == 'Left':
            horizontalPosition = int(Settings['Position'][1] * cliWidth / 100)
        elif Settings['Alignment'] == 'Right':
            horizontalPosition = int(cliWidth - (int(Settings['Position'][1] * cliWidth / 100) + size))
        elif Settings['Alignment'] == 'Center':
            horizontalPosition = int((cliWidth - size) / 2)
        else:
            raise Exception("Unknown alignment" + Settings['Alignment'])


        if self.displayData.currentCoverArtImage:
            try:
                bitmap = self._get_cover_art_bitmap(size)
                if bitmap is None:
                    return
                dc.DrawBitmap(bitmap, int(horizontalPosition), int(verticalPosition), True)
                self._draw_cover_art_outline(dc, horizontalPosition, verticalPosition, size)
            except Exception:
                try:
                    fallback_image = self.displayData.currentCoverArtImage.Scale(size, size, wx.IMAGE_QUALITY_HIGH)
                    dc.DrawBitmap(wx.Bitmap(fallback_image), int(horizontalPosition), int(verticalPosition), True)
                except Exception:
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

    def _wrap_long_token(self, dc, token, max_width):
        if not token:
            return ['']

        wrapped_parts = []
        remaining = token
        while remaining:
            split_index = 1
            while split_index <= len(remaining):
                candidate = remaining[:split_index]
                candidate_width, _ = dc.GetTextExtent(candidate)
                if candidate_width > max_width:
                    split_index -= 1
                    break
                split_index += 1

            if split_index <= 0:
                split_index = 1
            if split_index > len(remaining):
                split_index = len(remaining)

            wrapped_parts.append(remaining[:split_index])
            remaining = remaining[split_index:]

        return wrapped_parts

    def _wrap_text_lines(self, dc, text, max_width):
        if max_width <= 0:
            return [text]

        wrapped_lines = []
        for paragraph in str(text).splitlines() or ['']:
            words = paragraph.split()
            if not words:
                wrapped_lines.append('')
                continue

            current_line = ''
            for word in words:
                candidate = word if not current_line else current_line + ' ' + word
                candidate_width, _ = dc.GetTextExtent(candidate)
                if candidate_width <= max_width:
                    current_line = candidate
                    continue

                if current_line:
                    wrapped_lines.append(current_line)
                    current_line = ''

                word_width, _ = dc.GetTextExtent(word)
                if word_width <= max_width:
                    current_line = word
                    continue

                wrapped_word_parts = self._wrap_long_token(dc, word, max_width)
                wrapped_lines.extend(wrapped_word_parts[:-1])
                current_line = wrapped_word_parts[-1]

            if current_line or not wrapped_lines:
                wrapped_lines.append(current_line)

        return wrapped_lines or ['']

    def _get_text_width_position(self, alignment, horizontal_setting, cliWidth, text_width):
        if alignment == 'Left':
            return int(horizontal_setting * cliWidth / 100)
        if alignment == 'Right':
            return cliWidth - (int(horizontal_setting * cliWidth / 100) + text_width)
        if alignment == 'Center':
            return (cliWidth - text_width) / 2
        raise Exception("Unknown alignment" + alignment)


    def drawTextItem(self, dc, cliWidth, cliHeight, j, extra_vertical_offset=0):

        # Text and settings
        text = self.displayData.currentDisplayRows[j]
        Settings = self.displayData.currentDisplaySettings[j]

        # Get text size and position 
        # PRS integered size
        Size = int(Settings['Size'] * cliHeight / 100)
        HeightPosition = int(Settings['Position'][0] * cliHeight / 100) + int(extra_vertical_offset)

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
        text_flow = Settings.get('TextFlow', 'Cut')

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
        if text_flow == 'Cut':
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

        if text_flow == 'Scale':
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

        if text_flow == 'Wrap':
            wrapped_lines = self._wrap_text_lines(dc, text, TextSpaceAvailable)
            line_height = dc.GetTextExtent('Ag')[1]
            line_spacing = max(line_height, int(line_height * 1.1))
            for line_index, line in enumerate(wrapped_lines):
                line_width, _ = dc.GetTextExtent(line)
                width_position = self._get_text_width_position(
                    Settings['Alignment'],
                    Settings['Position'][1],
                    cliWidth,
                    line_width,
                )
                dc.DrawText(line, int(width_position), int(HeightPosition + (line_index * line_spacing)))
            return max(0, (len(wrapped_lines) - 1) * line_spacing)

        # Alignment position
        WidthPosition = self._get_text_width_position(
            Settings['Alignment'],
            Settings['Position'][1],
            cliWidth,
            TextWidth,
        )

        # Draw the text
        # PRS integered argument
        dc.DrawText(text, int(WidthPosition), int(HeightPosition))
        return 0


    def drawItems(self, dc):

        if self.displayData.textsAreVisible == False:
            return

        cliWidth, cliHeight = self.GetClientSize()
        if not cliWidth or not cliHeight:
            return

        # Draw images
        for j in range(0, len(self.displayData.currentDisplaySettings)):
            field = self.displayData.currentDisplaySettings[j]["Field"]
            if field.strip() == "%CoverArt" and self.displayData.currentDisplayRows[j] != "":
                self.drawCoverArt(dc, cliWidth, cliHeight, j)

        # Draw text after/over image. Wrapped rows reserve extra vertical space for later rows.
        text_row_indexes = []
        for j in range(0, len(self.displayData.currentDisplaySettings)):
            field = self.displayData.currentDisplaySettings[j]["Field"]
            if field.strip() != "%CoverArt":
                text_row_indexes.append(j)

        text_row_indexes.sort(
            key=lambda index: (
                self.displayData.currentDisplaySettings[index]['Position'][0],
                self.displayData.currentDisplaySettings[index]['Position'][1],
                index,
            )
        )

        cumulative_vertical_offset = 0
        current_row_position = None
        current_row_extra_height = 0
        for j in text_row_indexes:
            settings = self.displayData.currentDisplaySettings[j]
            row_position = settings['Position'][0]
            if current_row_position is None:
                current_row_position = row_position
            elif row_position > current_row_position:
                cumulative_vertical_offset += current_row_extra_height
                current_row_extra_height = 0
                current_row_position = row_position

            row_extra_height = self.drawTextItem(
                dc,
                cliWidth,
                cliHeight,
                j,
                cumulative_vertical_offset,
            )
            current_row_extra_height = max(current_row_extra_height, row_extra_height)


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
        self.drawItems(dc)


