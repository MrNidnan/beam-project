# Build

This document describes how to build Beam `v0.7.0` release artifacts for Windows and Linux.

Beam is packaged as a single-file executable with PyInstaller. Build on the target OS you want to release for.

## Version

Beam currently reports its version from `resources/json/strings.json`:

```json
"version": "0.7.0.0"
```

Release artifact names below use `v0.7.0`.

## Common Notes

- Run all commands from the repository root.
- Build Windows artifacts on Windows and Linux artifacts on Linux.
- The packaged app still reads user config from:
  - Windows: `%USERPROFILE%\\.beam\\beamconfig.json`
  - Linux: `~/.beam/beamconfig.json`

## Windows

### Prerequisites

- Windows 10 or newer
- Python 3.12 or newer
- PowerShell

### Build Commands

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
pip install pyinstaller

pyinstaller --noconfirm --noconsole --clean --onefile `
  --add-data "resources;resources" `
  --add-data "docs;docs" `
  --name "beam-win-v0.7.0" `
  beam.py
```

### Output

```powershell
.\dist\beam-win-v0.7.0.exe
```

### Smoke Test

```powershell
.\dist\beam-win-v0.7.0.exe
```

## Linux

These commands target Debian or Ubuntu style systems.

### System Packages

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

### Build Commands

Use `--system-site-packages` so the distro-provided `wxPython` and `dbus-python` packages are available inside the build environment.

```bash
python3 -m venv --system-site-packages .venv
source .venv/bin/activate

python -m pip install --upgrade pip setuptools wheel
python -m pip install pyinstaller

pyinstaller --noconfirm --noconsole --clean --onefile \
  --add-data "resources:resources" \
  --add-data "docs:docs" \
  --name "beam-lin-v0.7.0" \
  beam.py
```

### Output

```bash
./dist/beam-lin-v0.7.0
```

### Smoke Test

```bash
chmod u+x ./dist/beam-lin-v0.7.0
./dist/beam-lin-v0.7.0
```

## Release Checklist

1. Update `resources/json/strings.json` if the version changes.
2. Update `CHANGELOG.md`.
3. Build the Windows artifact.
4. Build the Linux artifact.
5. Smoke test both artifacts.
6. Tag the release.

```bash
git tag v0.7.0
git push origin v0.7.0
```

7. Create the GitHub release and upload:
   - `beam-win-v0.7.0.exe`
   - `beam-lin-v0.7.0`

## Packaging Notes

- Icecast is optional at runtime.
- The optional Icecast backend still depends on `traktor-nowplaying`, which may require either a patched dependency or an older Python version.
- On Linux, distro packages are preferred for `wxPython` and `dbus-python`.
