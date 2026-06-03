# For Developer

Use this page if the packaged app does not work for you, or if you want to run Beam directly from the repository.

## Run Beam From Source

Run all commands from the repository root. The local entry point is `beam.py` and dependencies are listed in `requirements.txt`.

## MacOS Step by Step for non tech users

If you do not have a packaged macOS app, you can run Beam from source. Step by step guide.

1. Open Terminal.
2. Press `Cmd + Space`.
3. Type `Terminal`.
4. Press `Enter`.
5. Install Apple command line tools:

```bash
xcode-select --install
```

6. Verify the tools:

```bash
xcode-select -p
git --version
```

If `git` is missing, install it from the official Git website: https://git-scm.com/download/mac

7. Check Python 3:

```bash
python3 --version
```

If Python 3 is missing, install it from https://www.python.org/downloads/macos/

Recommended starting version for older Macs: Python `3.11`

8. Get the Beam source code.

Option A: clone the repository:

```bash
cd ~
git clone <your-repo-url> beam-project
cd beam-project
```

Option B: download and unzip the source release, then open it:

```bash
cd ~/beam-project
```

9. Check that you are in the correct folder:

```bash
ls
```

You should see `beam.py`, `requirements.txt`, `bin`, and `resources`.

10. Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

11. Install dependencies:

```bash
python3 -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

12. Start Beam:

```bash
python beam.py
```

## Run Beam locally from source

For Windows and Linux the commandas are basically the same.
The current fork is meant to be run from the repository root with Python 3 and the dependencies listed in `requirements.txt`.

Clone or download the repository, then open a terminal in the project root and create a virtual environment.

### Windows

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python .\beam.py
```

### Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python beam.py
```

## Build And Release

Packaging, PyInstaller commands, smoke scripts, and release steps are documented in [../BUILD.md](../BUILD.md).

## Repository Basics

- main entry point: `beam.py`
- player modules: `bin/modules/`
- app strings and version: `resources/json/strings.json`
- runtime settings template: `resources/json/beamconfig.json`

If you change dependencies, reinstall them with `pip install -r requirements.txt` inside the same virtual environment.

## "Now Playing" source (SMTC / MPRIS)

`Now Playing` is one user-facing module backed by an OS-level, app-agnostic media
reader — no per-app integration. It reads whatever the desktop reports as the
current media session (Spotify, YouTube Music, browsers, Apple Music, etc).

### Architecture

- `bin/modules/nowplayingsource.py` — platform facade. Picks the backend the same
  way the per-app modules split win/lin: **Windows → SMTC**, **Linux → MPRIS**.
  The UI (`basicsettingspanel.py`) and `nowplayingdata.py` call only the facade.
- `bin/modules/win/smtcmodule.py` — Windows backend, reads the **SMTC**
  (`GlobalSystemMediaTransportControls`) session via WinRT.
- `bin/modules/lin/mprismodule.py` — Linux backend, reads **MPRIS**
  (`org.mpris.MediaPlayer2.*`) over D-Bus.

Both backends expose the identical public API
(`aumid_friendly_name` / `list_sessions` / `run_with_details` / `run`) so the
facade can swap them transparently. The "preferred app" id is an opaque string
stored in the existing `SMTC` settings block (an AUMID on Windows, a D-Bus bus
name on Linux).

### Dependencies / backends

- **Windows (SMTC)** — pywinrt split packages (prebuilt wheels, incl. 3.13):
  `winrt-Windows.Media.Control`, `winrt-Windows.Foundation`,
  `winrt-Windows.Foundation.Collections` (required — `get_sessions()` returns an
  `IVectorView` that lives in this namespace), `winrt-Windows.Storage.Streams`
  (optional — only for the album-art thumbnail). NOT the monolithic `winsdk`
  (no 3.13 wheel, compiles from source); `winsdk` is only a runtime fallback.
- **Linux (MPRIS)** — two bindings, preferred → fallback:
  1. `dbus-next` (async, pure-python) — preferred.
  2. `dbus-python` — fallback. Already a guaranteed Linux dep and what the
     existing per-app lin modules use, so MPRIS works on installs without
     dbus-next, and adding dbus-next never breaks them.

  Selection lives in `mprismodule`: `_HAS_DBUS_NEXT` then `_HAS_DBUS_PYTHON`,
  else `route='unavailable'` (no crash). `run_with_details` reports which backend
  is live (`mpris (dbus-next)` / `mpris (dbus-python)`), visible in the prefs
  Test dialog.

All optional imports are guarded so the module always imports and caches —
`nowplayingdata` re-imports it every poll cycle.

### Cover art — compromises

The whole cover pipeline is **path-based**: `SongObject.FilePath` →
`mutagenutils.readCoverArtData`. Neither media session exposes a file, so we
materialize the art to a temp file and point `FilePath` at it:

- **Format is not assumed.** SMTC thumbnails and MPRIS art are frequently PNG,
  sometimes BMP/GIF, not always JPEG. We sniff the magic bytes
  (`_image_extension`) and write the temp file with the **real** extension — no
  lossy re-encode. Unknown signature → skip (no cover, no crash).
- `mutagenutils.readCoverArtData` was taught to read an image file directly (by
  the mime its extension implies) when `FilePath` is itself an image — that is
  how the SMTC/MPRIS temp file is consumed. `getBitmapTypeFromMime` already maps
  jpeg/png/gif/bmp.
- **SMTC** reads thumbnail bytes via `DataReader` (note: pywinrt `read_bytes()`
  fills a pre-sized `bytearray` in place — it does not take a count and return
  data).
- **MPRIS** `mpris:artUrl` is a URI: `file://` is used directly (no copy);
  `http(s)://` is downloaded to a temp file (4s timeout).
