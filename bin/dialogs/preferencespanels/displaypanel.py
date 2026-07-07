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

from bin import textfit
from bin.beamsettings import beamSettings
from bin.beamutils import formatMemoryUsageMb, getProcessMemoryUsageBytes
from bin.mutagenutils import readCoverArtImage


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
    DEFAULT_CENTER_MAX_WIDTH_PERCENT = 85
    VERTICAL_SAFE_BOTTOM_RATIO = 0.92
    _BLOCK_FIT_MAX_ITERATIONS = 60

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
        if str(layer.get('kind', '')).lower() == 'color':
            return ''

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

    def _parse_background_colour(self, layer, opacity=1.0):
        if str(layer.get('kind', '')).lower() != 'color':
            return None

        color_value = str(layer.get('colorValue', '') or '').strip()
        if color_value.startswith('#'):
            color_value = color_value[1:]

        if len(color_value) not in (6, 8):
            return None

        try:
            red = int(color_value[0:2], 16)
            green = int(color_value[2:4], 16)
            blue = int(color_value[4:6], 16)
            alpha = int(color_value[6:8], 16) if len(color_value) == 8 else 255
        except ValueError:
            return None

        scaled_alpha = max(0, min(255, int(round(alpha * float(opacity)))))
        return wx.Colour(red, green, blue, scaled_alpha)

    def _fill_background_colour(self, dc, colour, cliWidth, cliHeight):
        if colour is None:
            return False

        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.SetBrush(wx.Brush(colour))
        dc.DrawRectangle(0, 0, int(cliWidth), int(cliHeight))
        return True

    @staticmethod
    def _readability_to_blur_dim(readability):
        # "Improve readability": map a single 0..100 value to blur radius and dim opacity.
        # blur radius = readability * 0.20 (0->0px, 50->10px, 100->20px)
        # dim opacity = readability * 0.005 (0->0.00, 50->0.25, 100->0.50)
        readability = max(0, min(100, int(readability or 0)))
        blur_radius = int(round(readability * 0.20))
        dim_opacity = readability * 0.005
        return blur_radius, dim_opacity

    def _draw_readability_dim(self, dc, base_layer, cliWidth, cliHeight):
        if not base_layer.get('improveReadability'):
            return
        _, dim_opacity = self._readability_to_blur_dim(base_layer.get('readability', 0))
        if dim_opacity <= 0:
            return
        dim_alpha = max(0, min(255, int(round(dim_opacity * 255))))
        self._fill_background_colour(dc, wx.Colour(0, 0, 0, dim_alpha), cliWidth, cliHeight)

    def _get_scaled_background_bitmap(self, source_path, cliWidth, cliHeight, opacity=1.0, source_image=None, cache_source_key=None, readability=0):
        if not source_path and source_image is None:
            return None

        readability = max(0, min(100, int(readability or 0)))
        cache_key = (
            cache_source_key or source_path,
            int(cliWidth),
            int(cliHeight),
            round(float(self.displayData.red), 4),
            round(float(self.displayData.green), 4),
            round(float(self.displayData.blue), 4),
            round(float(self.displayData.alpha), 4),
            round(float(opacity), 4),
            readability,
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

        if source_image is not None:
            image = source_image.Copy()
        else:
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

        blur_radius, _ = DisplayPanel._readability_to_blur_dim(readability)
        if blur_radius > 0:
            try:
                image = image.Blur(blur_radius)
            except Exception:
                pass

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
                float(evicted_key[7]),
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

        base_readability = int(base_layer.get('readability', 0) or 0) if base_layer.get('improveReadability') else 0

        base_drawn = False
        if base_layer.get('available'):
            base_colour = self._parse_background_colour(base_layer, 1.0)
            if self._fill_background_colour(dc, base_colour, cliWidth, cliHeight):
                self.modifiedBitmap = None
                base_drawn = True
            else:
                base_source_path = self._get_layer_draw_path(base_layer)
                base_bitmap = self._get_scaled_background_bitmap(base_source_path, cliWidth, cliHeight, 1.0, readability=base_readability)
                if base_bitmap is not None:
                    self._draw_bitmap_centered(dc, base_bitmap, cliWidth, cliHeight)
                    self.modifiedBitmap = base_bitmap
                    base_drawn = True

        if overlay_layer.get('available'):
            overlay_colour = self._parse_background_colour(
                overlay_layer,
                1.0 if overlay_mode == 'replace' else overlay_opacity,
            )
            if overlay_colour is not None:
                if overlay_mode == 'replace':
                    dc.SetBackground(wx.Brush(wx.BLACK))
                    dc.Clear()
                self._fill_background_colour(dc, overlay_colour, cliWidth, cliHeight)
                self.modifiedBitmap = None
                base_drawn = True
            else:
                overlay_source_path = self._get_layer_draw_path(overlay_layer)
                overlay_source_image = None
                overlay_cache_source_key = None
                if str(overlay_layer.get('kind', '')).lower() == 'coverart':
                    overlay_source_image = self.displayData.currentCoverArtImage
                    overlay_cache_source_key = overlay_layer.get('sourcePath', '') or overlay_layer.get('reference', 'coverArt:current')
                    if overlay_source_image is None and overlay_source_path:
                        overlay_source_image = readCoverArtImage(overlay_source_path)
                overlay_bitmap = self._get_scaled_background_bitmap(
                    overlay_source_path,
                    cliWidth,
                    cliHeight,
                    1.0 if overlay_mode == 'replace' else overlay_opacity,
                    source_image=overlay_source_image,
                    cache_source_key=overlay_cache_source_key,
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

        # "Improve readability": darken the resolved background before drawing text.
        self._draw_readability_dim(dc, base_layer, cliWidth, cliHeight)

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

        # Calculate aspect-ratio-preserving dimensions
        img_w, img_h = source_image.GetWidth(), source_image.GetHeight()
        if img_w <= 0 or img_h <= 0:
            return None
        scale = min(float(size) / img_w, float(size) / img_h)
        new_w, new_h = int(img_w * scale), int(img_h * scale)

        cache_key = (getattr(self.nowPlayingData, 'currentCoverArtPath', '') or '', int(new_w), int(new_h))
        cached_bitmap = self._cover_art_bitmap_cache.get(cache_key)
        if cached_bitmap is not None:
            self._cover_art_bitmap_cache.move_to_end(cache_key)
            return cached_bitmap

        image = source_image.Scale(new_w, new_h, wx.IMAGE_QUALITY_HIGH)
        # Use the smaller of width/height for radius calculation
        min_dim = min(new_w, new_h)
        radius = self._get_cover_art_corner_radius(min_dim)
        feather = self._get_cover_art_feather_amount(radius)

        # DEV NOTE / PERF: the rounded-corner + feather mask below is a pure-Python
        # per-pixel double loop (O(new_w * new_h)). On a ~500x500 cover that is
        # ~250k iterations with a SetAlpha() call per edge pixel, run on the UI
        # thread. The result is memoized in self._cover_art_bitmap_cache, so it
        # only fires on a cache miss (new cover art or a new render size), but
        # each miss can briefly stall the UI - most visible under software
        # rendering (e.g. WSLg/llvmpipe, no GPU accel).
        #   - This loop is gated by `radius > 0`, NOT by feather. Setting corner
        #     radius to 0 skips it entirely (fast path); feather 0 does NOT skip
        #     it (f is clamped to >=1 below) and only narrows the edge falloff.
        #   - Auto radius = ~8% of size, always > 0, so "auto" never takes the
        #     fast path.
        #   - Future optimization: vectorize the mask with numpy (build the
        #     signed-distance field and alpha channel array-wise) for ~100-1000x
        #     speedup and no per-song stall.
        if radius > 0:
            if not image.HasAlpha():
                image.InitAlpha()

            r = max(0, min(int(radius), new_w // 2, new_h // 2))
            f = max(1, int(feather))

            half_w = new_w / 2.0
            half_h = new_h / 2.0

            for y in range(new_h):
                py = (y + 0.5) - half_h

                for x in range(new_w):
                    px = (x + 0.5) - half_w

                    # Signed distance to rounded rectangle
                    qx = abs(px) - (half_w - r)
                    qy = abs(py) - (half_h - r)

                    ox = max(qx, 0.0)
                    oy = max(qy, 0.0)

                    outside_dist = (ox * ox + oy * oy) ** 0.5
                    inside_dist = min(max(qx, qy), 0.0)

                    dist = outside_dist + inside_dist - r

                    # dist <= 0 means inside rounded rectangle
                    if dist <= -f:
                        continue

                    if dist >= 0:
                        image.SetAlpha(x, y, 0)
                    else:
                        a = int(255 * (-dist / f))
                        image.SetAlpha(x, y, max(0, min(255, a)))

        bitmap = wx.Bitmap(image)
        self._cover_art_bitmap_cache[cache_key] = bitmap
        while len(self._cover_art_bitmap_cache) > self._background_bitmap_cache_limit:
            self._cover_art_bitmap_cache.popitem(last=False)
        return bitmap

    def _draw_cover_art_outline(self, dc, horizontal_position, vertical_position, width, height):
        if width <= 2 or height <= 2 or not self._supports_cover_art_outline(dc):
            return

        try:
            radius = max(2, self._get_cover_art_corner_radius(min(width, height)) - 1)
            dc.SetPen(wx.Pen(wx.Colour(255, 255, 255, self._cover_art_outline_alpha), self._cover_art_outline_width))
            dc.SetBrush(wx.TRANSPARENT_BRUSH)
            dc.DrawRoundedRectangle(int(horizontal_position), int(vertical_position), int(width), int(height), int(radius))
        except Exception:
            pass

    def drawCoverArt(self, dc, cliWidth, cliHeight, settings):
        Settings = settings

        # Get (text) size and position
        size = max(1, int(Settings['Size'] * cliHeight / 100))
        verticalPosition = int(Settings['Position'][0] * cliHeight / 100)

        # Calculate aspect-ratio-preserving dimensions for alignment
        source_image = self.displayData.currentCoverArtImage
        if source_image:
            img_w, img_h = source_image.GetWidth(), source_image.GetHeight()
            scale = min(float(size) / img_w, float(size) / img_h)
            new_w, new_h = int(img_w * scale), int(img_h * scale)
        else:
            new_w = new_h = size

        # Alignment position
        if Settings['Alignment'] == 'Left':
            horizontalPosition = int(Settings['Position'][1] * cliWidth / 100)
        elif Settings['Alignment'] == 'Right':
            horizontalPosition = int(cliWidth - (int(Settings['Position'][1] * cliWidth / 100) + new_w))
        elif Settings['Alignment'] == 'Center':
            horizontalPosition = int((cliWidth - new_w) / 2)
        else:
            raise Exception("Unknown alignment" + Settings['Alignment'])

        if self.displayData.currentCoverArtImage:
            # Cover art fades with the text during a transition: hidden while the
            # screen darkens (textAlpha == 0 in the fade-to-black "out" phase) and
            # ramped back in alongside the text. Apply the opacity through the
            # GCDC graphics context, since DrawBitmap has no global-alpha arg.
            cover_alpha = max(0.0, min(1.0, float(getattr(self.displayData, 'textAlpha', 1.0))))
            if cover_alpha <= 0.0:
                return

            graphics_context = None
            if cover_alpha < 1.0 and isinstance(dc, wx.GCDC):
                try:
                    graphics_context = dc.GetGraphicsContext()
                    graphics_context.BeginLayer(cover_alpha)
                except Exception:
                    graphics_context = None

            try:
                bitmap = self._get_cover_art_bitmap(size)
                if bitmap is None:
                    return
                dc.DrawBitmap(bitmap, int(horizontalPosition), int(verticalPosition), True)
                # Use the smaller of width/height for outline radius
                self._draw_cover_art_outline(dc, horizontalPosition, verticalPosition, new_w, new_h)
            except Exception:
                try:
                    fallback_image = self.displayData.currentCoverArtImage.Scale(new_w, new_h, wx.IMAGE_QUALITY_HIGH)
                    dc.DrawBitmap(wx.Bitmap(fallback_image), int(horizontalPosition), int(verticalPosition), True)
                except Exception:
                    pass
            finally:
                if graphics_context is not None:
                    try:
                        graphics_context.EndLayer()
                    except Exception:
                        pass

    def _wrap_long_token(self, dc, token, max_width):
        return textfit.wrap_long_token(dc.GetTextExtent, token, max_width)

    def _wrap_text_lines(self, dc, text, max_width):
        return textfit.wrap_text_lines(dc.GetTextExtent, text, max_width)

    def _get_text_width_position(self, alignment, horizontal_setting, cliWidth, text_width):
        if alignment == 'Left':
            return int(horizontal_setting * cliWidth / 100)
        if alignment == 'Right':
            return cliWidth - (int(horizontal_setting * cliWidth / 100) + text_width)
        if alignment == 'Center':
            return (cliWidth - text_width) / 2
        raise Exception("Unknown alignment" + alignment)

    def _get_render_state_snapshot(self):
        display_settings = list(getattr(self.displayData, 'currentDisplaySettings', []) or [])
        display_rows = list(getattr(self.displayData, 'currentDisplayRows', []) or [])
        render_count = min(len(display_settings), len(display_rows))
        return display_settings[:render_count], display_rows[:render_count]


    def _create_item_font(self, size_px, settings):
        try:
            return wx.Font(size_px,
                           wx.ROMAN,
                           beamSettings.FontStyleDictionary[settings['Style']],
                           beamSettings.FontWeightDictionary[settings['Weight']],
                           False,
                           settings['Font'])
        except:
            return wx.Font(size_px,
                           wx.ROMAN,
                           beamSettings.FontStyleDictionary[settings['Style']],
                           beamSettings.FontWeightDictionary[settings['Weight']],
                           False,
                           "Liberation Sans")

    def _resolve_fit_settings(self, settings, cliHeight):
        adaptive = settings.get('AdaptiveSize', 'yes') == 'yes'
        min_size_setting = int(settings.get('MinSize', 0) or 0)
        if min_size_setting <= 0:
            min_size_setting = max(1, int(round(settings['Size'] * 0.75)))
        min_size_px = max(1, int(min_size_setting * cliHeight / 100))
        max_lines = int(settings.get('MaxLines', 0) or 0)
        max_width_percent = int(settings.get('MaxWidthPercent', 0) or 0)
        return adaptive, min_size_px, max_lines, max_width_percent

    def _get_text_space_available(self, settings, cliWidth, max_width_percent):
        if max_width_percent > 0:
            return int(cliWidth * max_width_percent / 100)
        if settings['Alignment'] == 'Center':
            return int(cliWidth * self.DEFAULT_CENTER_MAX_WIDTH_PERCENT / 100)
        return int((100 - settings['Position'][1]) * cliWidth / 100)

    def _measure_at_size(self, dc, settings, size_px, text):
        dc.SetFont(self._create_item_font(size_px, settings))
        return dc.GetTextExtent(text)

    def _layout_text_item(self, dc, cliWidth, cliHeight, settings, text,
                          forced_size_px=None, forced_max_lines=None,
                          tight_spacing=False):
        base_size = int(settings['Size'] * cliHeight / 100)
        top_px = int(settings['Position'][0] * cliHeight / 100)
        adaptive, min_size_px, max_lines, max_width_percent = \
            self._resolve_fit_settings(settings, cliHeight)
        if forced_max_lines is not None:
            max_lines = forced_max_lines
        if forced_size_px is not None:
            base_size = max(1, min(base_size, int(forced_size_px)))
        min_size_px = min(min_size_px, base_size)

        text_space = self._get_text_space_available(settings, cliWidth, max_width_percent)
        text_flow = settings.get('TextFlow', 'Cut')

        def measure_at_size(size, value):
            return self._measure_at_size(dc, settings, size, value)

        def measure_at_base(value):
            return measure_at_size(base_size, value)

        if text_flow == 'Wrap':
            if max_lines <= 0:
                text_lines = textfit.wrap_text_lines(measure_at_base, text, text_space)
                size_px = base_size
            elif adaptive:
                fitted = textfit.fit_text(measure_at_size, text, text_space,
                                          base_size, min_size_px, max_lines=max_lines)
                text_lines = fitted['lines']
                size_px = fitted['size']
            else:
                text_lines = textfit.wrap_text_lines(measure_at_base, text, text_space)
                if len(text_lines) > max_lines:
                    last_line = ' '.join(line for line in text_lines[max_lines - 1:] if line)
                    text_lines = text_lines[:max_lines - 1] + [
                        textfit.ellipsize_line(measure_at_base, last_line, text_space)
                    ]
                size_px = base_size
        elif text_flow == 'Scale':
            fitted = textfit.fit_text(measure_at_size, text, int(text_space * 0.95),
                                      base_size, min_size_px, single_line=True)
            text_lines = fitted['lines']
            size_px = fitted['size']
        else:  # Cut
            if adaptive:
                fitted = textfit.fit_text(measure_at_size, text, text_space,
                                          base_size, min_size_px, single_line=True)
                text_lines = fitted['lines']
                size_px = fitted['size']
            else:
                text_lines = [textfit.ellipsize_line(measure_at_base, text, text_space)]
                size_px = base_size

        dc.SetFont(self._create_item_font(size_px, settings))
        line_height = dc.GetTextExtent('Ag')[1]
        if tight_spacing:
            line_spacing = line_height
        else:
            line_spacing = max(line_height, int(line_height * 1.1))
        extra_height = max(0, (len(text_lines) - 1) * line_spacing)

        return {
            'settings': settings,
            'text': text,
            'text_lines': text_lines,
            'size_px': size_px,
            'line_spacing': line_spacing,
            'top_px': top_px,
            'total_height': line_height + extra_height,
            'extra_height': extra_height,
        }

    def _draw_text_layout(self, dc, cliWidth, layout, extra_vertical_offset=0):
        settings = layout['settings']
        dc.SetFont(self._create_item_font(layout['size_px'], settings))

        # Set font color. Apply the transition text opacity (requires GCDC for
        # alpha text; plain DC ignores the alpha channel and just draws the
        # text fully opaque).
        text_colour = wx.Colour(eval(settings['FontColor']))
        text_alpha = max(0.0, min(1.0, float(getattr(self.displayData, 'textAlpha', 1.0))))
        if text_alpha < 1.0:
            text_colour = wx.Colour(
                text_colour.Red(),
                text_colour.Green(),
                text_colour.Blue(),
                int(round(255 * text_alpha)),
            )
        dc.SetTextForeground(text_colour)

        height_position = layout['top_px'] + int(extra_vertical_offset)
        for line_index, line in enumerate(layout['text_lines']):
            line_width, _ = dc.GetTextExtent(line)
            width_position = self._get_text_width_position(
                settings['Alignment'],
                settings['Position'][1],
                cliWidth,
                line_width,
            )
            dc.DrawText(line, int(width_position),
                        int(height_position + (line_index * layout['line_spacing'])))

        return layout['extra_height']

    def drawTextItem(self, dc, cliWidth, cliHeight, settings, text, extra_vertical_offset=0):
        layout = self._layout_text_item(dc, cliWidth, cliHeight, settings, text)
        return self._draw_text_layout(dc, cliWidth, layout, extra_vertical_offset)

    def _fit_layouts_vertically(self, dc, layouts, cliWidth, cliHeight):
        """Shrink the centered text block until it fits the vertical safe area.

        Only center-aligned items with adaptive sizing participate; left/right
        items keep their size (they still benefit because a smaller centered
        block reduces the cumulative offset pushing rows down).
        """
        safe_bottom = int(cliHeight * self.VERTICAL_SAFE_BOTTOM_RATIO)
        if textfit.block_overflow_px(layouts, safe_bottom) <= 0:
            return layouts

        def is_candidate(layout):
            settings = layout['settings']
            return (settings['Alignment'] == 'Center'
                    and settings.get('AdaptiveSize', 'yes') == 'yes'
                    and any(line.strip() for line in layout['text_lines']))

        candidate_indexes = [i for i, layout in enumerate(layouts) if is_candidate(layout)]
        if not candidate_indexes:
            return layouts

        # Multi-line (title-like) items shrink first, largest font first.
        candidate_indexes.sort(
            key=lambda i: (len(layouts[i]['text_lines']) <= 1, -layouts[i]['size_px'])
        )
        title_index = candidate_indexes[0]

        min_sizes = {}
        for i in candidate_indexes:
            _, min_size_px, _, _ = self._resolve_fit_settings(layouts[i]['settings'], cliHeight)
            min_sizes[i] = min_size_px

        overrides = {i: {} for i in candidate_indexes}

        def relayout(index):
            opts = overrides[index]
            layouts[index] = self._layout_text_item(
                dc, cliWidth, cliHeight,
                layouts[index]['settings'],
                layouts[index]['text'],
                forced_size_px=opts.get('forced_size_px'),
                forced_max_lines=opts.get('forced_max_lines'),
                tight_spacing=opts.get('tight_spacing', False),
            )

        for _ in range(self._BLOCK_FIT_MAX_ITERATIONS):
            if textfit.block_overflow_px(layouts, safe_bottom) <= 0:
                return layouts

            # Stage 1: step the first candidate still above its minimum size.
            target = None
            for i in candidate_indexes:
                if layouts[i]['size_px'] > min_sizes[i]:
                    target = i
                    break
            if target is not None:
                overrides[target]['forced_size_px'] = textfit.next_size_step(
                    layouts[target]['size_px'], min_sizes[target])
                relayout(target)
                continue

            # Stage 2: tighten line spacing on wrapped centered items.
            tightened = False
            for i in candidate_indexes:
                if not overrides[i].get('tight_spacing') and len(layouts[i]['text_lines']) > 1:
                    overrides[i]['tight_spacing'] = True
                    relayout(i)
                    tightened = True
            if tightened:
                continue

            # Stage 3: force non-title candidates to a single ellipsized line.
            forced = False
            for i in candidate_indexes:
                if i == title_index:
                    continue
                if len(layouts[i]['text_lines']) > 1 and overrides[i].get('forced_max_lines') != 1:
                    overrides[i]['forced_max_lines'] = 1
                    relayout(i)
                    forced = True
            if forced:
                continue

            # Stage 4: reduce the title's line count one line at a time.
            title_lines = len(layouts[title_index]['text_lines'])
            if title_lines > 1:
                overrides[title_index]['forced_max_lines'] = title_lines - 1
                relayout(title_index)
                continue

            break

        return layouts

    def drawItems(self, dc):

        if self.displayData.textsAreVisible == False:
            return

        cliWidth, cliHeight = self.GetClientSize()
        if not cliWidth or not cliHeight:
            return

        display_settings, display_rows = self._get_render_state_snapshot()

        # Draw images
        for j, settings in enumerate(display_settings):
            field = settings["Field"]
            if field.strip() == "%CoverArt" and display_rows[j] != "":
                self.drawCoverArt(dc, cliWidth, cliHeight, settings)

        # Draw text after/over image. Wrapped rows reserve extra vertical space
        # for later rows; the block pre-pass keeps the whole centered group
        # inside the vertical safe area.
        text_row_indexes = []
        for j, settings in enumerate(display_settings):
            field = settings["Field"]
            if field.strip() != "%CoverArt":
                text_row_indexes.append(j)

        text_row_indexes.sort(
            key=lambda index: (
                display_settings[index]['Position'][0],
                display_settings[index]['Position'][1],
                index,
            )
        )

        layouts = [
            self._layout_text_item(dc, cliWidth, cliHeight,
                                   display_settings[j], display_rows[j])
            for j in text_row_indexes
        ]
        layouts = self._fit_layouts_vertically(dc, layouts, cliWidth, cliHeight)

        offsets = textfit.compute_row_offsets(layouts)
        for layout, offset in zip(layouts, offsets):
            self._draw_text_layout(dc, cliWidth, layout, offset)


########################################################
# DRAW
########################################################
    def Draw(self, dc):
    # Get width and height of window
        cliWidth, cliHeight = self.GetClientSize()
        if not cliWidth or not cliHeight:
            return
        # GCDC.Clear() defaults to a white brush; force black so partially
        # transparent fades (Fade directly) reveal black, not white.
        dc.SetBackground(wx.Brush(wx.BLACK))
        dc.Clear()

        # Blackout is a final override: replace the normal Beam output with a
        # full black screen. The normal pipeline (moods/rules/rotation) keeps
        # running underneath; only the rendering is suppressed.
        if self.displayData.isBlackoutActive():
            self._draw_black_screen(dc, cliWidth, cliHeight)
        else:
            self.drawBackgroundBitmap(dc)
            self.drawItems(dc)

        # The temporary message renders on top of everything, including blackout.
        message_text = self.displayData.getTempMessageText()
        if message_text:
            self._draw_temp_message(dc, cliWidth, cliHeight, message_text)

    def _draw_black_screen(self, dc, cliWidth, cliHeight):
        dc.SetBackground(wx.Brush(wx.BLACK))
        dc.Clear()
        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.SetBrush(wx.Brush(wx.BLACK))
        dc.DrawRectangle(0, 0, int(cliWidth), int(cliHeight))

    def _draw_temp_message(self, dc, cliWidth, cliHeight, message_text):
        blackout_active = self.displayData.isBlackoutActive()

        # Large readable font, sized relative to the display height.
        font_size = max(12, int(cliHeight * 0.08))
        try:
            dc.SetFont(wx.Font(font_size, wx.ROMAN, wx.NORMAL, wx.BOLD, False, "Liberation Sans"))
        except Exception:
            dc.SetFont(wx.Font(font_size, wx.ROMAN, wx.NORMAL, wx.BOLD))

        lines = str(message_text).splitlines() or ['']

        line_widths = []
        line_height = dc.GetTextExtent('Ag')[1] or font_size
        line_spacing = max(line_height, int(line_height * 1.15))
        max_line_width = 0
        for line in lines:
            line_width, _ = dc.GetTextExtent(line if line else ' ')
            line_widths.append(line_width)
            max_line_width = max(max_line_width, line_width)

        total_text_height = line_spacing * len(lines)
        padding = max(20, int(font_size * 0.5))

        panel_width = min(int(cliWidth * 0.92), max_line_width + padding * 2)
        panel_height = total_text_height + padding * 2
        panel_x = int((cliWidth - panel_width) / 2)
        panel_y = int((cliHeight - panel_height) / 2)

        # Semi-transparent rounded panel behind the text. When blacked out the
        # screen is already black, so the panel is optional; draw a subtle one
        # for consistent readability.
        if blackout_active:
            panel_colour = wx.Colour(0, 0, 0, 140)
        else:
            panel_colour = wx.Colour(0, 0, 0, 180)
        try:
            dc.SetPen(wx.TRANSPARENT_PEN)
            dc.SetBrush(wx.Brush(panel_colour))
            corner_radius = max(8, int(padding * 0.6))
            dc.DrawRoundedRectangle(panel_x, panel_y, panel_width, panel_height, corner_radius)
        except Exception:
            pass

        # White text, centered horizontally and vertically.
        dc.SetTextForeground(wx.Colour(255, 255, 255, 255))
        text_y = panel_y + padding
        for line, line_width in zip(lines, line_widths):
            text_x = int((cliWidth - line_width) / 2)
            dc.DrawText(line, text_x, int(text_y))
            text_y += line_spacing


