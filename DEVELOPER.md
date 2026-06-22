# Developer Guide

Internals and conventions for working on Beam.

## Developer documentation

Deeper internals and subsystem notes:

- Network display protocol/architecture: [docs/NETWORK_DISPLAY.md](docs/NETWORK_DISPLAY.md)
- Background layering implementation plan: [docs/BACKGROUND_LAYERING_IMPLEMENTATION_PLAN.md](docs/BACKGROUND_LAYERING_IMPLEMENTATION_PLAN.md)

## Build And Release

Packaging, PyInstaller commands, smoke scripts, and release steps are documented in [../BUILD.md](../BUILD.md).

## Repository Basics

- main entry point: `beam.py`
- player modules: `bin/modules/`
- app strings and version: `resources/json/strings.json`
- runtime settings template: `resources/json/beamconfig.json`

If you change dependencies, reinstall them with `pip install -r requirements.txt` inside the same virtual environment.

## "Now Playing" source (SMTC / MPRIS)

`Now Playing` is one user-facing module backed by an OS-level, app-agnostic media
reader — no per-app integration. It reads whatever the desktop reports as the
current media session (Spotify, YouTube Music, browsers, Apple Music, etc).

### Architecture

- `bin/modules/nowplayingsource.py` — platform facade. Picks the backend the same
  way the per-app modules split win/lin: **Windows → SMTC**, **Linux → MPRIS**.
  The UI (`basicsettingspanel.py`) and `nowplayingdata.py` call only the facade.
- `bin/modules/win/smtcmodule.py` — Windows backend, reads the **SMTC**
  (`GlobalSystemMediaTransportControls`) session via WinRT.
- `bin/modules/lin/mprismodule.py` — Linux backend, reads **MPRIS**
  (`org.mpris.MediaPlayer2.*`) over D-Bus.

Both backends expose the identical public API
(`aumid_friendly_name` / `list_sessions` / `run_with_details` / `run`) so the
facade can swap them transparently. The "preferred app" id is an opaque string
stored in the existing `SMTC` settings block (an AUMID on Windows, a D-Bus bus
name on Linux).

### Dependencies / backends

- **Windows (SMTC)** — pywinrt split packages (prebuilt wheels, incl. 3.13):
  `winrt-Windows.Media.Control`, `winrt-Windows.Foundation`,
  `winrt-Windows.Foundation.Collections` (required — `get_sessions()` returns an
  `IVectorView` that lives in this namespace), `winrt-Windows.Storage.Streams`
  (optional — only for the album-art thumbnail). NOT the monolithic `winsdk`
  (no 3.13 wheel, compiles from source); `winsdk` is only a runtime fallback.
- **Linux (MPRIS)** — two bindings, preferred → fallback:
  1. `dbus-next` (async, pure-python) — preferred.
  2. `dbus-python` — fallback. Already a guaranteed Linux dep and what the
     existing per-app lin modules use, so MPRIS works on installs without
     dbus-next, and adding dbus-next never breaks them.

  Selection lives in `mprismodule`: `_HAS_DBUS_NEXT` then `_HAS_DBUS_PYTHON`,
  else `route='unavailable'` (no crash). `run_with_details` reports which backend
  is live (`mpris (dbus-next)` / `mpris (dbus-python)`), visible in the prefs
  Test dialog.

All optional imports are guarded so the module always imports and caches —
`nowplayingdata` re-imports it every poll cycle.

### Cover art — compromises

The whole cover pipeline is **path-based**: `SongObject.FilePath` →
`mutagenutils.readCoverArtData`. Neither media session exposes a file, so we
materialize the art to a temp file and point `FilePath` at it:

- **Format is not assumed.** SMTC thumbnails and MPRIS art are frequently PNG,
  sometimes BMP/GIF, not always JPEG. We sniff the magic bytes
  (`_image_extension`) and write the temp file with the **real** extension — no
  lossy re-encode. Unknown signature → skip (no cover, no crash).
- `mutagenutils.readCoverArtData` was taught to read an image file directly (by
  the mime its extension implies) when `FilePath` is itself an image — that is
  how the SMTC/MPRIS temp file is consumed. `getBitmapTypeFromMime` already maps
  jpeg/png/gif/bmp.
- **SMTC** reads thumbnail bytes via `DataReader` (note: pywinrt `read_bytes()`
  fills a pre-sized `bytearray` in place — it does not take a count and return
  data).
- **MPRIS** `mpris:artUrl` is a URI: `file://` is used directly (no copy);
  `http(s)://` is downloaded to a temp file (4s timeout).
- Temp filename is `beam_{smtc,mpris}_<hash>.<ext>`, hashed on
  `bus/aumid + title + artist` so the path changes per track (forces Beam to
  reload) but is reused within a track.

### Temp cleanup

- **Per-song:** writing a new cover deletes the previous one (`_LAST_COVER_PATH`).
- **Startup sweep:** on import, `_sweep_cover_temp()` removes any leftover
  `beam_*_*` files from a previous crashed run (atexit does not fire on crash).
- **Exit:** `atexit.register(_sweep_cover_temp)` clears everything on clean
  shutdown.
- Assumes a single Beam instance — a concurrent instance's covers would also be
  swept, which is harmless since each rewrites its cover every cycle.

### Diagnostic logging

