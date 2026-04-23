# Changelog

All notable changes in this fork are documented in this file.

The format is based on Keep a Changelog, adapted for this repository's existing release history.

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