- Temp filename is `beam_{smtc,mpris}_<hash>.<ext>`, hashed on
  `bus/aumid + title + artist` so the path changes per track (forces Beam to
  reload) but is reused within a track.

### Temp cleanup

- **Per-song:** writing a new cover deletes the previous one (`_LAST_COVER_PATH`).
- **Startup sweep:** on import, `_sweep_cover_temp()` removes any leftover
  `beam_*_*` files from a previous crashed run (atexit does not fire on crash).
- **Exit:** `atexit.register(_sweep_cover_temp)` clears everything on clean
  shutdown.
- Assumes a single Beam instance — a concurrent instance's covers would also be
  swept, which is harmless since each rewrites its cover every cycle.

### Diagnostic logging

Both backends use a `_log_once(tag, level, ...)` helper that de-dupes on change,
so the per-cycle poll does not spam the log. Routine state (session list, picked
app, track metadata) logs at **DEBUG**; genuine problems (import failure, read
failure, undecodable cover) log at **INFO**.

## Display controls, mood backgrounds & rules (v0.9.3.0, PR #23)

User-facing notes: [../docs/WHATS_NEW_0.9.3.0.md](../docs/WHATS_NEW_0.9.3.0.md).
Background architecture deep-dive:
[../docs/BACKGROUND_LAYERING_IMPLEMENTATION_PLAN.md](../docs/BACKGROUND_LAYERING_IMPLEMENTATION_PLAN.md).
Where the moving parts live:

### Live display overrides — Blackout & Message

Manual, **non-persisted** overrides that reset to inactive on startup; moods,
rules, player polling and background rotation keep running underneath.

- `bin/mainframe.py` — the Blackout/Resume and Show/Clear Message buttons, their
  state, and the one-line status bar (`Player | Mood | Display | [Message |]
  Network`).
- `bin/dialogs/messagedialog.py` — message text + duration (5–60s, default 15)
  dialog.
- `bin/displaydata.py` / `bin/dialogs/preferencespanels/displaypanel.py` — apply
  blackout (full-black output) and render the centered message overlay; the
  message still draws on top of a blackout.
- Pushed to the browser display via `bin/network/schema.py` +
  `bin/network/service.py`, so preview, projector and browser stay in sync.

### Mood backgrounds — Keep existing + Readability (blur/dim)

The mood **Background** section is now a single **Background type** dropdown
(`Keep existing` / `Color` / `Single image` / `Image slideshow`).

- `bin/dialogs/editmooddialog.py` — the rework (the big diff): the type dropdown,
  showing only relevant controls, and the **Readability** slider (0–100) used
  with `Keep existing`.
- **Readability** = combined blur + dark overlay applied to the *current*
  background so overlaid text stays legible. Resolved into display-layer state in
  `bin/nowplayingdata.py` and rendered in `displaydata` / `displaypanel`.
