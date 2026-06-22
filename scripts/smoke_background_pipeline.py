#!/usr/bin/env python

import json
import os
import platform
import sys
import tempfile
from collections import OrderedDict
from types import SimpleNamespace
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


PNG_BYTES = (
    b'\x89PNG\r\n\x1a\n'
    b'\x00\x00\x00\rIHDR'
    b'\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde'
    b'\x00\x00\x00\x0cIDATx\x9cc``\x00\x00\x00\x04\x00\x01\xf6\x178U'
    b'\x00\x00\x00\x00IEND\xaeB`\x82'
)


def write_png(path):
    Path(path).write_bytes(PNG_BYTES)


def load_default_config():
    config_path = ROOT / 'resources' / 'json' / 'beamconfig.json'
    with config_path.open('r', encoding='utf-8') as handle:
        return json.load(handle)


class FakeUniverse:
    def __init__(self):
        self.colours = []

    def setAllFixtureColours(self, colours):
        self.colours = list(colours)


class FakeSettings:
    def __init__(self, config_data):
        self.config_data = config_data

    def getRules(self):
        return self.config_data['Rules']

    def getMoods(self):
        return self.config_data['Moods']

    def getArtistBackgroundsEnabled(self):
        return str(self.config_data['ArtistBackgrounds'].get('Enabled', 'False')).lower() == 'true'

    def getArtistBackgroundsUseCoverArt(self):
        return str(self.config_data['ArtistBackgrounds'].get('UseCoverArt', 'False')).lower() == 'true'

    def getArtistBackgrounds(self):
        return self.config_data['ArtistBackgrounds']

    def getArtistBackgroundMappings(self):
        return self.config_data['ArtistBackgrounds'].get('Mappings', [])

    def getSelectedModuleName(self):
        return self.config_data.get('Module', '')

    def getCoverArtCornerRadius(self):
        return 'auto'

    def getCoverArtFeatherAmount(self):
        return 'auto'

    def getCoverArtOutlineEnabled(self):
        return True

    def getCoverArtOutlineAlpha(self):
        return 56

    def getCoverArtOutlineWidth(self):
        return 1

    # PlayedHistory interface expected by NowPlayingData.processData.
    # Smoke tests here focus on background pipeline behavior, so keep history
    # logging disabled to avoid unrelated file I/O and interface noise.
    def getPlayedHistoryEnabled(self):
        return False

    def getPlayedHistoryFolder(self):
        return ''

    def getPlayedHistoryTxtEnabled(self):
        return False

    def getPlayedHistoryCsvEnabled(self):
        return False

    def getPlayedHistoryM3u8Enabled(self):
        return False


def build_test_roots(temp_root):
    beam_home = Path(temp_root) / 'beam-home'
    beam_resources = beam_home / 'resources'
    beam_config = Path(temp_root) / 'beam-config'
    return beam_home, beam_resources, beam_config


