# Developer Guide

Internals and conventions for working on Beam. For build/release instructions
see [BUILD.md](BUILD.md).

## Developer documentation

Deeper internals and subsystem notes:

- Network display protocol/architecture: [docs/NETWORK_DISPLAY.md](docs/NETWORK_DISPLAY.md)
- Background layering implementation plan: [docs/BACKGROUND_LAYERING_IMPLEMENTATION_PLAN.md](docs/BACKGROUND_LAYERING_IMPLEMENTATION_PLAN.md)

## Settings Storage

All user settings live in JSON on disk and in a single in-memory dictionary at
runtime. `BeamSettings` (`bin/beamsettings.py`) owns that dictionary
(`self._beamConfigData`) and exposes typed `get*` / `set*` accessors; UI panels
never touch the JSON directly.

### Locations

- Config directory: `~/.beam/` (`getBeamConfigPath()` in `bin/beamutils.py`).
- Active config file name: `beamconfig.json` (the `configfilename` key in
  `resources/json/strings.json`).
- Bundled defaults: `resources/json/beamconfig.json`
  (`getDefaultConfigFilePath()`). Shipped read-only; used to seed new installs
  and to backfill missing keys.
- Profiles manifest: `~/.beam/beamprofiles.json`.
- Per-profile config: `~/.beam/profiles/<profileId>.json` (default profile id is
  `default`).

Files are written with `json.dump(..., indent=2, ensure_ascii=False)`. The
`~/.beam/` directory (and `profiles/` subdirectory) are created on first save.

### Profiles

`ProfileSettingsStore` (`bin/profilesettings.py`) manages multiple named profiles.
The manifest lists each profile (`Id`, `Name`, `File`, `Locked`, `Persisted`);
the active profile's JSON file holds the actual settings. `BeamSettings`
delegates profile load/save/switch/create/rename/delete to this store.

### Load flow

1. `loadProfiles()` reads the manifest and the active profile file. Missing
   files fall back, in order, to: legacy `~/.beam/beamconfig.json`, very old
   `~/BeamConfig.json`, then the bundled default.
2. `__setConfigData()` merges defaults into the loaded data with
   `complementDict()` — it **adds** keys absent from the user data without
   overwriting existing user values or lists. `AllModules` and `DMX` are always
   taken from the default config; every mood is backfilled from the default
   mood template.
3. In-memory migrations run last (background references, title text-flow rules,
   etc.) so old config files load cleanly into the current schema.

### Saving and dirty tracking

- Each `set*` accessor calls `_markDirty()`, flipping `self._isDirty`.
- `saveActiveProfile()` (and `dumpConfig()`) write the active profile via
  `dumpConfigData()` and then `clearDirty()`.
- `switchProfile()` auto-saves a dirty profile before switching away.
- Dirty tracking can be suspended (`self._suspendDirtyTracking`) while config is
  being loaded/merged so seeding defaults does not mark the profile dirty.

### Adding a new setting

1. Add the key with its default to `resources/json/beamconfig.json` (so existing
   user configs get it backfilled via `complementDict()`).
2. Add `get<Name>()` / `set<Name>()` accessors on `BeamSettings`; the setter must
   call `self._markDirty()`.
3. Read/write only through those accessors from the UI/runtime.