- Background layer resolution / managed-asset model is documented in the
  Background Layering plan above. Old mood configs load unchanged (migration is
  in `bin/beamsettings.py`).

### Cut / Trim rule on any tag

The old "Trim () in Title" became **Cut / Trim**, applicable to any input ID3
tag with a configurable "Start from" symbol/string.

- `bin/dialogs/editruledialog.py` — rule editor (tag picker + start-from field).
- Trim logic in `bin/songclass.py`; also applied to the previous-song display.
- Legacy "Trim () in Title" rules migrate automatically on load
  (`bin/beamsettings.py`).

### Browser / network display parity

Cover-art Advanced options (corner radius, outline enable/alpha/width up to
32 px) and timed-mood backgrounds now also render on the network/browser display
and update live. See `bin/network/schema.py` (payload) and
`bin/network/service.py` (start/stop made robust across Win/Linux/macOS). The
browser cover art letterboxes (preserves aspect) instead of cropping; the
native soft "feather" edge is approximated by corner rounding in the browser.

(venvs) MacBookPro:master UserName$ python3 -m pip install pypiwin32
(venvs) MacBookPro:master UserName$ python3 -m pip install traktor_nowplaying
(venvs) MacBookPro:master UserName$ python3 -m pip install ola
(venvs) MacBookPro:master UserName$ python3 -m pip install pyinstaller

 

### There are still other modules missing that are no longer part of the Python3 package and must be installed later:

(venvs) MacBookPro:master UserName$ python3 -m pip install legacy-cgi
(venvs) MacBookPro:master UserName$ python3 -m pip install numpy

 

### If you have logged out in the meantime or created a new terminal window, it must be sourced:

$ python3 -m venv /Users/UserName/.local/pipx/venvs
$ source /Users/UserName/.local/pipx/venvs/bin/activate

 

### Another problem: The icons do not have the correct format.

'/Users/UserName/Beam/master/resources/icons/icon_iOSapp/icon_iOSapp_512px.png' which exists but is not in the correct format.
On this platform, only ('icns',) images may be used as icons.
Please install Pillow or convert your 'png' file to one of ('icns',) and try again.

### I did the conversion manually using Preview. That works too.

 

 
pyinstaller --noconfirm --clean --onefile --windowed --osx-bundle-identifier="com.beam-project.beam" \
 --icon="resources/icons/icon_iOSapp/icon_iOSapp_512px.icns" --add-data="resources:resources" \
 --add-data="docs:docs" --name="beam-osx-v0.6.2.1" beam.py

 
198 INFO: PyInstaller: 6.11.1, contrib hooks: 2025.1
199 INFO: Python: 3.13.1
215 INFO: Platform: macOS-15.3-x86_64-i386-64bit-Mach-O
215 INFO: Python environment: /Users/UserName/.local/pipx/venvs/pyinstaller
216 INFO: wrote /Users/UserName/Beam/master/beam-osx-v0.6.2.1.spec
...
13109 INFO: Building BUNDLE BUNDLE-00.toc
13116 INFO: Signing the BUNDLE...
13218 INFO: Building BUNDLE BUNDLE-00.toc completed successfully.

```

# Linux

Distributions where the executable gets tested:

- Ubuntu 20.04 LTS
- Mint 20 Chinnamon

## Install Python3

These are instructions for a global installation.

A virtual environment installation might have advantages if you use Python also for other applications.

```

sudo apt-get -y install python3
sudo apt-get -y install python3-pip
sudo apt-get -y install python3-wxgtk4.0
sudo apt-get -y install python3-mutagen
sudo apt-get -y install python3-setuptools
sudo apt-get -y install python3-dev
sudo apt-get -y install python3-dbus

# Optional: preferred backend for the Now Playing (MPRIS) module. If omitted,
# mprismodule falls back to python3-dbus (installed above).
sudo pip3 install dbus-next

sudo pip3 install traktor_nowplaying
sudo pip3 install ola
sudo pip3 install pyinstaller

```

Now you can run Beam from your source directory:

```

python beam.py

```

or maybe

```

python3 beam.py

```

## Build an executable

```

cd ~/beam-project/beam
pyinstaller --noconfirm --noconsole --clean --onefile --add-data="resources:resources" --add-data="docs:docs" --name="beam-lin" beam.py

```

Run it:

```

$ chmod u+x ./dist/beam-lin
$ ./dist/beam-lin

```

```
