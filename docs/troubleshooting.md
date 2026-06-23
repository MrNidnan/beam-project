# Troubleshooting

Start with the symptom you see. If you are still stuck, the log file is the best
thing to share when asking for help.

## Where to find and open logs

Beam writes `beamlog.txt` in your user home folder under `.beam`.

You can acces to it an visualize it in realtime through the built-in viewer: **`Help > Open Log Viewer`**

### Log level

Log verbosity can be changed in settings `Logging > Log Level`

- `Info` — normal day-to-day use
- `Debug` — when troubleshooting or to report a bug.

If something is failing, switch to `Debug`, reproduce the problem once, then check
`beamlog.txt` (or the Log Viewer) again.

## Player not detected / Beam opens but shows no song

Check:

- the correct music player is selected in `Settings`
- the player is actually running and a song is playing
- you clicked `Apply` after changing settings
- the player-specific setup is complete (see [Player Support](../player-support))

![Beam open with no active song in the preview](../images/user-manual/beam_empty_preview.png)

## Wrong song, or the display does not update

Check:

- the player-specific setup is complete
- the connection settings are correct
- Beam is using the right integration mode (for example VirtualDJ History vs
  Network Control)
- the player is not paused or stopped

## No track info from certain players

Some sources only expose a few fields. **Now Playing (SMTC / MPRIS)** and
streaming apps often provide only title/artist (sometimes album and cover art) and
no file path. That is expected — see the limitations in
[Player Support](../player-support).

## The display opens on the wrong screen

Move the window manually to the correct monitor, then use full screen if needed.
Windows can reorder displays after reconnecting screens, docks, or projectors.

> A double-click does not maximize the display window (a framework limitation).
> Use **F11** to toggle full screen.

## The text is hard to read

Check font size, font color, background brightness, artist-overlay opacity, and
title wrapping/spacing. For a quick fix on timed moods, raise the **Readability**
slider — see [Moods and Backgrounds](../moods-and-backgrounds).

## Network display not reachable

Check, in order:

- the network display service is enabled (status bar shows **Network: ON**)
- the other device is on the **same** Wi-Fi/network
- you are opening the exact address Beam shows
- a firewall is not blocking Beam (on Linux you may need to open the port)

### Port already in use

If the port is taken by another program, change the **Port** in
`Settings > Network Display` to a free one and reopen the new address. More in
[Network Display](../network-display).

## Foobar2000 (Beefweb) setup issue

Foobar uses the Beefweb component, and Beam connects to one Beefweb URL. Make sure
the component is installed and the URL/credentials in Beam Preferences point to your
main playback instance. See [FOOBAR_MODULE.md](../FOOBAR_MODULE).

## Windows iTunes

The Windows iTunes integration was improved for stability and logging. If it
misbehaves, switch the log level to `Debug` (below), reproduce once, and check the
log.

## macOS binary install issues

### Troubleshooting installing macOS binary

If you see either of these messages when opening the app:

- “Beam.app is damaged and cannot be opened”
- “Apple could not verify “TangoDisplay””

that is usually because macOS Gatekeeper blocks apps downloaded from the internet
before they are notarized by Apple.

Two options:

1. Follow Apple’s guidance: [Open a Mac app from an unidentified developer](https://support.apple.com/en-gb/guide/mac-help/mh40616/mac)
2. Open a terminal in the folder that contains `Beam.app` and run:

`xattr -dr com.apple.quarantine Beam.app`

Then open the app again.

For other macOS security prompts, check:

1. App Settings
2. Privacy & Security
3. Automation
4. Beam
5. Ensure everything is checked

If you are building Beam on macOS, see [BUILD_MACOS.md](../BUILD_MACOS.md).

## Linux — player not visible in Now Playing (MPRIS)

The app must be open and actually playing to publish an MPRIS session. Some apps
do not publish one at all. Use **Detect** in the Now Playing settings to see what
the system currently reports.

## How to report bugs

Open an issue with a short description and, whenever possible, your `beamlog.txt` output:

<https://github.com/MrNidnan/beam-project/issues>

---

[Home](../) ·
[Download](../download) ·
[Getting Started](../getting-started) ·
[Features](../features) ·
[Player Support](../player-support) ·
[Network Display](../network-display) ·
[Live Display Controls](../live-display-controls) ·
[Moods & Backgrounds](../moods-and-backgrounds) ·
[Troubleshooting](../troubleshooting) ·
[Changelog](../changelog)
