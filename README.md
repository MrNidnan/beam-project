# Beam-project

Check the local [wiki/Home.md](wiki/Home.md) for project information.

This fork is licensed under the GNU General Public License, version 2 or, at your option, any later version (`GPL-2.0-or-later`). See [LICENSE.md](LICENSE.md).

Fork-specific changes and fixes are tracked in [CHANGELOG.md](CHANGELOG.md).

Build and release details for this fork are documented in [BUILD.md](BUILD.md).

## Foobar2000 v2

Foobar2000 support in this fork now uses the Beefweb HTTP API and is no longer compatible with the older deprecated plugin path. See [docs/FOOBAR_MODULE.md](docs/FOOBAR_MODULE.md) for setup and migration details.

Beam now stores Foobar2000 Beefweb connection settings in Preferences when `Foobar2000` is selected, instead of requiring environment variables for normal use.

## VirtualDJ

Beam now also supports VirtualDJ with two integration modes: `History File` by default for non-Pro setups, and optional `Network Control` for Pro users.

For History File mode you have to change virtualDJ settings:

- Enable `Record History`
- Lower `HistoryDelay` to something like `15` seconds (time taken to update the file),
- Set VirtualDJ `tracklistFormat` to:
  ```
  deck=`get_deck` artist=%author genre=%genre title=%titleremix year=`get_year`
  ```
  so Beam can parse labeled fields, import year and genre, and ignore deck '2' history entries.

The Network Control mode includes artist, title, album, genre, year, and file path metadata plus`Master`, `Deck 1`, `Deck 2`, `Left`, and `Right` source selection.
Full setup notes and the maintenance history for that integration are documented in [docs/VIRTUALDJ_MODULE.md](docs/VIRTUALDJ_MODULE.md).

## Rules

Beam also ships with a default disabled rule named `Trim () in the Title` that can be enabled from the Rules panel to remove trailing parenthetical suffixes from displayed song titles.
Example:

- `Malena (Take 1)` becomes `Malena`
- `La Cumparsita (Alt. take) (test press)` becomes `La Cumparsita`

The rule is optional and disabled by default, so Beam preserves the original title unless you enable it.

Beam now keeps the last song and active mood visible while playback is paused. When playback stops, Beam clears the current song and falls back to the default or not-playing mood.

## Profiles

Beam now supports named configuration profiles. The active profile is selected in Preferences and Beam stores the profile manifest plus one full configuration snapshot per profile under `~/.beam`.

Profile storage layout:

```text
~/.beam/
	beamconfig.json
	beamprofiles.json
	profiles/
		default.json
		<profile-id>.json
```

- `beamprofiles.json` stores the active profile ID and profile metadata.
- `profiles/default.json` is the non-deletable built-in `Default` profile.
- each `profiles/<profile-id>.json` file stores the full Beam configuration tree for that profile.
- `beamconfig.json` is still mirrored from the active profile for backward compatibility and manual troubleshooting.

To run the project locally make sure you have Python 3 installed and run:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python .\beam.py
```

## Build an executable

Beam is packaged with PyInstaller. Build on the same operating system you want to run or release.

### Windows

Requirements:

- Windows 10 or newer
- Python 3.12 or newer
- PowerShell

Commands:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
pip install pyinstaller

pyinstaller --noconfirm --noconsole --clean --onefile `
	--add-data "resources;resources" `
	--add-data "docs;docs" `
	--name "beam-win" `
	beam.py
```

Output:

```powershell
.\dist\beam-win.exe
```

### Linux

Requirements on Debian or Ubuntu style systems:

```bash
sudo apt-get update
sudo apt-get install -y \
	python3 \
	python3-venv \
	python3-pip \
	python3-wxgtk4.0 \
	python3-mutagen \
	python3-numpy \
	python3-dbus
```

Commands:

```bash
python3 -m venv --system-site-packages .venv
source .venv/bin/activate

python -m pip install --upgrade pip setuptools wheel
python -m pip install pyinstaller

pyinstaller --noconfirm --noconsole --clean --onefile \
	--add-data "resources:resources" \
	--add-data "docs:docs" \
	--name "beam-lin" \
	beam.py
```

Output:

```bash
./dist/beam-lin
```

### macOS

There are older build notes in [wiki/For Developer.md](wiki/For%20Developer.md), but the maintained build instructions in this fork currently cover Windows and Linux only. If you need a macOS build, start from the source run instructions above and the historical PyInstaller notes in the wiki.

For release workflow details, smoke-test expectations, and signing notes, use [BUILD.md](BUILD.md).

Icecast support is optional. Beam now lazy-loads the Icecast module, so you do not need its dependency just to start the app.

If you want to use the Icecast backend, install `traktor-nowplaying` separately. Note that the current release pulls in code that is not compatible with Python 3.13 because it still imports the removed `cgi` module, so Icecast currently needs either a patched dependency or an older Python version such as 3.12.