def test_background_asset_roundtrip(temp_root):
    from bin import backgroundassets

    beam_home, beam_resources, beam_config = build_test_roots(temp_root)
    builtin_background = beam_resources / 'backgrounds' / 'builtin-test.png'
    external_background = Path(temp_root) / 'external-art.png'
    folder_source = Path(temp_root) / 'rotation-source'

    builtin_background.parent.mkdir(parents=True, exist_ok=True)
    folder_source.mkdir(parents=True, exist_ok=True)
    write_png(builtin_background)
    write_png(external_background)
    write_png(folder_source / 'frame-a.png')
    write_png(folder_source / 'frame-b.jpg')
    (folder_source / 'ignore.txt').write_text('not an image', encoding='utf-8')

    with patch('bin.backgroundassets.getBeamHomePath', return_value=str(beam_home)), \
         patch('bin.backgroundassets.getBeamResourcesPath', return_value=str(beam_resources)), \
         patch('bin.backgroundassets.getBeamConfigPath', return_value=str(beam_config)):
        normalized = backgroundassets.normalize_background_reference('resources\\backgrounds\\builtin-test.png')
        assert normalized == 'asset:builtin/backgrounds/builtin-test.png'

        parsed = backgroundassets.parse_background_reference('asset:user/backgrounds/moods/test.png')
        assert parsed['kind'] == 'asset'
        assert parsed['scope'] == 'user'
        assert parsed['relativePath'] == 'backgrounds/moods/test.png'

        absolute_reference = backgroundassets.normalize_background_reference(str(external_background))
        assert absolute_reference == os.path.normpath(str(external_background))

        try:
            backgroundassets.normalize_background_reference('asset:user/backgrounds/../oops.png')
        except ValueError:
            pass
        else:
            raise AssertionError('Expected path traversal reference to raise ValueError')

        builtin_reference = backgroundassets.to_persisted_background_reference(str(builtin_background), 'moods')
        assert builtin_reference == 'asset:builtin/backgrounds/builtin-test.png'

        import_result = backgroundassets.import_background_asset(str(external_background), 'moods')
        assert import_result['status'] == 'imported'
        assert import_result['reference'].startswith('asset:user/backgrounds/moods/')
        assert Path(import_result['absolutePath']).is_file()

        reused_result = backgroundassets.import_background_asset(str(external_background), 'moods')
        assert reused_result['status'] == 'reused'
        assert reused_result['reference'] == import_result['reference']

        folder_result = backgroundassets.import_background_asset(str(folder_source), 'orchestras')
        assert folder_result['status'] == 'imported'
        assert folder_result['reference'].startswith('asset:user/backgrounds/orchestras/')
        imported_files = sorted(path.name for path in Path(folder_result['absolutePath']).iterdir())
        assert imported_files == ['frame-a.png', 'frame-b.jpg']

        resolved_import = backgroundassets.resolve_background_reference(import_result['reference'])
        assert resolved_import['exists'] is True
        assert resolved_import['scope'] == 'user'


