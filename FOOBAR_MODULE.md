Beam now reads foobar2000 through the Beefweb HTTP API instead of the legacy COM automation path.

If you are upgrading from an older Beam setup, note that this fork no longer supports the previous deprecated foobar2000 plugin path. Existing users should install Beefweb before moving to `v0.7.0`.

Check officiaal documentation and foobar componet at:
https://www.foobar2000.org/components/view/foo_beefweb

https://github.com/hyperblast/beefweb/blob/master/README.md

# What It Does

The adapter lives in `bin/modules/win/foobar2kmodule.py`. Beam calls `run(max_tanda_length)` from `bin/nowplayingdata.py` and expects two values back:

- a playlist of `SongObject` items
- a Beam playback status string such as `Playing`, `Paused`, `Stopped`, or `PlayerNotRunning`

The rest of Beam stays unchanged. That is the key design constraint.

Runtime Flow

1. Beam calls `run(max_tanda_length)`.
2. The module checks whether `foobar2000.exe` is running.
3. The module calls Beefweb `GET /player` with a list of title-format expressions to fetch player state and the current item.
4. If Beefweb returns an active playlist and item index, the module calls `GET /playlists/{playlistId}/items/{offset}:{count}` to fetch the currently playing song plus the next items.
5. The module converts each returned Beefweb item into Beam's `SongObject`.
6. Beam applies its normal rules, cortina logic, and display rendering.

API Endpoints Used

- `GET /player`
  Returns `playbackState` and `activeItem`.
- `GET /playlists/{playlistId}/items/{offset}:{count}`
  Returns a slice of the active playlist beginning at the current song.

The implementation requests these columns in order:

- `[%artist%]`
- `[%album%]`
- `[%title%]`
- `[%genre%]`
- `[%comment%]`
- `[%composer%]`
- `[%date%]`
- `[%album artist%]`
- `[%performer%]`
- `[%path%]`

That list maps directly onto Beam's `SongObject` fields.

Configuration

Beam now supports saved Foobar2000 Beefweb settings in the main Preferences UI when `Foobar2000` is the selected media player.

Open `Settings`, choose `Foobar2000` as the media player, and Beam will show the `Foobar2000 Beefweb` section directly below the media-player selector.

- `Beefweb URL`
  Default: `http://localhost:8880/`
- `Beefweb Username`
  Optional username if Beefweb authentication is enabled.
- `Beefweb Password`
  Optional password if Beefweb authentication is enabled.

These settings are stored in Beam configuration as:

```json
"Foobar2000": {
  "BeefwebUrl": "http://localhost:8880/",
  "BeefwebUser": "",
  "BeefwebPassword": ""
}
```

These values are stored in Beam configuration and used by the foobar module at runtime.

Beam first reads the saved Preferences values. Environment variables are only used as a fallback for older setups that have not moved to the saved settings yet.

Environment variables are still accepted as a fallback for older setups:

- `BEAM_BEEFWEB_URL`
  Default fallback: `http://localhost:8880/`
- `BEAM_BEEFWEB_USER`
  Optional username if Beefweb authentication is enabled.
- `BEAM_BEEFWEB_PASSWORD`
  Optional password if Beefweb authentication is enabled.
- `BEAM_BEEFWEB_TIMEOUT`
  Optional request timeout in seconds. Default: `2.0`

Example PowerShell session:

```powershell
$env:BEAM_BEEFWEB_URL = "http://localhost:8880/"
$env:BEAM_BEEFWEB_USER = ""
$env:BEAM_BEEFWEB_PASSWORD = ""
python .\beam.py
```

How The Playlist Logic Works

Beam's tanda logic is already implemented outside the foobar module. The only thing the foobar module needs to do is return enough songs in playback order.

The Beefweb implementation therefore returns:

- current song at index `activeItem.index`
- next items up to `max_tanda_length`

That is enough for Beam to populate:

- current song tags
- next song tags
- next tanda tags

No changes are required in the display pipeline for that part.

Failure Behavior

- If foobar2000 is not running, Beam returns `PlayerNotRunning`.
- If playback is paused, Beam keeps the last song and active mood on screen.
- If playback is stopped, Beam clears the current song display and falls back to the default or not-playing mood.
- If Beefweb is unreachable or misconfigured, Beam returns `BeefwebUnavailable` unless it already managed to recover current-song data.
- If playlist slicing fails but the player response contains current track columns, Beam can still project the current song.

How To Extend It

Add more metadata:

1. Add another Beefweb column expression in `BEAM_BEEFWEB_COLUMNS`.
2. Map the returned column to a `SongObject` field.
3. If it is a brand new Beam field, also update `bin/songclass.py`, `bin/nowplayingdata.py`, and the layout editor tags.

Improve configuration:

1. Add Beefweb URL, username, password, and timeout to Beam config.
2. Expose those settings in the preferences UI.
3. Replace the environment-variable reads in the foobar module with Beam settings accessors.

Support artwork:

1. Call `GET /artwork/current` or `GET /artwork/{playlistId}/{index}`.
2. Convert the returned bytes into an image object Beam can render.
3. Keep this logic in the foobar module or a small helper to avoid leaking Beefweb details into the UI layer.

Rules and title cleanup

Beam applies its normal rules after reading metadata from foobar2000. This includes the default disabled rule `Trim () in the Title`.

When that rule is enabled in the Rules panel, Beam removes trailing parenthetical suffixes from song titles before display. Example:

- `Malena (Take 1)` becomes `Malena`
- `La Cumparsita (Alt. take) (test press)` becomes `La Cumparsita`

The rule is optional and disabled by default, so Beam preserves the original title unless you enable it.
