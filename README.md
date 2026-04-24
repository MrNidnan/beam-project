# Beam-project

Check the local [wiki/Home.md](wiki/Home.md) for project information.

This fork is licensed under the GNU General Public License, version 2 or, at your option, any later version (`GPL-2.0-or-later`). See [LICENSE.md](LICENSE.md).

Fork-specific changes and fixes are tracked in [CHANGELOG.md](CHANGELOG.md).

Build and release commands for this fork are documented in [BUILD.md](BUILD.md).

Foobar2000 support in this fork now uses the Beefweb HTTP API and is no longer compatible with the older deprecated plugin path. See [FOOBAR_MODULE.md](FOOBAR_MODULE.md) for setup and migration details.

Beam now stores Foobar2000 Beefweb connection settings in Preferences when `Foobar2000` is selected, instead of requiring environment variables for normal use.

Beam also ships with a default disabled rule named `Trim () in the Title` that can be enabled from the Rules panel to remove trailing parenthetical suffixes from displayed song titles.

Beam now keeps the last song and active mood visible while playback is paused. When playback stops, Beam clears the current song and falls back to the default or not-playing mood.

To run the project locally make sure you have Python 3 installed and run:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python .\beam.py
```

Icecast support is optional. Beam now lazy-loads the Icecast module, so you do not need its dependency just to start the app.

If you want to use the Icecast backend, install `traktor-nowplaying` separately. Note that the current release pulls in code that is not compatible with Python 3.13 because it still imports the removed `cgi` module, so Icecast currently needs either a patched dependency or an older Python version such as 3.12.