def test_nowplaying_background_layers_and_snapshot(temp_root):
    from bin.network.schema import snapshot_from_display_data
    from bin.nowplayingdata import NowPlayingData
    from bin.songclass import SongObject

    beam_home, beam_resources, beam_config = build_test_roots(temp_root)
    base_background = beam_resources / 'backgrounds' / 'base-mood.png'
    overlay_background = beam_config / 'backgrounds' / 'orchestras' / 'di-sarli.png'
    base_background.parent.mkdir(parents=True, exist_ok=True)
    overlay_background.parent.mkdir(parents=True, exist_ok=True)
    write_png(base_background)
    write_png(overlay_background)

    config_data = load_default_config()
    config_data['Module'] = 'VirtualDJ'
    config_data['Moods'] = [deepcopy(config_data['Moods'][0])]
    config_data['Moods'][0]['Name'] = 'Default'
    config_data['Moods'][0]['Background'] = 'asset:builtin/backgrounds/base-mood.png'
    config_data['Moods'][0]['RotateBackground'] = 'linear'
    config_data['Moods'][0]['RotateTimer'] = 30
    config_data['ArtistBackgrounds'] = {
        'Enabled': 'True',
        'StorageRoot': 'backgrounds/orchestras',
        'MatchField': '%AlbumArtist',
        'FallbackField': '%Artist',
        'DefaultMode': 'blend',
        'DefaultOpacity': 35,
        'Mappings': [
            {
                'Name': 'Carlos Di Sarli',
                'Field': '%AlbumArtist',
                'Operator': 'is',
                'Value': 'Carlos Di Sarli',
                'Background': 'asset:user/backgrounds/orchestras/di-sarli.png',
                'Mode': 'blend',
                'Opacity': 40,
                'RotateBackground': 'random',
                'RotateTimer': 45,
                'Active': 'yes',
            }
        ],
    }

    current_settings = FakeSettings(config_data)
    song = SongObject(
        p_artist='Fallback Artist',
        p_album='Instrumental Favorites',
        p_title='Bahia Blanca',
        p_genre='Tango',
        p_albumArtist='Carlos Di Sarli',
        p_filePath='C:/Music/Bahia Blanca.flac',
    )

    now_playing = NowPlayingData()
    now_playing.currentPlaylist = [song]
    now_playing.LastRead = [SongObject()]
    now_playing.PlaybackStatus = 'Playing'
    now_playing.StatusMessage = 'Playing'
    now_playing.playlistchangetime = 12

    fake_u1 = FakeUniverse()
    fake_u2 = FakeUniverse()
    with patch('bin.backgroundassets.getBeamHomePath', return_value=str(beam_home)), \
         patch('bin.backgroundassets.getBeamResourcesPath', return_value=str(beam_resources)), \
         patch('bin.backgroundassets.getBeamConfigPath', return_value=str(beam_config)), \
            patch.object(__import__('bin.nowplayingdata', fromlist=['beamSettings']).beamSettings, '_Universe1', fake_u1, create=True), \
            patch.object(__import__('bin.nowplayingdata', fromlist=['beamSettings']).beamSettings, '_Universe2', fake_u2, create=True):
        now_playing.processData(current_settings)

    base_layer = now_playing.BackgroundLayers['base']
    overlay_layer = now_playing.BackgroundLayers['overlay']
    assert base_layer['available'] is True
    assert overlay_layer['available'] is True
    assert base_layer['sourcePath'].endswith(os.path.join('resources', 'backgrounds', 'base-mood.png'))
    assert overlay_layer['sourcePath'].endswith(os.path.join('backgrounds', 'orchestras', 'di-sarli.png'))
    assert overlay_layer['mode'] == 'blend'
    assert overlay_layer['opacity'] == 40
    assert overlay_layer['matchedField'] == '%AlbumArtist'
    assert now_playing.BackgroundPath == base_layer['sourcePath']
    assert now_playing.RotateBackground == 'linear'
    assert now_playing.rotatebackgroundseconds == 30
    assert fake_u1.colours
    assert fake_u2.colours

    display_data = SimpleNamespace(
        nowPlayingData=now_playing,
        currentPlaybackStatus='Playing',
        previousPlaybackStatus='Stopped',
        currentMoodName=now_playing.CurrentMoodName,
        getLegacyBackgroundPath=lambda: now_playing.BackgroundPath,
        backgroundLayers=deepcopy(now_playing.BackgroundLayers),
        currentDisplayRows=list(now_playing.DisplayRows),
        currentDisplaySettings=deepcopy(now_playing.DisplaySettings),
    )
    snapshot = snapshot_from_display_data(display_data, current_settings)
    assert snapshot['background']['available'] is True
    assert snapshot['background']['sourcePath'] == now_playing.BackgroundPath
    assert snapshot['background']['url'] == '/media/background/current'
    assert snapshot['background']['base']['canonicalReference'] == 'asset:builtin/backgrounds/base-mood.png'
    assert snapshot['background']['base']['currentPath'] == ''
    assert snapshot['background']['base']['url'] == '/media/background/base'
    assert snapshot['background']['overlay']['canonicalReference'] == 'asset:user/backgrounds/orchestras/di-sarli.png'
    assert snapshot['background']['overlay']['currentPath'] == ''
    assert snapshot['background']['overlay']['url'] == '/media/background/overlay'
    assert snapshot['background']['overlay']['mode'] == 'blend'
    assert snapshot['background']['overlay']['opacity'] == 40
    assert snapshot['currentSong']['albumArtist'] == 'Carlos Di Sarli'
    assert isinstance(snapshot['displayItems'], list)
    assert 'base' in snapshot['background']
    assert 'overlay' in snapshot['background']