Both backends use a `_log_once(tag, level, ...)` helper that de-dupes on change,
so the per-cycle poll does not spam the log. Routine state (session list, picked
app, track metadata) logs at **DEBUG**; genuine problems (import failure, read
failure, undecodable cover) log at **INFO**.

## Display controls, mood backgrounds & rules (v0.9.3.0, PR #23)

User-facing notes: [../docs/WHATS_NEW_0.9.3.0.md](../docs/WHATS_NEW_0.9.3.0.md).
Background architecture deep-dive:
[../docs/BACKGROUND_LAYERING_IMPLEMENTATION_PLAN.md](../docs/BACKGROUND_LAYERING_IMPLEMENTATION_PLAN.md).
Where the moving parts live:

### Live display overrides — Blackout & Message

Manual, **non-persisted** overrides that reset to inactive on startup; moods,
rules, player polling and background rotation keep running underneath.

- `bin/mainframe.py` — the Blackout/Resume and Show/Clear Message buttons, their
  state, and the one-line status bar (`Player | Mood | Display | [Message |]
Network`).
- `bin/dialogs/messagedialog.py` — message text + duration (5–60s, default 15)
  dialog.
- `bin/displaydata.py` / `bin/dialogs/preferencespanels/displaypanel.py` — apply
  blackout (full-black output) and render the centered message overlay; the
  message still draws on top of a blackout.
- Pushed to the browser display via `bin/network/schema.py` +
  `bin/network/service.py`, so preview, projector and browser stay in sync.

### Mood backgrounds — Keep existing + Readability (blur/dim)

The mood **Background** section is now a single **Background type** dropdown
(`Keep existing` / `Color` / `Single image` / `Image slideshow`).

- `bin/dialogs/editmooddialog.py` — the rework (the big diff): the type dropdown,
  showing only relevant controls, and the **Readability** slider (0–100) used
  with `Keep existing`.
- **Readability** = combined blur + dark overlay applied to the _current_
  background so overlaid text stays legible. Resolved into display-layer state in
  `bin/nowplayingdata.py` and rendered in `displaydata` / `displaypanel`.
- Background layer resolution / managed-asset model is documented in the
  Background Layering plan above. Old mood configs load unchanged (migration is
  in `bin/beamsettings.py`).

### Cut / Trim rule on any tag

The old "Trim () in Title" became **Cut / Trim**, applicable to any input ID3
tag with a configurable "Start from" symbol/string.

- `bin/dialogs/editruledialog.py` — rule editor (tag picker + start-from field).
- Trim logic in `bin/songclass.py`; also applied to the previous-song display.
- Legacy "Trim () in Title" rules migrate automatically on load
  (`bin/beamsettings.py`).

### Browser / network display parity

Cover-art Advanced options (corner radius, outline enable/alpha/width up to
32 px) and timed-mood backgrounds now also render on the network/browser display
and update live. See `bin/network/schema.py` (payload) and
`bin/network/service.py` (start/stop made robust across Win/Linux/macOS). The
browser cover art letterboxes (preserves aspect) instead of cropping; the
native soft "feather" edge is approximated by corner rounding in the browser.

## Played History (Session History)

Automatic per-session log of played tracks plus important non-track events.
Backend-independent: it consumes the already normalized `SongObject` / display
state, so it works for any player module.

- `bin/playedhistory.py` — `PlayedHistoryLogger`. One instance per Beam run, held
  by `NowPlayingData` (`self.playedHistory`). The session timestamp is fixed on
  the first write and never changes for the process lifetime — **one run = one
  file set**. Player/playback/blackout/display changes never start a new session.
  A `threading.Lock` serialises writes because they arrive from two threads (see
  below). Each entry is opened/appended/closed immediately so history survives an
  abrupt close.
- **Track path (worker thread):** `NowPlayingData.processData()` calls
  `playedHistory.observe(song, mood, player, status, settings)` at the end (inside
  the `processDataThread` worker). `observe()` detects player/playback
  transitions, then logs the current track only while `status == 'Playing'`.
- **Event path (main thread):** `bin/mainframe.py` calls
  `playedHistory.log_event(text, beamSettings)` via the `_logHistoryEvent` helper
  for display-opened, blackout on/off, and message shown/cleared/expired.
  `clearTempMessage(reason=...)` distinguishes manual clear from timer expiry.

**Dedup / no spam.** Tracks: a track is skipped if its identity
(title/artist/file path) equals the last logged one, or reappeared within
`DUPLICATE_WINDOW_SECONDS` (30s) — guards A→B→A flapping. Events: playback events
fire only on a real state change (`_KNOWN_STATUSES`, last-status tracking); player
events only when the selected player actually changes. Source lost/restored is
intentionally **not** emitted — not reliably distinguishable from `Stopped`.

**Outputs (UTF-8).** TXT is human-readable (`[Type] Artist - Singer > Title Year`)
with events as `# HH:MM:SS text` comment lines. CSV columns are
`timestamp,row_type,player,mood,genre,album_artist,artist,singer,title,year,album,file_path,event`;
`row_type` is `track` or `event`.

**M3U8 limitation.** The playlist stays a clean, playable list: `#EXTM3U` header +
`#EXTINF` entries only — no comments/events. A track is written **only** if it has
an absolute local file path (`os.path.isabs`). Sources without file paths (Now
Playing / SMTC / MPRIS, Spotify, network/streaming) are skipped in the `.m3u8` but
still logged to TXT/CSV. M3U8 is best-effort by design.

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
