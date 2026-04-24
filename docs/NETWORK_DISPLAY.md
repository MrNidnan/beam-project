# Network Display Adapter

Beam now includes an optional browser adapter for projecting the current display state to tablets, phones, or any browser-capable device on the same network.

The current tablet client is optimized for distance reading. It renders the current artist or mood, a centered title with automatic down-scaling for long names, the song year when available, the previous song title, and an optional background image.

## Goals

- Keep the wxPython desktop renderer as the source of truth.
- Expose a read model for browser clients without changing player modules.
- Preserve backwards compatibility by leaving the feature disabled by default.
- Support Windows, Linux, and macOS from the same in-process server implementation.

## Module Layout

- `bin/network/service.py`: lifecycle and publish API used by Beam.
- `bin/network/schema.py`: serializes Beam state into a browser-safe snapshot.
- `bin/network/events.py`: event metadata and protocol versioning.
- `resources/web/tablet`: minimal HTML, CSS, and JS dashboard.

The service is started and stopped from the main desktop frame. Configuration changes are applied through Beam settings, including the Preferences panel fields for enabling the service and setting the bind host and port.

## Configuration

Additions to `beamconfig.json`:

```json
"NetworkService": {
  "Enabled": "False",
  "Host": "0.0.0.0",
  "Port": 8765,
  "WebRoot": "resources/web/tablet"
}
```

`Enabled` defaults to `False`, so existing Beam installs continue to behave exactly as before.

The default network service port is `8765`. You can keep that value or change it from Beam Preferences under `Settings` -> `Network Display` using the `Port` field.

## HTTP API

### `GET /`

Serves the tablet dashboard.

### `GET /media/background/current`

Returns the currently selected Beam background image when one is available, otherwise returns `404 Not Found`.

### `GET /static/*`

Serves the tablet client assets from `resources/web/tablet`.

### `GET /now-playing`

Returns the latest serialized state document:

```json
{
  "protocolVersion": 1,
  "schemaVersion": "2026-04-24",
  "sequence": 7,
  "snapshot": {
    "module": "Foobar2000",
    "playbackStatus": "Playing",
    "previousPlaybackStatus": "Paused",
    "statusMessage": "Playing",
    "moodName": "Default",
    "background": {
      "available": true,
      "sourcePath": "C:/.../background.jpg",
      "url": "/media/background/current"
    },
    "displayRows": ["..."],
    "displayItems": [
      {
        "index": 0,
        "text": "La Cumparsita",
        "field": "%Title",
        "active": "yes",
        "alignment": "Center",
        "font": "Georgia",
        "fontColor": "(255, 255, 255, 255)",
        "size": 10,
        "style": "Normal",
        "weight": "Bold",
        "position": [48, 50],
        "hideControl": "",
        "textFlow": "Cut"
      }
    ],
    "currentSong": {
      "title": "La Cumparsita",
      "artist": "Rodriguez",
      "album": "Golden Age",
      "genre": "Tango",
      "year": "1939-09-22",
      "albumArtist": "Rodriguez",
      "isCortina": "no",
      "filePath": "C:/Music/La Cumparsita.mp3",
      "ignoreSong": "no"
    },
    "previousSong": {
      "title": "El Once",
      "artist": "Di Sarli"
    },
    "nextSong": {
      "title": "Bahia Blanca",
      "artist": "Di Sarli"
    },
    "nextTandaSong": null,
    "playlist": [],
    "displayTimer": 0,
    "coverArtAvailable": false
  }
}
```

Important notes:

- `sequence` starts at `0` and increases only when the serialized snapshot changes.
- `currentSong`, `previousSong`, `nextSong`, and `nextTandaSong` all use the same song object shape.
- Song objects can include `artist`, `album`, `title`, `genre`, `comment`, `composer`, `year`, `singer`, `albumArtist`, `performer`, `isCortina`, `filePath`, `moduleMessage`, and `ignoreSong`.
- Empty state responses return the same envelope with `currentSong` and related song fields set to `null` and arrays left empty.

## WebSocket Protocol

### `GET /events`

Upgrades to a WebSocket connection. Beam immediately sends a `session.hello` event with the current snapshot, then pushes `state.updated` events only when the serialized snapshot changes.

Initial event:

```json
{
  "type": "session.hello",
  "protocolVersion": 1,
  "schemaVersion": "2026-04-24",
  "sequence": 7,
  "timestamp": "2026-04-24T20:41:00Z",
  "snapshot": {}
}
```

Update event:

```json
{
  "type": "state.updated",
  "protocolVersion": 1,
  "schemaVersion": "2026-04-24",
  "sequence": 8,
  "timestamp": "2026-04-24T20:41:05Z",
  "snapshot": {}
}
```

## Event Model

- The adapter publishes from `MainFrame.refreshDisplay()`.
- Saving settings can restart the service with the new host or port and republish the current state.
- The desktop UI remains authoritative; the browser reads a serialized copy only.
- Duplicate snapshots are suppressed by comparing the serialized JSON payload.
- Multiple clients can connect simultaneously with no change to Beam's player integration model.

## Tablet Client Behavior

- The tablet page fetches `/now-playing` on load, then switches to `/events` for live updates.
- The browser requests fullscreen and screen wake lock on user interaction.
- If the WebSocket connection drops, the client reconnects with exponential backoff.
- Background imagery is loaded from `/media/background/current` when the snapshot marks it as available.
- The client applies tango, vals, and milonga theme variants based on the current song genre.
- The primary reading order is artist or mood, centered title, song year, then previous song.
- Long titles are automatically reduced in size to avoid awkward wrapping.

## Compatibility Notes

- Existing Beam workflows remain unchanged unless `NetworkService.Enabled` is turned on.
- The adapter uses `aiohttp` and a background thread, so it does not depend on a platform-specific media module.
- No changes were made to the now-playing module contracts.