def test_png_warning_suppressed_image_loading():
    import wx

    from bin.displaydata import DisplayData
    from bin.dialogs.preferencespanels.displaypanel import DisplayPanel

    log_calls = []

    class FakeLogNull:
        def __init__(self):
            log_calls.append('created')

    class FakeBitmap:
        def __init__(self, source):
            self.source = source

        def GetSize(self):
            return (64, 64)

    class FakeImage:
        def __init__(self, source):
            self.source = source
            self.channels_adjusted = False

        def IsOk(self):
            return True

        def GetWidth(self):
            return 32

        def GetHeight(self):
            return 32

        def Scale(self, width, height, quality):
            self.scaled_to = (width, height, quality)
            return self

        def AdjustChannels(self, red, green, blue, alpha):
            self.channels_adjusted = True
            return self

    fake_display = SimpleNamespace(
        red=1.0,
        green=1.0,
        blue=1.0,
        alpha=1.0,
        _resolve_background_path=lambda path, prefer_random=False: 'resolved:' + str(path),
    )
    fake_panel = SimpleNamespace(
        _background_bitmap_cache=OrderedDict(),
        _background_bitmap_cache_limit=8,
        displayData=fake_display,
    )
    fake_loader = SimpleNamespace(
        _backgroundLayerState={
            'base': {
                'available': True,
                'sourcePath': 'asset:user/backgrounds/moods/test.png',
                'currentPath': 'C:/managed/layered-background.png',
                'rotate': 'no',
                'rotateTimer': 0,
            },
            'overlay': {},
        },
        backgroundLayers={'base': {}, 'overlay': {}},
        _get_active_background_layer_name=lambda: 'base',
        RotateBackground='no',
        _legacyBackgroundBitmap=None,
        modifiedBitmap=None,
        BackgroundImageWidth=0,
        BackgroundImageHeight=0,
        _resolve_background_path=lambda path, prefer_random=False: 'C:/managed/background.png',
    )

    with patch.object(wx, 'LogNull', FakeLogNull), \
         patch.object(wx, 'Image', FakeImage), \
         patch.object(wx, 'Bitmap', FakeBitmap):
        bitmap = DisplayPanel._get_scaled_background_bitmap(fake_panel, 'C:/managed/background.png', 800, 600, 1.0)
        assert isinstance(bitmap, FakeBitmap)
        assert log_calls == ['created']

        cached_bitmap = DisplayPanel._get_scaled_background_bitmap(fake_panel, 'C:/managed/background.png', 800, 600, 1.0)
        assert cached_bitmap is bitmap
        assert log_calls == ['created']

        cache_limit = fake_panel._background_bitmap_cache_limit
        cache_paths = ['C:/managed/cache-%02d.png' % index for index in range(cache_limit + 1)]
        for cache_path in cache_paths[:cache_limit]:
            DisplayPanel._get_scaled_background_bitmap(fake_panel, cache_path, 800, 600, 1.0)

        DisplayPanel._get_scaled_background_bitmap(fake_panel, cache_paths[0], 800, 600, 1.0)
        DisplayPanel._get_scaled_background_bitmap(fake_panel, cache_paths[-1], 800, 600, 1.0)

        assert len(fake_panel._background_bitmap_cache) == cache_limit
        cached_paths = [cache_key[0] for cache_key in fake_panel._background_bitmap_cache.keys()]
        assert cache_paths[1] not in cached_paths
        assert cache_paths[0] in cached_paths
        assert cached_paths[-1] == cache_paths[-1]

        opacity_bitmap = DisplayPanel._get_scaled_background_bitmap(fake_panel, cache_paths[0], 800, 600, 0.35)
        assert isinstance(opacity_bitmap, FakeBitmap)
        assert len(fake_panel._background_bitmap_cache) == cache_limit
        cached_keys = list(fake_panel._background_bitmap_cache.keys())
        cached_opacity_paths = [cache_key[0] for cache_key in cached_keys if cache_key[7] == round(0.35, 4)]
        cached_full_opacity_paths = [cache_key[0] for cache_key in cached_keys if cache_key[7] == round(1.0, 4)]
        assert cached_opacity_paths == [cache_paths[0]]
        assert cache_paths[0] in cached_full_opacity_paths

        layer_draw_path = DisplayPanel._get_layer_draw_path(
            fake_panel,
            {
                'available': True,
                'sourcePath': 'asset:user/backgrounds/moods/test.png',
                'currentPath': 'C:/managed/layer-current.png',
                'rotate': 'random',
            },
        )
        assert layer_draw_path == 'C:/managed/layer-current.png'

        effective_background_path = DisplayData.getEffectiveTransitionBackgroundPath(fake_loader)
        assert effective_background_path == 'C:/managed/layered-background.png'
        assert DisplayData.shouldUseLegacyBackgroundFallback(fake_loader) is False

        log_count_before_display_load = len(log_calls)
        DisplayData._load_background(fake_loader)
        assert fake_loader._legacyBackgroundBitmap.source == 'C:/managed/background.png'
        assert fake_loader.modifiedBitmap == 'C:/managed/background.png'
        assert fake_loader.BackgroundImageWidth == 64
        assert fake_loader.BackgroundImageHeight == 64
        assert len(log_calls) == log_count_before_display_load + 1


