# Build Beam on macOS

This document explains how a collaborator can build Beam on a modern Mac, package the result, and send the finished artifact back.

The standard macOS output is a `.app` bundle zipped with `ditto`. That is the format to hand back for testing or release review.

## Target

- Preferred target: one `universal2` macOS app that runs on both Apple Silicon and Intel Macs.
- Fallback target: if a universal build is not possible in the collaborator's environment, build and send separate `arm64` and `x86_64` archives.

## Build Standard

Use this standard unless there is a specific reason not to:

- Build on macOS, not on Linux or Windows.
- Use Python `3.12`, because the repository CI and release workflow are already aligned to Python 3.12.
- Prefer the official `python.org` universal2 installer instead of a single-architecture Homebrew Python.
- Build a windowed macOS app bundle with PyInstaller.
- Zip the `.app` bundle with `ditto` so Finder metadata and symlinks are preserved.
- Name the archive with the Beam release version and the target architecture.

## What The Collaborator Needs

- A modern Mac running a supported macOS release.
- Terminal access.
- Xcode Command Line Tools.
- Python `3.12` from `python.org`.
- Network access to install Python packages from PyPI.

## Step 1: Install Xcode Command Line Tools

Open Terminal and run:

```bash
xcode-select --install
```

If the tools are already installed, macOS will say so.

## Step 2: Install Python 3.12 From python.org

Install a `3.12.x` macOS `universal2` installer from Python.org.

After installation, verify it:

```bash
python3.12 --version
file /Library/Frameworks/Python.framework/Versions/3.12/bin/python3.12
```

Expected result:

- `python3.12 --version` shows `Python 3.12.x`
- `file .../python3.12` should report a universal or multi-architecture Mach-O binary

Do not use a single-architecture Python if the goal is one archive for both Apple Silicon and Intel.

## Step 3: Get The Source Code

Either clone the repository:

```bash
git clone https://github.com/MrNidnan/beam-project.git
cd beam-project
```

Or download the source archive from GitHub, extract it, and `cd` into the extracted folder.

## Step 4: Confirm The Beam Version

Beam version comes from `resources/json/strings.json`.

Check it:

```bash
python3.12 - <<'PY'
import json
from pathlib import Path
version = json.loads(Path('resources/json/strings.json').read_text(encoding='utf-8'))['version']
print(version)
print('v' + version.removesuffix('.0'))
PY
```

Example output:

```text
0.9.1.0
v0.9.1.0
```

Use that value in the archive name you send back.

## Step 5: Create A Clean Virtual Environment

From the repository root:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
```

## Step 6: Install Build Dependencies

Install the project requirements and PyInstaller:

```bash
python -m pip install -r requirements.txt
python -m pip install pyinstaller
```

If `wxPython` fails to install, stop there and report the exact pip error. Beam cannot be packaged correctly without it.

## Step 7: Verify The Python Architecture

Before building, verify that the active Python supports the target you want:

```bash
python - <<'PY'
import platform
print(platform.platform())
print(platform.machine())
PY

file "$(python -c 'import sys; print(sys.executable)')"
```

For a single universal build, the Python installation itself needs universal2 support.

## Step 8: Build The macOS App Bundle

This is the standard Beam macOS build command:

```bash
VERSION_TAG="$(python - <<'PY'
import json
from pathlib import Path
version = json.loads(Path('resources/json/strings.json').read_text(encoding='utf-8'))['version']
print('v' + version.removesuffix('.0'))
PY
)"

python -m PyInstaller \
  --noconfirm \
  --clean \
  --windowed \
  --target-arch universal2 \
  --name "Beam" \
  --icon "resources/icons/installer_icon/icon_MacOS.icns" \
  --osx-bundle-identifier "com.beamproject.beam" \
  --add-data "resources:resources" \
  --add-data "docs:docs" \
  beam.py
```

Expected output:

```text
dist/Beam.app
```

## Step 9: Verify The Built App

Run these checks before zipping:

```bash
open dist/Beam.app
```

Confirm:

- Beam opens without an immediate crash.
- The main window appears.
- Closing the app works normally.

Then verify the app binary architecture:

```bash
file "dist/Beam.app/Contents/MacOS/Beam"
lipo -info "dist/Beam.app/Contents/MacOS/Beam"
```

For a universal build, `lipo -info` should report both `arm64` and `x86_64`.

## Step 10: Zip The App Bundle

Use `ditto`, not Finder compression and not plain `zip -r`.

```bash
mkdir -p release-artifacts

