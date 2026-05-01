# VirtualDJ Module

This fork integrates VirtualDJ through the official Network Control plugin instead of a custom native plugin.

## Why This Approach

The integration was intentionally built around VirtualDJ's HTTP-based Network Control plugin for three reasons:

- VirtualDJ maintainers and community posts point to Network Control as the simplest supported path for external now-playing integrations.
- Beam already has polling-based backends, so the Network Control model fits the existing architecture cleanly.
- This keeps the feature maintainable across Beam's supported platforms without introducing a compiled plugin or a VirtualDJ-specific SDK dependency.

## Runtime Model

Beam polls the VirtualDJ Network Control `/query` endpoint and reads plain-text responses.

Current query modes:

- `Master`: `deck master is_audible ? deck master get_artist_title : get_text ''`
- `Deck 1`: `deck 1 is_audible ? deck 1 get_artist_title : get_text ''`
- `Deck 2`: `deck 2 is_audible ? deck 2 get_artist_title : get_text ''`

Beam first checks whether the selected deck is audible and then enriches the current `SongObject` with per-field metadata queries.

Current metadata mapping:

- `Artist`
- `Title`
- `Album`
- `Genre`
- `Year`
- `FilePath`

Current limitations:

- A non-audible deck is treated as stopped.
- Beam does not currently call `/execute`; it is read-only.
- Metadata enrichment uses multiple `/query` calls after the audible check instead of one composite script.

## User Setup

VirtualDJ requirements:

- VirtualDJ 2023 or later
- A VirtualDJ Pro license
- The `Network Control` extension installed from `Config -> Extensions`

Plugin setup in VirtualDJ:

1. Open the `Master` panel.
2. In the `Auto-Start` section, enable `Network Control`.
3. Open the plugin settings with the cog wheel.
4. Configure the port Beam should use.
5. Optionally configure an authentication token.

Beam setup:

1. Open `Preferences -> Basic Settings`.
2. Select `VirtualDJ` as the media player.
3. Enter the host, port, and optional bearer token.
4. Pick the track source Beam should follow.

Default settings in Beam assume:

- Host: `127.0.0.1`
- Port: `80`
- Query mode: `Master`

## Files Involved

- `bin/modules/virtualdjmodule.py`: HTTP polling backend for VirtualDJ Network Control
- `bin/nowplayingdata.py`: module dispatch
- `bin/beamsettings.py`: VirtualDJ settings facade
- `bin/dialogs/preferencespanels/basicsettingspanel.py`: user-facing VirtualDJ settings controls
- `resources/json/beamconfig.json`: default config schema and module availability
- `scripts/smoke_virtualdj.py`: mocked end-to-end query-flow smoke test used in CI

## Future Extension Points

If Beam needs more metadata later, the safest next step is still to stay on `/query` rather than introducing a native plugin. If the request volume becomes a problem, the next optimization step is to replace the current per-field queries with a single composite `get_text` script.

Potential follow-up work:

- query remix/comment/filename data and map it into `SongObject`
- support more than two fixed deck targets
- surface connection failures more explicitly in the UI