def test_beamsettings_background_migration():
    from bin.beamsettings import BeamSettings

    default_config = load_default_config()
    legacy_config = deepcopy(default_config)
    module_index_by_platform = {
        'Linux': 0,
        'Windows': 1,
        'Darwin': 2,
    }
    module_index = module_index_by_platform.get(platform.system(), 0)
    legacy_config.pop('ArtistBackgrounds', None)
    legacy_config['Moods'][0]['Background'] = 'resources\\backgrounds\\bg1920x1080px_darkGreen.jpg'
    legacy_config['Moods'][0]['RotateBackground'] = 'linear'
    legacy_config['Moods'][0]['RotateTimer'] = 30
    legacy_config['Module'] = default_config['AllModules'][module_index]['Modules'][0]
    legacy_config['Moods'][0]['Display'][2]['Field'] = '%Title'
    legacy_config['Moods'][0]['Display'][2]['TextFlow'] = 'Cut'
    legacy_config['Moods'][0]['Display'][1]['Field'] = '%AlbumArtist'
    legacy_config['Moods'][0]['Display'][1]['TextFlow'] = 'Cut'

    default_config['ArtistBackgrounds']['Mappings'] = [
        {
            'Name': 'Default Mapping',
            'Field': '%AlbumArtist',
            'Operator': 'is',
            'Value': 'Test',
            'Background': '',
            'Mode': 'blend',
            'Opacity': 35,
            'RotateBackground': 'no',
            'RotateTimer': 120,
            'Active': 'yes',
        }
    ]
    legacy_config['ArtistBackgrounds'] = {
        'Enabled': 'True',
        'Mappings': [
            {
                'Name': 'Legacy Orchestra',
                'Field': '%AlbumArtist',
                'Operator': 'is',
                'Value': 'Carlos Di Sarli',
                'Background': 'resources/backgrounds/orchestras/di-sarli.png',
                'Mode': 'blend',
                'Opacity': 40,
                'RotateBackground': 'random',
                'RotateTimer': 45,
                'Active': 'yes',
            }
        ],
    }

    settings = BeamSettings()
    settings._BeamSettings__setConfigData(legacy_config, default_config)

    assert settings.getMoods()[0]['Background'] == 'asset:builtin/backgrounds/bg1920x1080px_darkGreen.jpg'
    assert settings.getArtistBackgrounds()['Enabled'] == 'True'
    assert settings.getArtistBackgrounds()['StorageRoot'] == 'backgrounds/orchestras'
    assert settings.getArtistBackgroundMappings()[0]['Background'] == 'asset:builtin/backgrounds/orchestras/di-sarli.png'
    assert settings.getMoods()[0]['Display'][2]['TextFlow'] == 'Wrap'
    assert settings.getMoods()[0]['Display'][1]['TextFlow'] == 'Cut'
    assert settings.isDirty() is False


