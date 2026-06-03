# Changelog

All notable changes in this fork are documented in this file.

## v0.9.3.0 - 2026-06-03

### Added

- New player: Now Playing (SMTC / MPRIS)
  An OS-level, app-agnostic "Now Playing" reader — no per-app integration, offline.
  Windows reads the SMTC session (the volume/media flyout); Linux reads MPRIS over
  D-Bus. One **Now Playing** module backed by a platform facade
  (`bin/modules/nowplayingsource.py`) that picks `smtcmodule` on Windows and
  `mprismodule` on Linux. The Linux backend prefers `dbus-next` and falls back to
  `dbus-python` (already a Linux dependency), so it works without the new package.
  Preferences offer a **Source app** picker (Detect / Active session) and a test
  button; album art is read when the app provides it (genre when present).

- Live display controls: Blackout and temporary Message
  Two manual overrides next to the Display button:
  - **Show Message** opens a dialog
    to display a centered message (5–60s, default 15s) on display; it auto-clears on expiry, and the button toggles to **Clear Message** to remove it early.
  - **Blackout** turns the output fully black and the button toggles to **Resume**; a temporary message still renders on top of the blackout. These overrides are not persisted and reset to inactive on startup; moods, rules, player state and background rotation keep running underneath.
    The status bar now reports state as
    `Player: ... | Mood: ... | Display: ON/OFF/BLACKOUT | [Message: Ns |] Network: ON/OFF`.

- Cut / Trim rule applies to any field
  The "Trim () in Title" rule is now "Cut / Trim" and works on any input tag, not
  just the title. The start symbol field ("Start from"), can be a single character or more.

- Blurr dimm existing background on timed moods
  Example:
  Steps:
  1. Add the default mood slider presentation images with no text
  2. Add a mood with the text you want with a duration for X seconds
  3. select background "Keep existing" and a readability to blurr the background

  Mood backgrounds now have a "Readability" control. The mood editor's Background
  options are "Keep existing", "Image" and "Color". "Keep existing" leaves the
  background that is already on screen unchanged — useful for timed message moods
  (e.g. LAST TANDA) that should overlay text without swapping the background. When
  selected, a single "Readability" slider (0–100) applies a combined blur + dark
  overlay to that background so on-screen text is easier to read (0 = no change,
  100 = strong blur and darkening). "Image" and "Color" continue to use the mood's
  own background as before. Works on both the native (wx) and network/browser
  displays. Old mood configurations continue to load unchanged.

### Changed

- Reworked the mood editor Background section for clarity. The background type is now
  chosen from a single **Background type** dropdown — **Keep existing**, **Color**,
  **Single image**, or **Image slideshow** — and only the controls for the selected
  type are shown, keeping the dialog compact. The rotation interval / random-order
  options now live inside **Image slideshow** instead of a separate "Background
  Rotation" group. Existing moods load into the matching type automatically (single
  image, rotating folder, color, or keep-existing).

### Fixed

- Rotating backgrounds refresh work like a charm now.
- Alignment with backgrounds, cover art images and opacity settings between web display and normal display
- Cover art Advanced display options (corner radius, outline enable/alpha/width) now
  apply to the network/browser display and update live, matching the native display.
  The browser cover art also preserves aspect ratio (letterbox) like the native render
  instead of cropping to a square. (Feather is approximated by corner rounding in the browser.)
- Some other comestic issues in Windows / Linux

## v0.9.2.1 - 2026-05-31

### Fixed

- iTunes windows 11 module improved stablity and logging

## v0.9.2.0 - 2026-05-15

### Added

- Removed main Save button and switch the UI to a fully auto-save model. Any change in the ui should be relfected inmediately in the display

### Changed

- doc: update, Temporary Messages on Display Tags.md

### Fixed

- Network consitency on displaying background and typographies
- Check on/off custom and timed moods. Mood duration will reset and enable the timer again once select

## v0.9.1.2 - 2026-05-10

### Added

