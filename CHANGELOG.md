# Changelog

All notable changes in this fork are documented in this file.

The format is based on Keep a Changelog, adapted for this repository's existing release history.

## v0.6.3 - 2026-04-23

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

- Fixed startup behavior so the optional Icecast backend is lazy-loaded instead of being required just to launch the application.