def test_readability_background_mode(temp_root):
    from bin.network.schema import background_layer_to_dict
    from bin.nowplayingdata import NowPlayingData
    from bin.songclass import SongObject

    beam_home, beam_resources, beam_config = build_test_roots(temp_root)
    base_background = beam_resources / 'backgrounds' / 'readable-mood.png'
    base_background.parent.mkdir(parents=True, exist_ok=True)
    write_png(base_background)

    config_data = load_default_config()
    config_data['Module'] = 'VirtualDJ'
    config_data['Moods'] = [deepcopy(config_data['Moods'][0])]
    mood = config_data['Moods'][0]
    mood['Name'] = 'Default'
    mood['Background'] = 'asset:builtin/backgrounds/readable-mood.png'
    # "Keep existing" mode keeps the background and applies the Readability blur/dim.
    mood['BackgroundMode'] = 'keep'
    mood['Readability'] = 50
    config_data['ArtistBackgrounds'] = {'Enabled': 'False', 'Mappings': []}

    current_settings = FakeSettings(config_data)
    now_playing = NowPlayingData()
    now_playing.currentPlaylist = [SongObject(p_title='Song')]

    with patch('bin.backgroundassets.getBeamHomePath', return_value=str(beam_home)), \
         patch('bin.backgroundassets.getBeamResourcesPath', return_value=str(beam_resources)), \
         patch('bin.backgroundassets.getBeamConfigPath', return_value=str(beam_config)):
        state = now_playing.build_display_state_for_mood(current_settings, mood)

    base_layer = state['backgroundLayers']['base']
    # The background reference is preserved (keep existing does not clear it),
    # and the base layer is flagged so the display can inherit the on-screen background.
    assert base_layer['available'] is True
    assert base_layer['keepExisting'] is True
    assert base_layer['canonicalReference'] == 'asset:builtin/backgrounds/readable-mood.png'
    assert base_layer['improveReadability'] is True
    assert base_layer['readability'] == 50

    layer_dict = background_layer_to_dict(base_layer, 'base')
    assert layer_dict['improveReadability'] is True
    assert layer_dict['readability'] == 50

    # The legacy "readability" mode name still enables the effect.
    mood['BackgroundMode'] = 'readability'
    assert now_playing._resolve_readability_settings(mood)[0] is True

    # Readability 0 means no effect, even in keep mode.
    mood['BackgroundMode'] = 'keep'
    mood['Readability'] = 0
    assert now_playing._resolve_readability_settings(mood)[0] is False

    # Image/Color modes use the mood's own background and never apply readability.
    mood['BackgroundMode'] = 'image'
    mood['Readability'] = 80
    assert now_playing._resolve_readability_settings(mood)[0] is False
    image_state = now_playing.build_display_state_for_mood(current_settings, mood)
    assert image_state['backgroundLayers']['base']['keepExisting'] is False

    # Missing fields (legacy configs) default to image (use own background), no effect.
    mood.pop('BackgroundMode', None)
    mood.pop('Readability', None)
    improve_legacy, readability_legacy = now_playing._resolve_readability_settings(mood)
    assert improve_legacy is False
    assert readability_legacy == 0


def test_keep_existing_inherits_previous_background():
    from bin.displaydata import DisplayData

    # A "keep existing" mood inherits the background already on screen instead of
    # replacing it; only the readability tweaks from the new mood are carried over.
    previous_layers = {
        'base': {
            'available': True,
            'kind': 'asset',
            'sourcePath': 'C:/managed/previous-bg.png',
            'currentPath': 'C:/managed/previous-bg.png',
            'canonicalReference': 'asset:user/backgrounds/moods/previous-bg.png',
            'improveReadability': False,
            'readability': 0,
        },
        'overlay': {},
    }
    fake_display = SimpleNamespace(backgroundLayers=deepcopy(previous_layers))

    keep_layers = {
        'base': {
            'available': True,
            'kind': 'asset',
            'sourcePath': 'C:/managed/message-mood-bg.png',
            'canonicalReference': 'asset:user/backgrounds/moods/message-mood-bg.png',
            'keepExisting': True,
            'improveReadability': True,
            'readability': 40,
        },
        'overlay': {},
    }
    merged = DisplayData._apply_keep_existing_background(fake_display, deepcopy(keep_layers))
    merged_base = merged['base']
    # The previously displayed background is kept, not the message mood's own one.
    assert merged_base['sourcePath'] == 'C:/managed/previous-bg.png'
    assert merged_base['currentPath'] == 'C:/managed/previous-bg.png'
    # Readability settings from the new mood are applied to the kept background.
    assert merged_base['improveReadability'] is True
    assert merged_base['readability'] == 40

    # A non-keep mood replaces the background as before.
    replace_layers = {
        'base': {
            'available': True,
            'sourcePath': 'C:/managed/own-bg.png',
            'keepExisting': False,
        },
        'overlay': {},
    }
    replaced = DisplayData._apply_keep_existing_background(fake_display, deepcopy(replace_layers))
    assert replaced['base']['sourcePath'] == 'C:/managed/own-bg.png'

    # Keep mode with nothing to inherit falls back to the mood's own background.
    empty_display = SimpleNamespace(backgroundLayers={'base': {}, 'overlay': {}})
    fallback = DisplayData._apply_keep_existing_background(empty_display, deepcopy(keep_layers))
    assert fallback['base']['sourcePath'] == 'C:/managed/message-mood-bg.png'