- The “Trim () in Title” rule is now configurable by start symbol.
  - symbol ( trims Song "Title (Live)" to Song "Title"
  - symbol - trims Song "Title - Live" to Song "Title"

## v0.9.1.1 - 2026-05-08

### Added

- The layout-item hide condition now supports tag / operator / value instead of only “tag is empty”.
  • is and is not accept comma-separated values in the layout hide condition.

  Example:
  %PreviousGenre is Milonga, Tango, Vals

  This is evaluated as: genre is milonga or tango or vals

### Changed

- Windows JRiver module now respects max_tanda_length in both paths and avoids repeated target-zone resolution work

## v0.9.1.0 - 2026-05-08

### Added

- Add a feature that allows using Cover Art/ Album Art as the Artist background
  - coverArt background take the default mode for "blend/replace" and the default opacity for displaying.
  - if specific background artist is defined, will overrule coverArt brackground
    ![cover_art_as_background](docs/images/user-manual/beam_artist_background.png)
- **JRiver**: reads singer custom tag from jriver module, reads composer
- Add an option to define a uniform color for the background instead of a picture.

### Fixed

- Preserve the ratio of CoverArt, don't make them all square
- Fix coverArt rounding displaying
- Avoid UI flicker when updating display visualization while changing settings

## v0.9.0.1 - 2026-05-05

### Fixed

- macOs failed on start

## v0.9.0.0 - 2026-05-04

### Added

- **Custom backgrounds per album artist / artist**, including reworked background settings.
  - Supports layered rendering with mood backgrounds and artist-specific overlays.
  - Artist backgrounds can blend with mood backgrounds using configurable opacity/blend mode, or replace them entirely.
- Browser and tablet projection support for layered backgrounds.
- Imported mood and orchestra backgrounds are stored under `~/.beam/backgrounds/...` and referenced as `asset:user/...`.
- **JRiver** support updated for macOS and Windows, with Zone support for preview listening without beaming.
- **CoverArt** settings for optional outline, border radius, and feathering.
- **VirtualDJ** deck selector and CoverArt support for history parsing.
- **AIMP** windows support

### Changed

- Modernized **Mixxx** integration.
- Reworked settings UI:
  - Basic settings layout.
  - Layout configuration screen.
  - Edit Mood dialog.
  - Edit Layout Item dialog.
- Edit Layout Item changes are now shown automatically and immediately in the display.
- Long titles now wrap instead of being truncated.

### Fixed

- Resolved overlapping issues caused by wrapped titles in desktop layouts.
- Fixed `%CoverArt` rendering by using integer image scaling sizes for cross-platform compatibility.
- Improved Foobar2000 startup reliability and diagnostics on Windows.
- Fixed compatibility with older background configurations and rotating backgrounds.
- Fixed Mood "Display Timer" behavior. (also renamed to Mood Timing)

## v0.8.0.0 - 2026-05-01

### Added

- **Support for VirtualDJ integration**, including history parsing and network control functionality.
- **Profiles settings configutarion** configuration can be organized in named profiles instead of a single setup.
- Added profile management in Preferences so you can create, save, switch, rename, and delete named Beam setups.
- Added clearer feedback for the active profile, including an unsaved-changes indicator.
- Updated the Preferences window with a dedicated Profiles page.
- Older Beam configurations and existing users should be able to move to profiles without losing their current setup and transparently

### Fixed

- Fixed several startup and refresh issues around settings and the new profile workflow.

## v0.7.1.2 - 2026-04-30

### Fixed

- Fixed Windows executable startup failures on non-UTF-8 system locales by loading bundled JSON resources and config files with explicit UTF-8 encoding.

## v0.7.1.1 - 2026-04-24

### Added

- Added saved Foobar2000 Beefweb settings in Beam Preferences for URL, username, and password.
- Added a default disabled rule named `Trim () in the Title` to remove trailing parenthetical suffixes from song titles when enabled.
- Added a local network address hint in Network Display settings so users can see the reachable browser URL without using external OS commands.

### Changed

- Updated the Foobar2000 integration to read saved Beefweb settings from Beam configuration before falling back to environment variables.
- Updated the Rules UI to expose the new optional title-trimming rule.
- Updated the Network Display settings UI to show a detected local IP address while preserving wildcard bind behavior for `0.0.0.0`.
- Updated the README, Foobar2000 documentation, and user wiki to reflect the saved Foobar settings and the new default rule.

### Fixed

- Improved Foobar2000 Beefweb error logging to include the failing request URL and response body when available.
- Avoided invalid Beefweb playlist slice requests when foobar2000 does not report a valid active playlist reference.

## v0.7.1 - 2026-04-24

### Added

- Add http display service and a browser projection view

## v0.7.0 - 2026-04-23

### Breaking Changes

- Replaced the legacy foobar2000 integration path with the Beefweb HTTP API integration.
- Dropped compatibility with the older deprecated foobar2000 plugin path used by previous Beam setups.

### Migration

- Install and enable the Beefweb foobar2000 component.
- Configure Beam to reach Beefweb through `BEAM_BEEFWEB_URL` and optional authentication environment variables.
- Review [docs/FOOBAR_MODULE.md](docs/FOOBAR_MODULE.md) before upgrading an existing foobar2000 setup.

### Added

- Added updated foobar2000 support and repository documentation for the foobar module.
- Added project-level dependency tracking via `requirements.txt`.
- Added a local wiki snapshot covering user guidance, developer notes, releases, FAQ, known bugs, display tags, DMX notes, contact information, and project background.
- Added `.gitignore` for local development artifacts.

### Changed

- Updated the Windows foobar2000 integration to improve current track extraction and compatibility handling.
- Updated `README.md` to document local setup and optional Icecast support.
- Updated string resources and now-playing handling to align with the foobar2000 changes.

### Fixed

- Mediamonkey plugin to use latest version 2024
- If Genre tag was null or empty, song was not computed as cortina if the rule was set to "cortina when %genre is not Tango, milonga, vals"
- Foobar2000 and other ID3-based files now accept front-cover APIC frames with non-empty descriptions for `%CoverArt`, instead of only the legacy `APIC:` key.
- Preserved the last song and active mood while playback is paused, and switched back to the default or not-playing mood when playback is stopped.
- Fixed Windows startup behavior so the optional Icecast backend is lazy-loaded instead of being required just to launch the application.
