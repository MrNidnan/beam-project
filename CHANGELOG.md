# Changelog

All notable changes in this fork are documented in this file.

The format is based on Keep a Changelog, adapted for this repository's existing release history.

## v0.8.0 - 2026-05-01

### Added

- Updated Beam so your current configuration can be organized into reusable named profiles instead of a single setup.
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

- Added Preferences controls for the Network Display service, including enable/disable, bind host, and configurable port settings.
- Added browser projection refinements for distance reading, including automatic title scaling for long song names.

## v0.7.0 - 2026-04-23

### Breaking Changes

- Replaced the legacy foobar2000 integration path with the Beefweb HTTP API integration.
- Dropped compatibility with the older deprecated foobar2000 plugin path used by previous Beam setups.

### Migration

- Install and enable the Beefweb foobar2000 component.
- Configure Beam to reach Beefweb through `BEAM_BEEFWEB_URL` and optional authentication environment variables.
- Review [FOOBAR_MODULE.md](FOOBAR_MODULE.md) before upgrading an existing foobar2000 setup.

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
