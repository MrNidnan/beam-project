# Background Layering Implementation Plan

## Goal

Extend Beam's current single-background display model so the display can combine:

- a base background driven by the active mood, which continues to behave like the current curtain/background
- an optional secondary background driven by the current orchestra or artist
- configurable layering behavior so the secondary image can be fully opaque, semitransparent, or disabled
- backgrounds selected and added by the user at runtime after Beam has already been built and installed

The feature should work for both the wxPython display and the browser projection, remain compatible with existing profiles, and keep the current mood workflow intact.

## Requirement Summary

The requested capability is:

- keep mood-based backgrounds
- allow a different background to be assigned to a specific artist or orchestra
- support blending the artist background over the curtain, instead of always replacing it
- support cases where the artist background should completely replace the base background
- allow users to add new background image files after installation, without rebuilding the app

For Beam's current metadata model, "orchestra" should map to `%AlbumArtist` first and fall back to `%Artist` when `%AlbumArtist` is empty. This matches the existing song fields already exposed through `SongObject` and the network snapshot.

## Current State

Today Beam has a single active background path.

- Mood selection resolves one `Background` value plus one `RotateBackground` mode in [bin/nowplayingdata.py](c:/dev/beam-project/bin/nowplayingdata.py#L336).
- The active path is copied into display state as `_currentBackgroundPath` in [bin/displaydata.py](c:/dev/beam-project/bin/displaydata.py#L202).
- The wxPython renderer draws one bitmap in [bin/dialogs/preferencespanels/displaypanel.py](c:/dev/beam-project/bin/dialogs/preferencespanels/displaypanel.py#L103).
- The browser adapter also serializes one background image in [bin/network/schema.py](c:/dev/beam-project/bin/network/schema.py#L60), and the tablet client renders one CSS background in [resources/web/tablet/app.js](c:/dev/beam-project/resources/web/tablet/app.js#L150).
- Mood and default layout editors expose one background picker with optional folder rotation in [bin/dialogs/editmooddialog.py](c:/dev/beam-project/bin/dialogs/editmooddialog.py#L452) and [bin/dialogs/preferencespanels/defaultlayoutpanel.py](c:/dev/beam-project/bin/dialogs/preferencespanels/defaultlayoutpanel.py#L152).

There is also an important packaging constraint:

- `getBeamHomePath()` points at the unpacked application bundle when Beam is frozen, via `sys._MEIPASS`, in [bin/beamutils.py](c:/dev/beam-project/bin/beamutils.py#L46).
- `resources/backgrounds` is therefore a build-time asset location, not a safe long-term home for user-added images after installation.

This means the current implementation cannot represent layered backgrounds without a model change first.

It also means runtime background management should be treated as a prerequisite design step, not as a later polish item.

## Value

- Gives DJs a stable visual identity per mood while still highlighting the current orchestra.
- Preserves existing curtain-like readability because the orchestra art can be blended instead of replacing the whole scene.
- Makes the projection more expressive during tandas without forcing more mood definitions.
- Fits naturally with Beam's new profile system because different events can keep different artist background libraries.
- Removes the need to rebuild or repack Beam whenever a user wants to add or replace visual assets.

## Phase 0 Code Design

Phase 0 should be implemented before any layered rendering work. The current code still assumes that every background string can be resolved by joining it against `getBeamHomePath()`, which is no longer safe once users can import images after install or run a frozen build through `sys._MEIPASS`.

The design below keeps the change small:

- add one helper module that owns parsing, normalization, resolution, and import decisions for background assets
- keep persisted config as strings so existing JSON shape stays simple
- migrate in `BeamSettings` during load without forcing an immediate rewrite of the user profile

### Storage roots

Built-in and user-managed assets should have explicit roots.

```text
builtin root = <Beam resources root>
user root = <Beam config root>

builtin backgrounds live under:
resources/backgrounds/

user backgrounds live under:
~/.beam/backgrounds/moods/
~/.beam/backgrounds/orchestras/
```

`builtin` should resolve from `getBeamResourcesPath()` rather than `getBeamHomePath()`. That matches how bundled JSON and other resources are already loaded in [bin/beamsettings.py](c:/dev/beam-project/bin/beamsettings.py#L62) and avoids carrying `resources/` twice inside the helper.

### Path parser and resolver helper

Add a small helper module, for example `bin/backgroundassets.py`.

Its job is to centralize all background path handling that is currently split across [bin/beamutils.py](c:/dev/beam-project/bin/beamutils.py#L54), [bin/displaydata.py](c:/dev/beam-project/bin/displaydata.py#L85), and the background picker flows in [bin/dialogs/editmooddialog.py](c:/dev/beam-project/bin/dialogs/editmooddialog.py#L452) and [bin/dialogs/preferencespanels/defaultlayoutpanel.py](c:/dev/beam-project/bin/dialogs/preferencespanels/defaultlayoutpanel.py#L152).

Recommended persisted contract:

```text
asset:<scope>/<relative-path>
```

Examples:

```text
asset:builtin/backgrounds/bg1920x1080px.jpg
asset:user/backgrounds/moods/golden-age-curtain.jpg
asset:user/backgrounds/orchestras/di-sarli/overlay-01.jpg
```

Compatibility inputs Beam should continue to accept:

1. `asset:...`
2. `resources/...` or `resources\\...`
3. absolute filesystem paths
4. empty string

Recommended helper surface:

```python
AssetScopes = ('builtin', 'user', 'external', 'invalid', 'empty')

ParsedBackgroundRef = {
   'kind': 'asset' | 'legacy-resource' | 'absolute' | 'empty' | 'invalid',
   'scope': 'builtin' | 'user' | 'external' | None,
   'reference': 'asset:user/backgrounds/moods/a.jpg',
   'rawValue': 'resources/backgrounds/a.jpg',
   'relativePath': 'backgrounds/moods/a.jpg',
   'normalizedReference': 'asset:builtin/backgrounds/a.jpg',
}

ResolvedBackgroundAsset = {
   'kind': 'asset' | 'legacy-resource' | 'absolute' | 'empty' | 'invalid',
   'scope': 'builtin' | 'user' | 'external' | None,
   'reference': 'asset:user/backgrounds/orchestras/di-sarli.jpg',
   'absolutePath': 'C:/Users/.../.beam/backgrounds/orchestras/di-sarli.jpg',
   'relativePath': 'backgrounds/orchestras/di-sarli.jpg',
   'exists': True,
   'canonicalReference': 'asset:user/backgrounds/orchestras/di-sarli.jpg',
}
```

Recommended functions:

```python
def parse_background_reference(value):
   pass

def normalize_background_reference(value):
   pass

def resolve_background_reference(value):
   pass

def to_persisted_background_reference(absolute_path, asset_type):
   pass

def import_background_asset(source_path, asset_type, copy_mode='copy'):
   pass
```

Function behavior:

- `parse_background_reference(value)` only classifies and sanitizes the string
- `normalize_background_reference(value)` converts accepted legacy built-in values like `resources/backgrounds/foo.jpg` into `asset:builtin/backgrounds/foo.jpg`
- `resolve_background_reference(value)` returns one runtime object with the final absolute path, regardless of whether the source was canonical, legacy, or external
- `to_persisted_background_reference(absolute_path, asset_type)` converts a selected file already under Beam roots into `asset:builtin/...` or `asset:user/...`
- `import_background_asset(source_path, asset_type, copy_mode='copy')` copies unmanaged files into Beam-managed storage and returns the persisted `asset:user/...` reference

Scope rules:

- `builtin` maps to `getBeamResourcesPath()` plus the stored relative path
- `user` maps to `getBeamConfigPath()` plus the stored relative path
- `external` maps directly to the absolute path and is treated as compatibility-only, not the preferred saved format

Normalization rules:

- always persist forward slashes inside `asset:...` strings, even on Windows
- strip leading `./`
- treat `resources/backgrounds/...` as legacy builtin and normalize to `asset:builtin/backgrounds/...`
- reject `..` path traversal after normalization
- preserve file extension casing as-is or lower-case it consistently, but choose one rule and apply it everywhere

### Managed asset copy and import rules

Phase 0 should define the import contract now, even if the full artist mapping UI lands later.

Asset classes:

- mood backgrounds import under `backgrounds/moods/`
- artist backgrounds import under `backgrounds/orchestras/`

Recommended picker behavior for both mood and future artist background editors:

1. User selects a file or a rotation folder.
2. Beam calls `to_persisted_background_reference()`.
3. If the selection is already under `getBeamResourcesPath()`, save `asset:builtin/...`.
4. If the selection is already under `getBeamConfigPath()`, save `asset:user/...`.
5. If the selection is outside both roots, Beam offers to import it.
6. If the import succeeds, save the returned `asset:user/...` reference.
7. If the import fails, keep the old value unchanged unless the user explicitly accepts an unmanaged external path.

Recommended collision and copy policy:

- create the destination directory if missing
- keep the original filename when the target path is unused
- if the filename already exists with different content, append `-1`, `-2`, and so on
- if the filename already exists with identical content, reuse the existing file and return its `asset:user/...` reference
- never overwrite a built-in asset in `resources/backgrounds`
- folder imports should only bring in supported image files and ignore other files

Recommended import result object:

```python
ImportedBackgroundAsset = {
   'status': 'imported' | 'reused' | 'external' | 'failed',
   'reference': 'asset:user/backgrounds/moods/example.jpg',
   'absolutePath': 'C:/Users/.../.beam/backgrounds/moods/example.jpg',
   'copiedFiles': 1,
   'message': '',
}
```

Folder rotation rules:

- if a folder is selected for a rotating mood background, Beam imports the folder contents into one managed destination folder under the relevant asset class
- the stored config value points at the managed folder reference, not a single file
- file ordering remains a runtime concern in `DisplayData`; Phase 0 only decides where the folder lives and how it is referenced

### Exact `BeamSettings` migration behavior

The migration point should be `BeamSettings.__setConfigData()` in [bin/beamsettings.py](c:/dev/beam-project/bin/beamsettings.py#L432). That is already the place where Beam complements missing defaults and patches older config shapes without immediately marking the profile dirty.

Recommended Phase 0 migration sequence inside `__setConfigData()`:

1. Deep-copy the loaded profile into `self._beamConfigData` as today.
2. Apply `complementDict(defaultConfigData, self._beamConfigData)` as today for new top-level keys.
3. Continue complementing each mood from `defaultConfigData['Moods'][0]` as today.
4. Add a dedicated migration pass after the existing default completion logic and before dirty tracking resumes.

Recommended migration helper calls:

```python
def _migrate_background_config_in_memory(self):
   self._migrate_mood_background_references()
   self._ensure_artist_background_defaults()

def _migrate_mood_background_references(self):
   pass

def _ensure_artist_background_defaults(self):
   pass
```

Exact in-memory migration behavior for mood `Background` values:

- if the value is empty, keep it empty
- if the value starts with `asset:`, validate and keep it unchanged
- if the value starts with `resources/` or `resources\\`, normalize it in memory to `asset:builtin/...`
- if the value is an absolute path, keep it unchanged in memory for compatibility in Phase 0
- if the value is a Beam-home-relative legacy path that does not start with `resources/`, keep it unchanged and log a warning instead of guessing
- if normalization fails, keep the original string and log a warning

Exact default injection behavior for the new top-level section:

```json
"ArtistBackgrounds": {
  "Enabled": "False",
  "StorageRoot": "backgrounds/orchestras",
  "MatchField": "%AlbumArtist",
  "FallbackField": "%Artist",
  "DefaultMode": "blend",
  "DefaultOpacity": 35,
  "Mappings": []
}
```

This should be added to the default JSON and then injected through the existing `complementDict()` flow. No explicit profile rewrite should happen during load.

Exact dirty/save semantics:

- `__setConfigData()` already runs with `_suspendDirtyTracking = True`, so migration should not mark the profile dirty on load
- a migrated `resources/...` value that was normalized in memory should be persisted only when the user later saves the active profile
- unchanged absolute-path backgrounds should round-trip unchanged until the user edits that field through the new import-aware picker flow
- `dumpConfigData()` should stay simple and write the current in-memory config without adding more migration logic

Writeback rules on explicit save:

- `asset:...` values save unchanged
- normalized legacy built-in values save as `asset:builtin/...`
- absolute paths save unchanged only if they were preserved from an older profile or the user explicitly chose an unmanaged external reference
- newly selected unmanaged files should not be written back as raw absolute paths unless the import flow failed and the user explicitly opted into that fallback

This keeps migration safe and reversible:

- old profiles continue to load with no surprise file copies
- legacy bundled paths become canonical on the next normal save
- external absolute paths are not silently imported or rewritten behind the user's back

### Phase 0 integration points

The minimum Phase 0 code touch points should be:

- `bin/backgroundassets.py`: new helper module
- `bin/beamsettings.py`: in-memory migration pass and accessors for managed asset roots if needed
- `bin/dialogs/editmooddialog.py`: replace `getRelativePath()` save behavior with import-aware asset persistence
- `bin/dialogs/preferencespanels/defaultlayoutpanel.py`: same picker update as the mood dialog
- `bin/displaydata.py`: replace `os.path.join(getBeamHomePath(), background_path)` with helper-based resolution

Phase 0 explicitly does not need to implement layered display state yet. It only needs to make background storage and resolution deterministic enough that Phase 1 can build on it.

## Recommended Product Shape

Implement this as two coordinated background layers:

1. `Mood background`
   The existing mood background. This remains the base layer.

2. `Artist background overlay`
   An optional layer selected from artist-orchestra mappings. This sits above the mood layer and below text.

Each overlay should support:

- `mode = off | blend | replace`
- `opacity = 0..100`
- optional `rotate = no | linear | random`
- optional `rotateTimer`

Recommended first release behavior:

- `off`: only the mood background is shown
- `blend`: draw mood background first, then draw artist background using the configured opacity
- `replace`: draw only the artist background for that song, while still retaining the mood for layout, DMX, and text rules

This keeps the feature understandable and avoids introducing more complex blend modes such as multiply or screen in the first pass.

## Proposed Data Model

### 1. Keep existing mood fields for backward compatibility

Do not remove or rename:

- `Background`
- `RotateBackground`
- `RotateTimer`

These should continue to define the base mood layer.

However, new values should not be limited to bundled `resources/...` paths. They should also support user-managed assets stored in the Beam config area.

Recommended interpretation of `Background`:

- existing configs may still contain `resources/...`
- new saves should write `asset:builtin/...` or `asset:user/...`

### 2. Add a new top-level artist background section to config

Recommended shape:

```json
"ArtistBackgrounds": {
  "Enabled": "False",
  "StorageRoot": "backgrounds/orchestras",
  "MatchField": "%AlbumArtist",
  "FallbackField": "%Artist",
  "DefaultMode": "blend",
  "DefaultOpacity": 35,
  "Mappings": [
    {
      "Name": "Carlos Di Sarli",
      "Field": "%AlbumArtist",
      "Operator": "is",
      "Value": "Carlos Di Sarli",
      "Background": "resources/backgrounds/orchestras/di-sarli.jpg",
      "Mode": "blend",
      "Opacity": 40,
      "RotateBackground": "no",
      "RotateTimer": 120,
      "Active": "yes"
    }
  ]
}
```

Why a separate section instead of extending moods:

- moods answer "what visual layout applies"
- artist mappings answer "what art should be layered for this orchestra"
- the feature is cross-cutting and should not require duplicating every mood for every orchestra

### 3. Add resolved display-layer state at runtime

Instead of one `BackgroundPath`, the runtime model should resolve something like:

```python
ResolvedBackgroundLayers = {
    'base': {
        'path': '...',
        'rotate': 'no',
        'rotateTimer': 120,
    },
    'overlay': {
        'available': True,
        'path': '...',
        'mode': 'blend',
        'opacity': 35,
        'rotate': 'no',
        'rotateTimer': 120,
    }
}
```

The renderer should consume the resolved layers rather than re-deciding matching logic.

### 4. Introduce an asset-resolution layer

Beam should stop assuming that every background path is relative to the application home.

Recommended runtime abstraction:

```python
ResolvedBackgroundAsset = {
  'reference': 'asset:user/backgrounds/orchestras/di-sarli.jpg',
  'source': 'builtin' or 'user',
  'relativePath': 'backgrounds/orchestras/di-sarli.jpg',
  'absolutePath': 'C:/Users/.../.beam/backgrounds/orchestras/di-sarli.jpg',
}
```

That resolution should happen in one place and be shared by mood backgrounds, artist overlays, preview rendering, and network media serving.

## Matching Rules

Recommended matching precedence:

1. If `ArtistBackgrounds.Enabled` is false, do nothing.
2. Resolve the active mood as today.
3. Resolve the base layer from the mood.
4. Evaluate artist background mappings against the current song.
5. First active matching mapping wins.
6. Match `%AlbumArtist` first.
7. If `%AlbumArtist` is empty, retry using `%Artist`.

Matching operators should initially mirror Beam's existing rule vocabulary:

- `is`
- `is not`
- `contains`

That keeps the UI and behavior aligned with existing rule and mood concepts.

## UI Changes

### Preferences

Add a new Preferences page named `Artist Backgrounds` or `Background Layers`.

Recommended controls:

- enable artist backgrounds
- default match field
- default fallback field
- list of artist mappings
- add, edit, delete mapping buttons

Each mapping editor should include:

- name
- field to match
- operator
- value
- background file or folder picker
- mode: blend or replace
- opacity slider when mode is blend
- rotate checkbox and timer
- active checkbox

### Mood Editor

The mood editor should remain focused on the base layer. Only small wording changes are needed:

- rename the current mood background label to `Base background`
- explain that artist overlays can be configured separately

This avoids turning the mood editor into a second place to manage artist assets.

### Preview Panel

The preview should eventually render both layers so the operator can validate readability before saving. That can ship in phase 2 if needed, but the data model should support it from the start.

## Rendering Changes

### wxPython display

Current issue:

- the preview and display render one bitmap only

Recommended implementation:

1. Resolve base and overlay images separately in `DisplayData`.
2. Cache both loaded bitmaps and their scaled versions.
3. Draw base layer first.
4. If overlay is available:
   - in `blend` mode, draw overlay with alpha derived from `Opacity`
   - in `replace` mode, skip drawing base layer and draw overlay only
5. Draw text and cover art last.

Important note:

The current fade logic adjusts color channels on a single image. After layering, transitions should operate on the composed result or on both layers consistently. The lowest-risk path is:

- keep current fade behavior for phase 1
- apply the same transition factors to each rendered layer before drawing

### Background rotation

Current rotation assumes one active path and one timer.

Recommended change:

- keep existing mood rotation behavior for the base layer
- add separate overlay rotation state only if an artist mapping is active
- do not reuse the current single `_currentBackgroundPath` field for both roles

The cleanest direction is to replace the single background state with explicit base and overlay state objects.

### Browser projection

The web client already draws a soft background overlay via CSS. It should be extended to accept:

- `background.base`
- `background.overlay`

Recommended browser behavior:

- base layer stays on `body::before`
- overlay uses `body::after` or an inner fixed layer
- blend opacity is passed through from the snapshot

This keeps visual parity with the desktop renderer without changing the event model.

## Configuration and Migration

Existing profiles must continue to load with no user action.

Migration strategy:

- if `ArtistBackgrounds` is missing, inject defaults in memory when loading config
- save the section only after the user changes related settings or saves the profile
- keep all existing mood background fields untouched
- normalize legacy bundled `resources/...` paths in memory to `asset:builtin/...` during `BeamSettings.__setConfigData()`
- normalize legacy built-in values to `asset:builtin/...` when the profile is next saved
- allow newly selected backgrounds to be copied into `~/.beam/backgrounds/...` and stored as `asset:user/...`
- preserve existing absolute paths for compatibility, but avoid writing new unmanaged absolute paths unless the user explicitly opts into that fallback

Suggested defaults:

```json
"ArtistBackgrounds": {
  "Enabled": "False",
  "StorageRoot": "backgrounds/orchestras",
  "MatchField": "%AlbumArtist",
  "FallbackField": "%Artist",
  "DefaultMode": "blend",
  "DefaultOpacity": 35,
  "Mappings": []
}
```

## Implementation Phases

### Phase 0: Runtime asset management

- define the Beam-managed user asset folders under the config directory
- add one path parser/resolver helper for built-in, user-managed, and external backgrounds
- define `asset:<scope>/<relative-path>` as the canonical persisted contract
- update file-picker flows so selected images can be copied into Beam-managed storage using explicit import rules
- add `BeamSettings` in-memory migration for legacy `resources/...` background references
- make runtime-selected backgrounds available immediately after save

Deliverable:

- users can add new mood or orchestra background assets after installation with no rebuild
- config can reference both built-in and user-managed assets safely

### Phase 1: Data model and runtime resolution

- extend config defaults and `BeamSettings` accessors
- add artist background mapping data structures
- resolve `base` and `overlay` layers in `NowPlayingData`
- expose layered background state through `DisplayData`
- preserve current behavior when no artist overlay matches

Deliverable:

- no visible regression
- logs and runtime state show which background layers are active

### Phase 2: Desktop rendering

- update `DisplayPanel` to draw two layers
- add caching for scaled base and overlay bitmaps
- support blend opacity and replace mode
- update transition logic to apply to both layers

Deliverable:

- desktop display shows mood base plus artist overlay correctly

### Phase 3: Preferences UI

- add the new editor panel and mapping dialog
- rename mood background wording to clarify it is the base layer
- update preview behavior if practical in the same pass

Deliverable:

- the feature is fully configurable without editing JSON manually

### Phase 4: Browser projection

- extend network snapshot schema for layered backgrounds
- serve current base and overlay images, either through separate endpoints or a parameterized endpoint
- update the tablet client CSS and JS to render both layers

Deliverable:

- browser projection matches desktop behavior closely

### Phase 5: Documentation and migration notes

- update README or docs for the feature
- explain orchestra matching using `%AlbumArtist` and fallback to `%Artist`
- add a short migration note for older profiles

## Validation Plan

### Runtime cases

- no artist mapping configured: behavior is identical to today
- bundled background path still resolves after the new asset layer is introduced
- user imports a new background after installation and can select it immediately
- mood with base image only
- mood with rotating base folder only
- artist overlay with single image in blend mode
- artist overlay with single image in replace mode
- artist overlay with folder rotation
- `%AlbumArtist` present and matching
- `%AlbumArtist` empty, `%Artist` fallback matching
- mood change while artist stays the same
- artist change while mood stays the same
- paused and stopped playback behavior

### Regression checks

- current mood background rotation still works
- text remains readable over light and dark overlays
- profile save and switch preserve the new config section
- network display still works when layered backgrounds are disabled

## Risks

### 0. Wrong storage location

If user-managed backgrounds are written under the app bundle instead of the Beam config directory, packaged installs can lose assets on upgrade or fail to persist them reliably.

Mitigation:

- treat runtime asset storage as Phase 0
- centralize asset resolution and copying rules before layering work starts

### 1. Renderer complexity

The current rendering path assumes one bitmap, one path, and one rotation timer. Layering will touch transition, caching, and repaint behavior.

Mitigation:

- separate resolution state from rendering state early
- avoid adding blend modes beyond `blend` and `replace` in the first version

### 2. Performance

Two large images may increase scaling cost and repaint time.

Mitigation:

- cache scaled bitmaps by panel size and image path
- invalidate only when size, path, opacity, or transition state changes

### 3. Configuration sprawl

If artist mappings are buried inside moods, the feature becomes hard to maintain.

Mitigation:

- keep artist background mappings as a dedicated top-level config section

### 4. Visual readability

Some orchestra images may reduce contrast for text.

Mitigation:

- default to low opacity
- optionally add a later enhancement for a dark scrim over the composed background

## Open Questions

- Should artist overlays support folders and rotation in the first release, or only single images?
- Should matching use only `%AlbumArtist` and `%Artist`, or should `%Performer` also be supported?
- Should the browser client receive two raw image layers, or one server-composited image in a later optimization pass?
- Should there be a global darkening scrim over all backgrounds to preserve readability regardless of image choice?

## Recommended First Slice

If implementation starts after a rest period, the smallest valuable slice is:

1. add runtime asset storage and asset-resolution helpers
2. allow mood backgrounds to use user-managed files without rebuild
3. add `ArtistBackgrounds` config support
4. resolve one optional artist overlay in `NowPlayingData`
5. render it in `blend` mode only on the desktop display
6. leave browser projection and folder rotation for a second pass

That sequence delivers visible value quickly while keeping the first code change narrow enough to validate.

## Background Renderer Refactor Plan

The bounded cache work reduces the most immediate repaint cost, but the remaining design risk is still the split state between:

- the layered runtime model in `backgroundLayers` and `_backgroundLayerState`
- the legacy transition path in `_currentBackgroundPath` and `backgroundImage`

That split is acceptable as a temporary bridge, but it is not a good permanent design. The real risk is not that it looks untidy. The real risk is that every future change to fade behavior, replace mode, rotation, cache invalidation, or browser and desktop parity has to stay correct in two code paths that can drift apart.

### Current assessment

- This is a maintainability and regression risk, not a confirmed cross-platform architecture constraint.
- The desktop rendering path is still wxPython-based across Windows, Linux, and macOS, so the refactor risk is mostly behavioral, not OS-specific.
- The highest-probability regressions are in mood transitions, background rotation timing, and fallback behavior when no overlay is active.
- That makes the refactor worth doing, but only as an incremental change, not a big-bang rewrite.

### Refactor goal

Make layered background state the single source of truth for background resolution, rotation, and transition input in the desktop renderer.

The legacy single-background fields should become temporary derived compatibility values during the migration, and then be removed once no caller depends on them.

### Recommended scope

Keep the refactor limited to the desktop display pipeline:

- `bin/displaydata.py`
- `bin/dialogs/preferencespanels/displaypanel.py`
- any direct transition or timer callers in `bin/mainframe.py`

Do not combine this with player-module changes, network protocol changes, or preferences UI changes.

### Phase 2.5: Unified desktop background state

#### Step 1: Identify the compatibility boundary

- Enumerate every caller that still reads or writes `_currentBackgroundPath`, `backgroundImage`, or `modifiedBitmap`.
- Mark which usages are true desktop-transition dependencies and which are now legacy leftovers.
- Keep one narrow derived compatibility accessor if a caller still requires a single effective path during migration.

Current identified boundary in the implementation:

- `DisplayData` no longer uses `_currentBackgroundPath` or `backgroundImage` as mutable source-of-truth fields. Legacy compatibility is exposed through derived accessors and one explicit fallback bitmap artifact.
- `bin/dialogs/preferencespanels/displaypanel.py` still needs compatibility access only for the final single-image fallback draw path when no layered bitmap was drawn.
- `bin/network/schema.py` still exposes the legacy `background.available` and `background.sourcePath` envelope fields for the browser payload, even though the layered `background.base` and `background.overlay` fields are now the primary model.
- `modifiedBitmap` is no longer a broad compatibility field. It is now effectively local runtime state used inside the desktop rendering path and smoke fixtures, not a cross-module ownership boundary.

Deliverable:

- one documented compatibility boundary instead of implicit field sharing

#### Step 2: Make layer state the source of truth

- Move transition-time background selection to the resolved `base` and `overlay` runtime state.
- Keep `_refresh_background_layer_state()` responsible for producing the current effective layer paths.
- Stop re-deciding active background selection through `_currentBackgroundPath` during transition setup.

Deliverable:

- the transition pipeline reads current background state from the layered model only

#### Step 3: Convert legacy single-image loading into a derived path

- Replace direct background loading through `_load_background()` as a primary control path.
- If a single effective background is still needed for an interim transition step, compute it from the resolved layered state rather than storing a separate mutable source of truth.
- Keep `backgroundImage` as a short-lived compatibility artifact only if one remaining draw path still needs it.

Deliverable:

- legacy image loading becomes a compatibility adapter, not an owning state path

#### Step 4: Unify transition behavior over layered inputs

Status: completed in code

- Ensure fade factors apply consistently to base and overlay rendering from the same transition state.
- Remove any transition branch that assumes there is only one active background path.
- Keep `replace` and `blend` behavior controlled by layer metadata, not by fallback single-image assumptions.

Implementation note:

- The transition path is now layered-first. Legacy fallback bitmap loading only runs when no renderable layered background is available.
- The renderer no longer collapses base and overlay through one active background path during normal layered drawing.

Deliverable:

- fade and mood-change behavior are defined once for layered rendering

#### Step 5: Remove obsolete legacy fields

Status: completed in code

- Remove `_currentBackgroundPath` as a mutable source of truth once no control path depends on it.
- Remove `backgroundImage` ownership from `DisplayData` once the renderer no longer needs single-image compatibility.
- Keep only the minimum derived fields required by remaining external callers, or remove those too if the caller is updated.

Implementation note:

- `_currentBackgroundPath` is no longer stored or mutated as owning runtime state in `DisplayData`; legacy path exposure is now derived from layered state.
- `backgroundImage` is no longer owned by `DisplayData`; the remaining compatibility artifact is an explicit legacy fallback bitmap.
- The remaining legacy surface is now narrow and intentional: derived current-background output for compatibility payloads plus the fallback bitmap used when no layered draw path is available.

Deliverable:

- one desktop background state model instead of layered plus legacy duplicates

### Why this is safe enough to attempt

- The refactor is mostly pure Python state management around wx rendering, not OS-specific media integration.
- The affected timers and repaint logic are shared across supported desktop OSes, so one good desktop validation pass can cover most of the risk.
- The work can be staged so that each step preserves current behavior before the next field is removed.

### Main risks during the refactor

- mood-change transitions may briefly lose parity with the old fade behavior
- rotating folders may regress if active-path selection is moved too aggressively
- `replace` mode may accidentally fall back to base-layer drawing if the compatibility bridge is removed too early

### Validation plan before and during implementation

#### Automated checks

- keep `scripts/smoke_background_pipeline.py` passing after each refactor slice
- keep `scripts/soak_layered_repaints.py` available for longer repaint and memory observation
- add or extend smoke coverage around transition-time effective layer selection if the compatibility accessor is introduced

#### Manual checks

- mood with base image only
- mood with rotating base folder
- artist overlay in `blend` mode
- artist overlay in `replace` mode
- mood change with fade enabled
- song change with same mood
- no overlay active

#### Platform confidence target

- verify at least one Windows run and one Linux run before removing the last legacy compatibility field
- treat macOS as lower-confidence until a maintainer can do a real app run there, but do not block the refactor on speculative macOS concerns alone

### Recommendation

Do not keep the split state permanently.

Do not rewrite everything at once either.

Treat this as a focused post-Phase-2 cleanup, effectively a `Phase 2.5`, and refactor the desktop background pipeline in small behavior-preserving slices until layered state is the only source of truth.
