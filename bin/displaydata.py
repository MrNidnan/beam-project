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
import time
from copy import deepcopy

import wx
import wx.lib.delayedresult

from bin.backgroundassets import resolve_background_reference
from bin.beamsettings import beamSettings
from bin.beamutils import formatMemoryUsageMb, getProcessMemoryUsageBytes
from bin.nowplayingdata import NowPlayingData
from random import randint

from bin.dialogs.preferencespanels.basicsettingspanel import BasicSettingsPanel
from bin.dialogs.preferencespanels.defaultlayoutpanel import DefaultLayoutPanel
from bin.dialogs.preferencespanels.moodspanel import MoodsPanel
from bin.dialogs.preferencespanels.rulespanel import RulesPanel
from bin.dialogs.preferencespanels.tagspreviewpanel import TagsPreviewPanel

from bin.dialogs.helpdialog import HelpDialog
from bin.dialogs import aboutdialog
# from bin.dialogs.displayframe import DisplayPanel


###################################################################
#                Build main preferences Window                    #
###################################################################

class DisplayData():

    _background_extensions = ('.jpg', '.jpeg', '.png')

    def _log_background_debug(self, message, *args):
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            logging.debug(message, *args)

    def __init__(self, mainFrame):

        # !!! callback to be removed
        self.mainFrame = mainFrame

        # Data from player
        self.nowPlayingData = NowPlayingData()

        # initially no worker started to get update finished in extract data thread
        self.currentlyUpdating = False
        self._display_time_expiry_refresh_done = False
        self._restart_display_timer_on_next_apply = False

        self.alpha = float(1.0)
        self.red = float(1.0)
        self.blue = float(1.0)
        self.green = float(1.0)

        self.currentDisplayRows = []
        self.currentDisplaySettings = []
        self.currentPlaybackStatus = ""
        self.previousMoodName = ""
        self.currentMoodName = ""

        # self.backgroundImage = wx.EmptyBitmap(800,600)
        self._legacyBackgroundBitmap = wx.Bitmap(800,600)
        # self.SetBackgroundColour(wx.BLACK)
        # Legacy compatibility data is exposed through derived accessors only.
        self.backgroundLayers = {
            'base': {},
            'overlay': {},
        }
        self._backgroundLayerState = {
            'base': {},
            'overlay': {},
        }
        self.BackgroundImageWidth, self.BackgroundImageHeight = self._legacyBackgroundBitmap.GetSize()
        # "no", "linear", "random"
        # ??? wird wo gesetzt und gespeichert
        self.RotateBackground = 'no'

        # trigger
        self.triggerResizeBackground = True
        self.textsAreVisible = False
        self.FadeDirection = 'In'
        self.RotateBackgroundTrigger = False

        # Manual display overrides. Final overlays on top of the normal
        # pipeline; never persisted and always reset to inactive on startup.
        self.blackoutEnabled = False
        self.tempMessageText = None
        self.tempMessageUntil = None

        ########################## END OF INITIALIZATION #########################

    ########################################################
    # Manual display overrides (blackout + temporary message)
    ########################################################
    def setBlackout(self, enabled):
        self.blackoutEnabled = bool(enabled)

    def toggleBlackout(self):
        self.blackoutEnabled = not bool(getattr(self, 'blackoutEnabled', False))
        return self.blackoutEnabled

    def isBlackoutActive(self):
        return bool(getattr(self, 'blackoutEnabled', False))

    def showTempMessage(self, text, duration_seconds):
        self.tempMessageText = text
        try:
            duration_seconds = float(duration_seconds)
        except (TypeError, ValueError):
            duration_seconds = 0
        self.tempMessageUntil = time.time() + max(0, duration_seconds)

    def clearTempMessage(self):
        self.tempMessageText = None
        self.tempMessageUntil = None

    def isTempMessageActive(self):
        if not self.tempMessageText:
            return False
        if self.tempMessageUntil is None:
            return False
        if time.time() >= self.tempMessageUntil:
            return False
        return True

    def getTempMessageText(self):
        if self.isTempMessageActive():
            return self.tempMessageText
        return None

    def getTempMessageSecondsRemaining(self):
        if not self.isTempMessageActive():
            return 0
        return max(0, self.tempMessageUntil - time.time())

    def getLegacyBackgroundPath(self):
        return DisplayData.getEffectiveTransitionBackgroundPath(self)

    def hasLegacyBackgroundPath(self):
        return bool(self.getLegacyBackgroundPath())

    def getLegacyBackgroundBitmap(self):
        legacy_background_bitmap = getattr(self, '_legacyBackgroundBitmap', None)
        return legacy_background_bitmap

    def _set_legacy_background_bitmap(self, bitmap):
        self._legacyBackgroundBitmap = bitmap
        self.BackgroundImageWidth, self.BackgroundImageHeight = bitmap.GetSize()

    def _get_effective_transition_layer_state(self):
        active_layer_name = self._get_active_background_layer_name()
        layer_state = (getattr(self, '_backgroundLayerState', {}) or {}).get(active_layer_name, {})
        if layer_state.get('available'):
            return layer_state

        background_layers = getattr(self, 'backgroundLayers', {}) or {}
        layer_state = background_layers.get(active_layer_name, {})
        if layer_state.get('available'):
            return layer_state

        return {}

    def getEffectiveTransitionBackgroundPath(self):
        layer_state = DisplayData._get_effective_transition_layer_state(self)
        if layer_state.get('kind') == 'color':
            return layer_state.get('canonicalReference') or layer_state.get('reference') or None
        return layer_state.get('currentPath') or layer_state.get('sourcePath') or None

    def hasRenderableLayeredBackground(self):
        for layer_state in (getattr(self, '_backgroundLayerState', {}) or {}).values():
            if layer_state.get('available') and (
                layer_state.get('kind') == 'color'
                or layer_state.get('currentPath')
                or layer_state.get('sourcePath')
            ):
                return True

        for layer_state in (getattr(self, 'backgroundLayers', {}) or {}).values():
            if layer_state.get('available') and (
                layer_state.get('kind') == 'color'
                or layer_state.get('currentPath')
                or layer_state.get('sourcePath')
            ):
                return True

        return False

    def shouldUseLegacyBackgroundFallback(self):
        return not DisplayData.hasRenderableLayeredBackground(self)

    def _get_background_candidates(self, background_path):
        if not background_path:
            return (None, [], None)

        current_file = None
        scan_path = background_path
        if os.path.isfile(background_path):
            scan_path, current_file = os.path.split(background_path)

        if not os.path.isdir(scan_path):
            return (None, [], current_file)

        backgrounds = sorted(
            [
                entry for entry in os.listdir(scan_path)
                if os.path.isfile(os.path.join(scan_path, entry))
                and os.path.splitext(entry)[1].lower() in self._background_extensions
            ]
        )
        return (scan_path, backgrounds, current_file)

    def _resolve_background_path(self, background_path, prefer_random=False):
        if not background_path:
            return None

        resolved_background = resolve_background_reference(background_path)
        resolved_path = resolved_background['absolutePath'] or os.path.normpath(str(background_path))
        if os.path.isfile(resolved_path):
            return resolved_path

        background_dir, backgrounds, _ = self._get_background_candidates(resolved_path)
        if not backgrounds:
            return resolved_path

        if prefer_random and len(backgrounds) > 1:
            position = randint(0, len(backgrounds) - 1)
        else:
            position = 0
        return os.path.join(background_dir, backgrounds[position])

    def _load_background(self, background_path=None):
        background_source = background_path
        if background_source is None:
            background_source = DisplayData.getEffectiveTransitionBackgroundPath(self)

        resolved_path = self._resolve_background_path(
            background_source,
            prefer_random=self.RotateBackground == 'random'
        )
        if resolved_path is None:
            DisplayData._log_background_debug(
                self,
                "DisplayData background load skipped: source=%s memory=%s",
                background_source,
                formatMemoryUsageMb(getProcessMemoryUsageBytes()),
            )
            return

        previous_path = self.modifiedBitmap if isinstance(getattr(self, 'modifiedBitmap', None), str) else DisplayData.getLegacyBackgroundPath(self)
        previous_size = None
        previous_background_bitmap = DisplayData.getLegacyBackgroundBitmap(self)
        if previous_background_bitmap is not None:
            try:
                previous_size = previous_background_bitmap.GetSize()
            except Exception:
                previous_size = None

        DisplayData._log_background_debug(
            self,
            "DisplayData background load start: source=%s resolved=%s previous=%s previousSize=%s memory=%s",
            background_source,
            resolved_path,
            previous_path,
            previous_size,
            formatMemoryUsageMb(getProcessMemoryUsageBytes()),
        )

        log_silencer = wx.LogNull()
        try:
            previous_background_image = previous_background_bitmap
            DisplayData._set_legacy_background_bitmap(self, wx.Bitmap(resolved_path))
        finally:
            del log_silencer
        if previous_background_image is not None:
            DisplayData._log_background_debug(
                self,
                "DisplayData background bitmap reference released: previous=%s memory=%s",
                previous_path,
                formatMemoryUsageMb(getProcessMemoryUsageBytes()),
            )
            del previous_background_image
        self.modifiedBitmap = resolved_path
        DisplayData._log_background_debug(
            self,
            "DisplayData background load complete: current=%s size=%sx%s memory=%s",
            resolved_path,
            self.BackgroundImageWidth,
            self.BackgroundImageHeight,
            formatMemoryUsageMb(getProcessMemoryUsageBytes()),
        )

    def _build_layer_runtime_state(self, layer_definition, previous_state=None):
        layer_definition = deepcopy(layer_definition or {})
        previous_state = previous_state or {}

        available = bool(layer_definition.get('available'))
        kind = str(layer_definition.get('kind', '')).lower()
        source_path = layer_definition.get('sourcePath', '')
        rotate_mode = str(layer_definition.get('rotate', 'no')).lower()
        rotate_timer = int(layer_definition.get('rotateTimer', 0) or 0)

        layer_state = deepcopy(layer_definition)
        layer_state['currentPath'] = ''
        layer_state['nextRotationAt'] = None

        if not available:
            return layer_state

        if kind == 'color':
            layer_state['currentPath'] = layer_definition.get('canonicalReference') or layer_definition.get('reference', '')
            return layer_state

        if not source_path:
            return layer_state

        same_source = (
            previous_state.get('sourcePath', '') == source_path
            and str(previous_state.get('rotate', 'no')).lower() == rotate_mode
            and int(previous_state.get('rotateTimer', 0) or 0) == rotate_timer
        )

        if same_source and previous_state.get('currentPath'):
            layer_state['currentPath'] = previous_state.get('currentPath', '')
            layer_state['nextRotationAt'] = previous_state.get('nextRotationAt')
        else:
            layer_state['currentPath'] = self._resolve_background_path(
                source_path,
                prefer_random=rotate_mode == 'random',
            ) or ''
            if rotate_mode in ('linear', 'random') and rotate_timer > 0:
                layer_state['nextRotationAt'] = time.time() + rotate_timer

        if rotate_mode not in ('linear', 'random') or rotate_timer <= 0:
            layer_state['nextRotationAt'] = None

        return layer_state

    def _refresh_background_layer_state(self):
        previous_states = self._backgroundLayerState
        refreshed_states = {}
        for layer_name in ('base', 'overlay'):
            refreshed_states[layer_name] = self._build_layer_runtime_state(
                self.backgroundLayers.get(layer_name, {}),
                previous_states.get(layer_name, {}),
            )

        self._backgroundLayerState = refreshed_states

        for layer_name, layer_state in refreshed_states.items():
            self.backgroundLayers[layer_name] = deepcopy(layer_state)

        self._sync_active_background_state()

    def _get_active_background_layer_name(self):
        overlay_state = self._backgroundLayerState.get('overlay', {})
        if overlay_state.get('available') and str(overlay_state.get('mode', '')).lower() == 'replace':
            return 'overlay'
        return 'base'

    def _sync_active_background_state(self):
        active_layer_name = self._get_active_background_layer_name()
        active_layer = self._backgroundLayerState.get(active_layer_name, {})
        self.RotateBackground = str(active_layer.get('rotate', 'no')).lower()
        self.rotatebackgroundseconds = int(active_layer.get('rotateTimer', 0) or 0)

    def _get_next_rotation_delay_ms(self):
        next_rotation_at = None
        now = time.time()
        for layer_state in self._backgroundLayerState.values():
            if not layer_state.get('available'):
                continue
            next_rotation = layer_state.get('nextRotationAt')
            if next_rotation is None:
                continue
            if next_rotation_at is None or next_rotation < next_rotation_at:
                next_rotation_at = next_rotation

        if next_rotation_at is None:
            return None

        return max(1, int(max(0.0, next_rotation_at - now) * 1000))

    def _update_background_rotation_timer(self):
        next_delay_ms = self._get_next_rotation_delay_ms()
        if next_delay_ms is None:
            self.mainFrame.RotateBackgroundTimer.Stop()
            return

        self.mainFrame.RotateBackgroundTimer.Start(next_delay_ms, oneShot=True)

    def _advance_background_layer(self, layer_name):
        layer_state = self._backgroundLayerState.get(layer_name, {})
        if not layer_state.get('available'):
            return False

        rotate_mode = str(layer_state.get('rotate', 'no')).lower()
        rotate_timer = int(layer_state.get('rotateTimer', 0) or 0)
        if rotate_mode not in ('linear', 'random') or rotate_timer <= 0:
            layer_state['nextRotationAt'] = None
            return False

        scan_path = layer_state.get('currentPath') or layer_state.get('sourcePath', '')
        path, backgrounds, current_file = self._get_background_candidates(scan_path)
        if not backgrounds:
            layer_state['nextRotationAt'] = time.time() + rotate_timer
            return False

        try:
            position = backgrounds.index(current_file)
        except ValueError:
            position = -1

        if rotate_mode == 'linear':
            new_position = (position + 1) % len(backgrounds)
        else:
            if len(backgrounds) == 1:
                new_position = 0
            else:
                new_position = randint(0, len(backgrounds) - 1)
                if new_position == position:
                    new_position = (position + 1) % len(backgrounds)

        layer_state['currentPath'] = os.path.join(path, backgrounds[new_position])
        layer_state['nextRotationAt'] = time.time() + rotate_timer
        self.backgroundLayers[layer_name] = deepcopy(layer_state)
        return True



    ########################################################
    # Update data - Executed from mainFrame to bottom with exception if preferences changed
    ########################################################

    # Copy display data from nowplayingdata
    # gets continously called by a timer in MainFrame.__init__()
    def updateData(self, event=wx.EVT_TIMER):
        try:
            # copy playing data to current
            # ??? and below again
            # Only copy rows and cover art from nowPlayingData when not in expired state.
            # In expired state, _apply_expired_display_state() owns these fields; copying
            # nowPlayingData here would overwrite them with stale data from the previously
            # active (expired) timed mood.
            if not self.nowPlayingData.isDisplayTimeExpired():
                self.currentDisplayRows = self.nowPlayingData.DisplayRows
                self.currentCoverArtImage = self.nowPlayingData.currentCoverArtImage
            self.currentPlaybackStatus = self.nowPlayingData.StatusMessage
            self.previousPlaybackStatus = self.nowPlayingData.PreviousPlaybackStatus

            if not self.currentlyUpdating:
                self.currentlyUpdating = True
                # asynchronous transmission of data from a worker thread to the main thread
                # calls readDataThread() in separate thread and then getDataFinished()
                wx.lib.delayedresult.startWorker(self.getDataFinished, self.readDataThread)
            # ??? Why resets updateDate it's own timer
            # It will create a new one, indeed
            # self.updateDataTimer()  # Reset the timer
        except Exception as e:
            logging.error(e, exc_info=True)


    #
    # Read song info from the modules
    # in a thread by updateData()
    #
    def readDataThread(self):
        try:
            self.nowPlayingData.readData(beamSettings)
            # sets playlistChanged
        except Exception as e:
            logging.error(e, exc_info=True)

    #
    # Check if the playlist got changed
    # and in case process that
    # in the MainThread
    #
    def getDataFinished(self, result):
        try:
            self.currentlyUpdating = False
            # playlistChabnged set by NowPlayingData.readData()
            if self.nowPlayingData.playlistChanged:
                self._display_time_expiry_refresh_done = False
                # Only update if playlist has changed
                self.processData()

            if self.nowPlayingData.isDisplayTimeExpired() and not self._display_time_expiry_refresh_done:
                self._apply_expired_display_state()
                # erase
                self.mainFrame.refreshDisplay()
                self._display_time_expiry_refresh_done = True

        except Exception as e:
            logging.error(e, exc_info=True)

    def _apply_keep_existing_background(self, new_background_layers):
        # "Keep existing" mood backgrounds inherit whatever background is already on
        # screen instead of replacing it (e.g. a timed message mood). Only the
        # readability blur/dim settings from the new mood are carried over.
        new_background_layers = new_background_layers or {'base': {}, 'overlay': {}}
        new_base_layer = new_background_layers.get('base') or {}
        if not new_base_layer.get('keepExisting'):
            return new_background_layers

        previous_base_layer = deepcopy((getattr(self, 'backgroundLayers', {}) or {}).get('base') or {})
        if not previous_base_layer.get('available'):
            # Nothing to inherit yet; fall back to the mood's own background.
            return new_background_layers

        previous_base_layer['keepExisting'] = True
        previous_base_layer['improveReadability'] = bool(new_base_layer.get('improveReadability', False))
        previous_base_layer['readability'] = int(new_base_layer.get('readability', 0) or 0)

        merged_background_layers = dict(new_background_layers)
        merged_background_layers['base'] = previous_base_layer
        return merged_background_layers

    def _apply_expired_display_state(self):
        moods = beamSettings.getMoods()
        if not moods:
            self.currentMoodName = ''
            self.currentDisplaySettings = []
            self.currentDisplayRows = []
            self.backgroundLayers = {
                'base': {},
                'overlay': {},
            }
            self._refresh_background_layer_state()
            return

        expired_display_state = self.nowPlayingData.build_display_state_for_mood(beamSettings, moods[0])
        self.currentMoodName = expired_display_state['currentMoodName']
        self.currentDisplaySettings = expired_display_state['displaySettings']
        self.currentDisplayRows = expired_display_state['displayRows']
        self.currentCoverArtImage = expired_display_state['coverArtImage']
        self.backgroundLayers = self._apply_keep_existing_background(expired_display_state['backgroundLayers'])
        self._refresh_background_layer_state()

    def _update_status_text(self):
        update_status_bar = getattr(self.mainFrame, 'updateStatusBar', None)
        if callable(update_status_bar):
            update_status_bar()
            return
        self.mainFrame.SetStatusText(
            beamSettings.getSelectedModuleName() + ": " + self.currentPlaybackStatus + " - Mood: " + self.currentMoodName
        )

    #
    # called in MainTread
    # starts Thread for processDataThread()
    # and then calls __updateMood()
    #
    def processData(self):
        try:
            wx.lib.delayedresult.startWorker(self.__updateMood, self.processDataThread)
        except Exception as e:
            logging.error(e, exc_info=True)
            pass

    # Process data in own thread
    def processDataThread(self):
        try:
            self.nowPlayingData.processData(beamSettings)
        except Exception as e:
            logging.error(e, exc_info=True)
            pass

    def _apply_processed_mood_state(self):
        self.currentDisplayRows = self.nowPlayingData.DisplayRows
        self.currentCoverArtImage = self.nowPlayingData.currentCoverArtImage
        self.currentPlaybackStatus = self.nowPlayingData.StatusMessage

        self.previousMoodName = deepcopy(self.currentMoodName)
        self.currentMoodName = self.nowPlayingData.CurrentMoodName
        self.currentDisplaySettings = self.nowPlayingData.DisplaySettings
        self.backgroundLayers = self._apply_keep_existing_background(deepcopy(self.nowPlayingData.BackgroundLayers))
        self._refresh_background_layer_state()

        self._update_status_text()

        if self.previousMoodName != self.currentMoodName:
            self.startTransition('MoodChange')
        else:
            self.startTransition('SongChange')

    def _apply_current_display_state(self):
        if self._restart_display_timer_on_next_apply:
            self.nowPlayingData.restartDisplayTimer()
            self._restart_display_timer_on_next_apply = False

        self.currentPlaybackStatus = self.nowPlayingData.StatusMessage

        if self.nowPlayingData.isDisplayTimeExpired():
            self._apply_expired_display_state()
            self._display_time_expiry_refresh_done = True
            self._update_status_text()
            self._update_background_rotation_timer()
            return

        self._display_time_expiry_refresh_done = False
        self._apply_processed_mood_state()
        self._update_background_rotation_timer()

    def requestDisplayTimerRestart(self):
        self._restart_display_timer_on_next_apply = True
        self._display_time_expiry_refresh_done = False

    #toggling an unused mood: no timer restart
    #toggling a mood that actually becomes the applied mood: restart only that timed mood
    def refreshProcessedStateImmediately(self):
        try:
            previous_mood_name = self.nowPlayingData.CurrentMoodName
            self.nowPlayingData.processData(beamSettings)

            next_mood = self.nowPlayingData.currentMood
            try:
                next_display_timer = int(next_mood.get('DisplayTimer', 0)) if next_mood else 0
            except (TypeError, ValueError, AttributeError):
                next_display_timer = 0

            if self.nowPlayingData.CurrentMoodName != previous_mood_name and next_display_timer > 0:
                self.nowPlayingData.restartDisplayTimer()

            self._apply_current_display_state()
        except Exception as e:
            logging.error(e, exc_info=True)
            pass

    # Running in MainThread
    # After processing data
    # update the mood
    # and refresh the display
    def __updateMood(self, result):
        try:
            self._apply_current_display_state()
            self.mainFrame.refreshDisplay()
        except Exception as e:
            logging.error(e, exc_info=True)
            pass



    ########################################################
    #                                                      #
    #                                                      #
    #                  TRANSITIONS                         #
    #                                                      #
    #                                                      #
    ########################################################
    #
    # TransitionType:
    #    MoodChange -> Change the mood and song (mood transition type)
    #    SongChange -> change text (direct fade or no transition
    def startTransition(self, TransitionType):

        if TransitionType == 'MoodChange':
            # LOAD NEW SETTINGS FOR NEW MOOD
            # Stop RotateBackground timer if it is running
            self.mainFrame.RotateBackgroundTimer.Stop()
            # Select Mood transition and start changing
            if beamSettings.getMoodTransition() == 'Fade directly':
                self.currentTransition = 'FadeDirect'
                self.initiateTransition()
            elif beamSettings.getMoodTransition() == 'Fade to black':
                # Always begin with the darken (Out) phase. FadeDirection persists
                # across transitions, so without this a first or interrupted
                # fade-to-black can start in 'In' and skip darkening entirely.
                self.FadeDirection = 'Out'
                self.currentTransition = 'FadeToBlack'
                self.initiateTransition()
            else:
                self.currentTransition = ''
                self.initiateTransition()

            self._update_background_rotation_timer()

            return

        if TransitionType == 'SongChange':
            if beamSettings.getMoodTransition() == 'No transition':
                self.currentTransition = ''
                self.initiateTransition()
            else:
                self.currentTransition = 'FadeDirect'
                self.initiateTransition()

            return

    ########################################################
    # INITIATE TRANSITION
    ########################################################
    def initiateTransition(self):

        # Cancel any in-flight fade so two transitions cannot drive the timer
        # at once and leave channel/alpha state half-applied.
        self.mainFrame.TransitionTimer.Stop()

        # MoodTransitionSpeed is the total fade duration in ms (slider 500..5000).
        # Run the timer at a fixed frame rate and derive the per-frame step from
        # the duration, instead of tying the timer interval to the speed (which
        # made the slow end fire at ~200 Hz and thrash the UI thread).
        TRANSITION_FRAME_MS = 33  # ~30 fps
        duration_ms = max(1, int(beamSettings.getMoodTransitionSpeed()))
        self.transitionSpeed = TRANSITION_FRAME_MS
        self.delta = float(TRANSITION_FRAME_MS) / float(duration_ms)

        # FADE DIRECTLY
        if self.currentTransition == 'FadeDirect':

            self.alpha = float(0.0)
            # Reset the colour multipliers: a FadeDirect only animates alpha, so
            # any darkening left over from an interrupted FadeToBlack must be
            # cleared or it sticks permanently and the display keeps getting
            # darker with no way to recover.
            self.red = float(1.0)
            self.green = float(1.0)
            self.blue = float(1.0)
            # Load the legacy fallback only when no layered background is available.
            if self.shouldUseLegacyBackgroundFallback() and self.getEffectiveTransitionBackgroundPath() is not None:
                self._load_background()

            # Set triggers
            self.triggerResizeBackground = True
            self.textsAreVisible = True

            # start the timer for the transition
            self.mainFrame.TransitionTimer.Start(self.transitionSpeed)
            return

        # FADE TO BLACK
        if self.currentTransition == 'FadeToBlack':
            if self.FadeDirection == 'Out':
                self.textsAreVisible = False
                self.red = float(1.0)
                self.green = float(1.0)
                self.blue = float(1.0)
                self.alpha = float(1.0)
                # Fade out
                self.mainFrame.TransitionTimer.Start(self.transitionSpeed)

            else:
                # Load the legacy fallback only when no layered background is available.
                if self.shouldUseLegacyBackgroundFallback():
                    self._load_background()
                # Set triggers
                self.triggerResizeBackground = True
                self.textsAreVisible = True

                self.red = float(0.0)
                self.green = float(0.0)
                self.blue = float(0.0)
                self.alpha = float(1.0)

                self.mainFrame.TransitionTimer.Start(self.transitionSpeed)
                return

        else:
            self.currentTransition = ''
            self.switchBackground()

    ########################################################
    # No transition
    ########################################################
    def switchBackground(self):

        # No transition: snap to a fully opaque, un-darkened background so leftover
        # fade state cannot persist.
        self.red = float(1.0)
        self.green = float(1.0)
        self.blue = float(1.0)
        self.alpha = float(1.0)
        self.triggerResizeBackground = True
        if self.shouldUseLegacyBackgroundFallback():
            self._load_background()
        self.textsAreVisible = True
        self.mainFrame.refreshDisplay()

    ########################################################
    # TIMER - USED for Fade directly and Fade to black
    ########################################################
    def transition(self, event):
        if self.currentTransition == 'FadeDirect':
            self.FadeImage()
            return
        if self.currentTransition == 'FadeToBlack' and self.FadeDirection == 'Out':
            self.FadeToBlackImage()
            return
        if self.currentTransition == 'FadeToBlack' and self.FadeDirection == 'In':
            self.FadeBackImage()
            return

    ########################################################
    # Fade directly
    ########################################################
    def FadeImage(self):
        self.alpha += self.delta
        if self.alpha >= 1:
            self.alpha = 1.0
            self.mainFrame.TransitionTimer.Stop()
            self.RotateBackgroundTrigger = False
        self.mainFrame.refreshDisplay()

    ########################################################
    # Fade To black - 2 functions (IN and OUT)
    ########################################################
    def FadeToBlackImage(self):

        self.red -= 2 * self.delta
        self.green -= 2 * self.delta
        self.blue -= 2 * self.delta

        if self.red >= 0 and self.red <= 1:
            self.triggerResizeBackground = True
            self.textsAreVisible = False
            self.mainFrame.refreshDisplay()
        else:
            self.red = float(0.0)
            self.green = float(0.0)
            self.blue = float(0.0)
            self.direction = 'in'  # Change fading direction
            self.mainFrame.TransitionTimer.Stop()
            self.mainFrame.refreshDisplay()

            self.FadeDirection = 'In'
            self.currentTransition = 'FadeToBlack'
            self.initiateTransition()

    def FadeBackImage(self):
        self.red += self.delta
        self.green += self.delta
        self.blue += self.delta

        if self.red >= 0 and self.red <= 1:
            self.triggerResizeBackground = True
            self.mainFrame.refreshDisplay()
        else:
            self.red = float(1.0)
            self.green = float(1.0)
            self.blue = float(1.0)
            self.FadeDirection = 'Out'
            self.mainFrame.TransitionTimer.Stop()
            self.mainFrame.refreshDisplay()

    #
    # Gets triggered by a timer event in MainFrame
    def rotateBackground(self, event=wx.EVT_TIMER):
        rotated_any_layer = False
        now = time.time()
        for layer_name in ('base', 'overlay'):
            layer_state = self._backgroundLayerState.get(layer_name, {})
            next_rotation_at = layer_state.get('nextRotationAt')
            if next_rotation_at is None or next_rotation_at > now:
                continue
            if self._advance_background_layer(layer_name):
                rotated_any_layer = True

        self._sync_active_background_state()
        self._update_background_rotation_timer()

        if not rotated_any_layer:
            return

        # Start the transition
        if beamSettings.getMoodTransition() == 'No transition':
            self.currentTransition = ''
            self.initiateTransition()
        else:
            self.currentTransition = 'FadeDirect'
            self.initiateTransition()



