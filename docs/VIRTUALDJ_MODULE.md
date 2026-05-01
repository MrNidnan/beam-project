# VirtualDJ Module

This fork integrates VirtualDJ through two selectable modes:

- `History File`: default mode, based on `VirtualDJ/History/tracklist.txt`
- `Network Control`: optional mode for users with the VirtualDJ Pro plugin available

## Why This Approach

The default integration now starts with VirtualDJ's local history/tracklist files because that works without requiring the Pro-only Network Control plugin. Network Control remains available as an optional advanced mode.

History File mode was chosen as the default for three reasons:

- It does not require VirtualDJ Pro.
- It stays local and cross-platform.
- It fits Beam's existing polling model with minimal platform-specific code.

Network Control remains useful when available for three reasons:

- VirtualDJ maintainers and community posts point to Network Control as the simplest supported path for external now-playing integrations.
- Beam already has polling-based backends, so the Network Control model fits the existing architecture cleanly.
- This keeps the feature maintainable across Beam's supported platforms without introducing a compiled plugin or a VirtualDJ-specific SDK dependency.

## Runtime Model

Beam supports two runtime paths.

### History File

By default, Beam reads the newest VirtualDJ history source it can find:

- an explicitly configured history file path, if you set one
- otherwise `VirtualDJ/History/tracklist.txt`
- otherwise the newest `.txt` file inside the `History` folder

Beam auto-detects common VirtualDJ home locations:

- Windows: `%LOCALAPPDATA%\VirtualDJ` and `~/Documents/VirtualDJ`
- macOS: `~/Library/Application Support/VirtualDJ` and `~/Documents/VirtualDJ`

Beam strips common timestamp prefixes such as `22:45 : Artist - Title`, parses the most recent non-empty line, and treats it as active only while the file is still fresh enough.

Default history settings in Beam:

- Integration mode: `History File`
- History file path: blank, which means auto-detect
- Recent track window: `300` seconds

Current limitations of History File mode:

- History is only recorded once VirtualDJ decides the song belongs in its history.
- It is near-now-playing, not exact deck state.
- It depends on VirtualDJ writing history/tracklist output.
- It may lag behind pause, stop, or deck changes.
- Its format depends on the user's `tracklistFormat` setting.
- Beam only reads deck `1` entries from history when deck markers are present, so deck `2` prelisten/history writes are ignored.

Recommended VirtualDJ history settings:

- Make sure `Record History` is enabled in VirtualDJ.
- Reduce `HistoryDelay` from the default `45` seconds to a lower value such as `15` seconds if you want Beam to react sooner.
- Set `tracklistFormat` to `deck=`get_deck` artist=%author genre=%genre title=%titleremix year=`get_year``so Beam can parse labeled fields directly, ignore deck`2`, and import year without guessing field order.

Recommended `tracklistFormat` example:

```text
deck=`get_deck` artist=%author genre=%genre title=%titleremix year=`get_year`
```

With that format, VirtualDJ writes lines such as:

```text
22:45 : deck=1 artist=Oscar Larroca genre=Tango title=Remolino year=1941
```

See other formats or text in virtualDj wiki:
https://virtualdj.com/wiki/Skin%20SDK%20Textzone.html

Beam reads that as:

- Deck: `1`
- Artist: `Oscar Larroca`
- Genre: `Tango`
- Title: `Remolino`
- Year: `1941`

If a later history line is written for `deck=2`, Beam skips it instead of replacing the current Beam song with a prelisten deck entry.

Backward compatibility:

- Beam still accepts legacy positional history lines such as `Artist - Title`.
- Beam still accepts the earlier deck-prefixed format `deck=1 Artist - Genre - Title`.
- The labeled `artist=... genre=... title=... year=...` format is now the preferred configuration because it avoids ambiguous splitting.

Important behavior note:

- Beam only sees the song after VirtualDJ has written it to history.
- With VirtualDJ defaults, that usually means Beam will not see the track until about `45` seconds of playback.
- If you reduce `HistoryDelay`, Beam will pick the track up earlier, but it is still reading history after the fact rather than live deck state.

### Network Control

When enabled, Beam polls the VirtualDJ Network Control `/query` endpoint and reads plain-text responses.

Current query modes:

- `Master`: `deck master is_audible ? deck master get_artist_title : get_text ''`
- `Deck 1`: `deck 1 is_audible ? deck 1 get_artist_title : get_text ''`
- `Deck 2`: `deck 2 is_audible ? deck 2 get_artist_title : get_text ''`
- `Left`: `deck left is_audible ? deck left get_artist_title : get_text ''`
- `Right`: `deck right is_audible ? deck right get_artist_title : get_text ''`

Beam first checks whether the selected deck is audible and then enriches the current `SongObject` with per-field metadata queries.

Current metadata mapping:

- `Artist`
- `Title`
- `Album`
- `Genre`
- `Year`
- `FilePath`

Current limitations of Network Control mode:

- A non-audible deck is treated as stopped.
- Beam does not currently call `/execute`; it is read-only.
- Metadata enrichment uses multiple `/query` calls after the audible check instead of one composite script.

## User Setup

### History File

VirtualDJ requirements:

- A normal VirtualDJ installation that writes to its History folder
- `Record History` enabled in VirtualDJ

Beam setup:

1. Open `Preferences -> Basic Settings`.
2. Select `VirtualDJ` as the media player.
3. Choose `History File` as the integration.
4. Leave `History File Path` blank for auto-detection, or enter a specific `tracklist.txt` path or `History` folder.
5. In VirtualDJ, make sure history recording is enabled, set `tracklistFormat` to `deck=`get_deck` artist=%author genre=%genre title=%titleremix year=`get_year``, and lower `HistoryDelay` if you want Beam to react faster.
6. Adjust `Recent Track Window (sec)` if you want Beam to forget stale entries faster or slower.

### Network Control

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
3. Choose `Network Control` as the integration.
4. Enter the host, port, and optional bearer token.
5. Pick the track source Beam should follow. Beam supports `Master`, `Deck 1`, `Deck 2`, `Left`, and `Right`.

Default Network Control settings in Beam assume:

- Host: `127.0.0.1`
- Port: `80`
- Query mode: `Master`

## Files Involved

- `bin/modules/virtualdjmodule.py`: shared VirtualDJ backend with History File and Network Control modes
- `bin/nowplayingdata.py`: module dispatch
- `bin/beamsettings.py`: VirtualDJ settings facade
- `bin/dialogs/preferencespanels/basicsettingspanel.py`: user-facing VirtualDJ settings controls
- `resources/json/beamconfig.json`: default config schema and module availability
- `scripts/smoke_virtualdj.py`: smoke test covering both History File and Network Control modes in CI

## Future Extension Points

If Beam needs better non-Pro fidelity later, the next likely step is to improve the history-file parser around timestamp handling, stale detection, and alternate `tracklistFormat` layouts.

If Beam needs more metadata in Pro mode later, the safest next step is still to stay on `/query` rather than introducing a native plugin. If the request volume becomes a problem, the next optimization step is to replace the current per-field queries with a single composite `get_text` script.

Potential follow-up work:

- improve parsing for more `tracklistFormat` variants
- add an explicit home-folder override in addition to the history file path override
- query remix/comment/filename data and map it into `SongObject`
- support additional deck targeting modes beyond `Master`, `Deck 1`, `Deck 2`, `Left`, and `Right`
- surface connection failures more explicitly in the UI
