# Notes about the supported Music Player

## MediaMonkey

Do not use a "portable installation".

If MM4 and MM5 are installed, MM5 gets addressed.

Media Monkey 5 does not transmit a %Year, however.

## Foobar2000

Beam needs an installed version of Foobar2000 and the Beefweb component.

Look at:

https://www.foobar2000.org/components/view/foo_beefweb

After installing Beefweb, open Beam `Settings`, choose `Foobar2000` as the media player, and configure these saved settings in the `Foobar2000 Beefweb` section:

- `Beefweb URL` default: `http://localhost:8880/`
- `Beefweb Username` optional
- `Beefweb Password` optional

These values are stored by Beam, so you normally do not need to set environment variables manually.

## Rules

Beam includes a default disabled rule named `Trim () in the Title`.

If you enable that rule in the `Rules` panel, Beam removes trailing parenthetical suffixes from song titles before display. Example:

- `Malena (Take 1)` becomes `Malena`

The rule is optional and disabled by default.

## WinAMP / AIMP

The %Year gets only transmitted if there are ID3v3 and no ID3v1 tags in the file.

## Mixxx

### V0.5

The last played title of the "Auto DJ" playlist in the database gets queried. So Beam will only work if Auto DJ gets used und played titles get appended at the end of the playlist. Thats Options->Preferences->Auto DJ->Re-queue tracks after playback.

### V0.6

The current song will come from the history and the next ones from Auto-DJ, if there.
There is a restriction: each song gets only inserted once in the history (since the last start of Mixxx). So you should better not play songs twice at a milonga.

## Icecast

There is an experimental module for player that can send the "Icecast" protocol (namely NI Traktor).
Metadata from an Icecast2 broadcasting stream get extracted. You have to configure broadcasting to Host http://localhost and Port 8000. Choose any low bitrate Ogg Vorbis codec.

Disadvantages are a potentially higher CPU-Load, only "artist" and "title", and a display delay around 10s.

Currently Icecast does not work for Mixxx, but the existing database related module is preferable, however.

# User Interface

## Main Window

![mainframe-01.jpg](https://bitbucket.org/repo/RarB8L/images/1431575890-mainframe-01.jpg)

The main window includes a preview panel and several panels to configure the display content. The "Apply" button writes the configuration to file and and applies it.

The display window is shown and hidden using the "Display" button.

## Display Window

![displayframe-01.jpg](https://bitbucket.org/repo/RarB8L/images/2196513193-displayframe-01.jpg)

The display window can be moved to a separate screen, monitor or display, and switched between full screen mode and window mode using function key F11.

## DJ Desk

![dj-desk-01.jpg](https://bitbucket.org/repo/RarB8L/images/4207610444-dj-desk-01.jpg)

Typically, the DJ music player and main window run on the laptop screen while the display window is positioned on a separate monitor or beamer displayed for the dancers.