def test_readability_blur_dim_mapping_and_cache():
    from bin.dialogs.preferencespanels.displaypanel import DisplayPanel

    assert DisplayPanel._readability_to_blur_dim(0) == (0, 0.0)
    assert DisplayPanel._readability_to_blur_dim(50) == (10, 0.25)
    assert DisplayPanel._readability_to_blur_dim(100) == (20, 0.5)
    # Out-of-range values are clamped.
    assert DisplayPanel._readability_to_blur_dim(150) == (20, 0.5)
    assert DisplayPanel._readability_to_blur_dim(-5) == (0, 0.0)

    import wx

    blur_calls = []

    class FakeImage:
        def __init__(self, source):
            self.source = source

        def IsOk(self):
            return True

        def GetWidth(self):
            return 32

        def GetHeight(self):
            return 32

        def Scale(self, width, height, quality):
            return self

        def Blur(self, radius):
            blur_calls.append(radius)
            return self

        def AdjustChannels(self, red, green, blue, alpha):
            return self

    class FakeBitmap:
        def __init__(self, source):
            self.source = source

        def GetSize(self):
            return (64, 64)

    fake_display = SimpleNamespace(red=1.0, green=1.0, blue=1.0, alpha=1.0)
    fake_panel = SimpleNamespace(
        _background_bitmap_cache=OrderedDict(),
        _background_bitmap_cache_limit=8,
        displayData=fake_display,
    )

    with patch.object(wx, 'LogNull', lambda: SimpleNamespace()), \
         patch.object(wx, 'Image', FakeImage), \
         patch.object(wx, 'Bitmap', FakeBitmap):
        DisplayPanel._get_scaled_background_bitmap(fake_panel, 'C:/bg.png', 800, 600, 1.0, readability=0)
        assert blur_calls == []

        DisplayPanel._get_scaled_background_bitmap(fake_panel, 'C:/bg.png', 800, 600, 1.0, readability=50)
        assert blur_calls == [10]

        # Same readability hits the cache (no second blur), different readability misses.
        DisplayPanel._get_scaled_background_bitmap(fake_panel, 'C:/bg.png', 800, 600, 1.0, readability=50)
        assert blur_calls == [10]
        DisplayPanel._get_scaled_background_bitmap(fake_panel, 'C:/bg.png', 800, 600, 1.0, readability=100)
        assert blur_calls == [10, 20]


def main():
    os.chdir(ROOT)
    temp_home = tempfile.mkdtemp(prefix='beam-background-pipeline-')
    os.environ['HOME'] = temp_home
    os.environ['USERPROFILE'] = temp_home
    os.environ['LOCALAPPDATA'] = temp_home

    test_background_asset_roundtrip(temp_home)
    test_beamsettings_background_migration()
    test_nowplaying_background_layers_and_snapshot(temp_home)
    test_png_warning_suppressed_image_loading()
    test_readability_background_mode(temp_home)
    test_readability_blur_dim_mapping_and_cache()
    test_keep_existing_inherits_previous_background()
    print('Background pipeline smoke test passed')


if __name__ == '__main__':
    main()
