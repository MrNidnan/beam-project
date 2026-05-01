# Network Display Adapter

Beam now includes an optional browser adapter for projecting the current display state to tablets, phones, or any browser-capable device on the same network.

The current tablet client is optimized for distance reading. It renders the configured mood layout directly from `displayItems`, including `%CoverArt`, and keeps optional layered backgrounds made of a mood base layer plus an artist overlay.

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

### `GET /media/background/base`

Returns the current base background image used by the browser projection when one is available, otherwise returns `404 Not Found`.

### `GET /media/cover-art/current`

Returns the current track's cover art image when the active layout includes `%CoverArt` and art is available, otherwise returns `404 Not Found`.

### `GET /media/background/overlay`

Returns the current overlay background image used by the browser projection when one is available, otherwise returns `404 Not Found`.

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
      "url": "/media/background/current",
      "base": {
        "available": true,
        "sourcePath": "C:/.../resources/backgrounds/curtain.jpg",
        "currentPath": "",
        "url": "/media/background/base",
        "reference": "asset:builtin/backgrounds/curtain.jpg",
        "canonicalReference": "asset:builtin/backgrounds/curtain.jpg",
        "relativePath": "backgrounds/curtain.jpg",
        "scope": "builtin",
        "kind": "asset",
        "rotate": "no",
        "rotateTimer": 120,
        "mode": "base",
        "opacity": 100,
        "name": "Default",
        "field": "",
        "matchedField": "",
        "operator": "",
        "value": ""
      },
      "overlay": {
        "available": true,
        "sourcePath": "C:/Users/.../.beam/backgrounds/orchestras/di-sarli.jpg",
        "currentPath": "",
        "url": "/media/background/overlay",
        "reference": "asset:user/backgrounds/orchestras/di-sarli.jpg",
        "canonicalReference": "asset:user/backgrounds/orchestras/di-sarli.jpg",
        "relativePath": "backgrounds/orchestras/di-sarli.jpg",
        "scope": "user",
        "kind": "asset",
        "rotate": "no",
        "rotateTimer": 120,
        "mode": "blend",
        "opacity": 40,
        "name": "Carlos Di Sarli",
        "field": "%AlbumArtist",
        "matchedField": "%AlbumArtist",
        "operator": "is",
        "value": "Carlos Di Sarli"
      }
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
    "coverArt": {
      "available": true,
      "url": "/media/cover-art/current",
      "sourcePath": "C:/Music/La Cumparsita.mp3"
    },
    "coverArtAvailable": true
  }
}
```

Important notes:

- `sequence` starts at `0` and increases only when the serialized snapshot changes.
- `currentSong`, `previousSong`, `nextSong`, and `nextTandaSong` all use the same song object shape.
- Song objects can include `artist`, `album`, `title`, `genre`, `comment`, `composer`, `year`, `singer`, `albumArtist`, `performer`, `isCortina`, `filePath`, `moduleMessage`, and `ignoreSong`.
- Empty state responses return the same envelope with `currentSong` and related song fields set to `null` and arrays left empty.
- `background.base` and `background.overlay` mirror the desktop layer model.
- `background.base.currentPath` and `background.overlay.currentPath` are populated when folder rotation is active and the browser should fetch the current rotated file rather than the source directory.
- Artist overlay matching follows Beam's layered background rules: `%AlbumArtist` first, then `%Artist` as fallback when `%AlbumArtist` is empty.
- `coverArt.url` is a stable route; append the current `sequence` as a query string when you need to bust browser caches after track changes.

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
- Background imagery is loaded from `/media/background/base` and `/media/background/overlay` when the snapshot marks those layers as available.
- In `blend` mode the overlay is rendered above the base background with the configured opacity.
- In `replace` mode the browser suppresses the base layer and renders the overlay as the effective full background.
- The client applies tango, vals, and milonga theme variants based on the current song genre.
- The client renders the configured mood layout directly from `displayItems`, including `%CoverArt`, instead of using a fixed title-only composition.
- Text layout, alignment, wrapping, and sizing follow the serialized `displayItems` rows so browser output stays close to the desktop renderer.
- When no layout items are configured, the client falls back to a simple waiting-state composition.

## Compatibility Notes

- Existing Beam workflows remain unchanged unless `NetworkService.Enabled` is turned on.
- The adapter uses `aiohttp` and a background thread, so it does not depend on a platform-specific media module.
- No changes were made to the now-playing module contracts.

## Migration Notes

- Older profiles that still store mood or artist backgrounds as `resources/backgrounds/...` continue to load.
- Beam normalizes those bundled paths in memory to `asset:builtin/...` and persists the canonical form on the next normal save.
- Existing absolute paths are preserved for compatibility until the user explicitly replaces or imports them.
