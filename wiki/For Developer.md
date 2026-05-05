# For Developer

Use this page if the packaged app does not work for you, or if you want to run Beam directly from the repository while developing.

## Run Beam From Source

Run all commands from the repository root. The local entry point is `beam.py` and dependencies are listed in `requirements.txt`.

### Windows

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
python .\beam.py
```

### Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
python beam.py
```

### macOS

If Beam packaging is unavailable on macOS, use the same repository-root flow:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
python beam.py
```

If `python3` is missing, install a current Python 3 release from https://www.python.org/downloads/macos/.

## Build And Release

Packaging, PyInstaller commands, smoke scripts, and release steps are documented in [../BUILD.md](../BUILD.md).

## Repository Basics

- main entry point: `beam.py`
- player modules: `bin/modules/`
- app strings and version: `resources/json/strings.json`
- runtime settings template: `resources/json/beamconfig.json`

If you change dependencies, reinstall them with `pip install -r requirements.txt` inside the same virtual environment.
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
