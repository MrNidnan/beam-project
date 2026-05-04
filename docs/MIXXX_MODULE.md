# Mixxx Module

Beam integrates with Mixxx by reading the local `mixxxdb.sqlite` database.

This keeps the integration local and cross-platform, but it also means Beam only sees the Auto DJ playlist and history state that Mixxx has already written into sqlite. Beam does not have a live deck-control API for Mixxx.

## Runtime Model

Beam supports one runtime path for Mixxx today:

- `SQLite database`: Beam opens the Mixxx library database read-only, reads the Auto DJ playlist queue, and uses the newest history row as the first item when Mixxx exposes one.

Current metadata mapping:

- `Artist`
- `Album`
- `Title`
- `Genre`
- `Comment`
- `Composer`
- `Year`
- `AlbumArtist`
- `FilePath`

If Beam detects an older Mixxx schema that does not include optional fields such as `comment`, `composer`, or `album_artist`, Beam still loads the song and queue rows and leaves those fields blank.

If the Mixxx database is truly incompatible and is missing required columns such as `title` or `location`, Beam treats that as a backend failure and reports the missing required columns in diagnostics instead of trying to guess.

## Database Path Resolution

Beam prefers the traditional per-platform Mixxx database path first and then falls back to other common locations used by newer versions.

Preferred default paths:

- Windows: `%LOCALAPPDATA%\Mixxx\mixxxdb.sqlite`
- macOS: `~/Library/Containers/org.mixxx.mixxx/Data/Library/Application Support/Mixxx/mixxxdb.sqlite`
- Linux: `~/.mixxx/mixxxdb.sqlite`

Additional auto-detected paths:

- Windows: `%APPDATA%\Mixxx\mixxxdb.sqlite`
- macOS: `~/Library/Application Support/Mixxx/mixxxdb.sqlite`
- Linux: `~/.local/share/mixxx/mixxxdb.sqlite`

You can override the database path in `Preferences -> Basic Settings -> Mixxx`.

## Status Model

Beam reports these Mixxx states:

- `Playing`: Beam found a current Mixxx history-first or Auto DJ playlist snapshot.
- `Unknown`: Beam could open the database, but sqlite alone could not prove whether Mixxx is paused or stopped.
- `No database`: Beam could not find or open the configured/auto-detected database.
- `PlayerNotRunning`: Windows only, when the Mixxx process is not running.

Important limitation:

- Beam can infer current playback from sqlite, but it cannot distinguish pause from stop with confidence when Mixxx has not written fresh playlist rows.

## Metadata Source Reporting

Beam reports where the current Mixxx metadata came from:

- `History row plus Auto DJ queue`: the first song comes from Mixxx history and the remaining songs come from the Auto DJ playlist
- `Auto DJ queue`: Mixxx did not expose a current history row, so Beam is using the Auto DJ queue only
- `Mixxx sqlite library metadata`: generic fallback when Beam can read tags but not classify the queue source further

The Mixxx `Run test` button in Beam shows:

- selected database path
- path source (`default`, `auto`, `configured`, or `explicit`)
- metadata source
- schema flavor (`current` or `legacy-optional-columns-missing`)
- current song diagnostics

## Current Limitations

- Beam does not control Mixxx and does not call a live network API.
- Pause and stop are not reliably distinguishable from sqlite alone.
- Next tanda detection can be wrong when Beam is reading a history-first Mixxx snapshot, because the first row comes from already-played history and the remaining rows come from the current Auto DJ queue.
- The current queue query expects the Mixxx tables `Playlists`, `PlaylistTracks`, `library`, and `track_locations` to exist.

## Diagnostics And Testing

Beam includes a smoke test for Mixxx in `scripts/smoke_mixxx.py`.

That smoke test covers:

- auto-detected database paths
- explicit database path overrides
- legacy schema handling for missing optional library columns
- broken schema handling for missing required library columns
- `Unknown`, `No database`, and `PlayerNotRunning` status paths
- propagation of Mixxx diagnostics into `NowPlayingData.StatusMessage`
