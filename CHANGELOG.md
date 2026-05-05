# Changelog

All notable changes in this fork are documented in this file.

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