ARCHIVE_NAME="beam-mac-${VERSION_TAG}-universal2.zip"

ditto -c -k --sequesterRsrc --keepParent \
  "dist/Beam.app" \
  "release-artifacts/${ARCHIVE_NAME}"
```

Expected output:

```text
release-artifacts/beam-mac-v0.9.1.0-universal2.zip
```

## Step 11: Sanity-Test The Zip

Before sending the file back:

```bash
rm -rf /tmp/Beam-smoke
mkdir -p /tmp/Beam-smoke
ditto -x -k "release-artifacts/${ARCHIVE_NAME}" /tmp/Beam-smoke
open /tmp/Beam-smoke/Beam.app
```

This confirms the archive expands correctly and still launches.

## Step 12: Send Back These Files

The collaborator should send back:

- The zip archive from `release-artifacts/`
- The exact commit SHA they built
- The macOS version they used
- Whether the build is `universal2`, `arm64`, or `x86_64`

Recommended handoff note:

```text
Built Beam from commit <sha> on macOS <version> using Python 3.12.x from python.org.
Artifact: beam-mac-v<version>-universal2.zip
PyInstaller target: universal2
Smoke check: app opened and main window appeared
```

## Fallback: Build Separate Apple Silicon And Intel Archives

If `--target-arch universal2` fails because the local Python or one of the binary wheels is not universal-compatible, build separate archives instead.

### Apple Silicon build

On an Apple Silicon Mac using native Terminal:

```bash
python -m PyInstaller \
  --noconfirm \
  --clean \
  --windowed \
  --target-arch arm64 \
  --name "Beam" \
  --icon "resources/icons/installer_icon/icon_MacOS.icns" \
  --osx-bundle-identifier "com.beamproject.beam" \
  --add-data "resources:resources" \
  --add-data "docs:docs" \
  beam.py
```

Zip it as:

```bash
ditto -c -k --sequesterRsrc --keepParent \
  "dist/Beam.app" \
  "release-artifacts/beam-mac-${VERSION_TAG}-arm64.zip"
```

### Intel build

Preferred option:

- Build on a real Intel Mac with the same steps as above, using `--target-arch x86_64`.

Fallback option on Apple Silicon:

- Use a Python installation and dependency stack that can run under Rosetta 2.
- Open a Rosetta Terminal session.
- Recreate the virtual environment under Rosetta.
- Build with `--target-arch x86_64`.

Command:

```bash
python -m PyInstaller \
  --noconfirm \
  --clean \
  --windowed \
  --target-arch x86_64 \
  --name "Beam" \
  --icon "resources/icons/installer_icon/icon_MacOS.icns" \
  --osx-bundle-identifier "com.beamproject.beam" \
  --add-data "resources:resources" \
  --add-data "docs:docs" \
  beam.py
```

Zip it as:

```bash
ditto -c -k --sequesterRsrc --keepParent \
  "dist/Beam.app" \
  "release-artifacts/beam-mac-${VERSION_TAG}-x86_64.zip"
```

## Troubleshooting

### `wxPython` does not install

- Confirm you are using Python `3.12`.
- Confirm you are using the official `python.org` installer, not an arbitrary Python build.
- Upgrade `pip`, `setuptools`, and `wheel` first.
- If it still fails, send the pip error log back with the build attempt.

### PyInstaller build succeeds but the app crashes on launch

- Run the binary from Terminal to capture output:

```bash
dist/Beam.app/Contents/MacOS/Beam
```

- Include the crash output and `beamlog.txt` when reporting back.

### Universal build does not contain both architectures

- Check the active Python binary with `file`.
- Rebuild with a universal2 Python installation.
- Recreate `.venv` after changing Python installations.

## Notes

- This process creates an unsigned app bundle. Gatekeeper warnings are expected on machines other than the builder's machine.
- This process does not notarize the app.
- For collaborator handoff, a zipped unsigned `.app` is acceptable unless release signing is added later.
