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

## CI Policy

- Branch pushes and pull requests run the GitHub Actions validation workflow only.
- The validation workflow checks the Python entrypoint on Windows and Linux, but it does not package Beam and it does not upload artifacts.
- Release artifacts are built only by the GitHub Actions release workflow.
- The Windows release workflow can optionally Authenticode-sign the executable when `WINDOWS_CERTIFICATE_PFX_BASE64` and `WINDOWS_CERTIFICATE_PASSWORD` GitHub Actions secrets are configured.
- The release workflow runs when you push a `v*` tag, or when you start it manually with `workflow_dispatch` and provide a release tag.
- The release workflow builds the Windows and Linux executables, uploads those workflow artifacts, pauses at the `release-smoke-test` environment gate, and then creates a draft GitHub release.

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

### Code Signing

Unsigned Windows executables will show `Unknown publisher`, and SmartScreen may warn that the app is unrecognized. To improve this:

- Export your code-signing certificate as a `.pfx` file.
- Base64-encode that file and store it as the `WINDOWS_CERTIFICATE_PFX_BASE64` GitHub Actions secret.
- Store the PFX password as the `WINDOWS_CERTIFICATE_PASSWORD` secret.
- The release workflow will sign the executable automatically when both secrets are present.

Example PowerShell command to prepare the Base64 value locally:

```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("C:\path\to\beam-signing-cert.pfx"))
```

Notes:

- Standard code signing removes the `Unknown publisher` label but does not guarantee SmartScreen will stop warning immediately.
- SmartScreen reputation is built over time, and a newly issued certificate may still trigger warnings.
- An EV code-signing certificate usually establishes SmartScreen reputation faster than a standard OV certificate.

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

7. Wait for the GitHub Actions `Release` workflow to build:

- `beam-win-v0.7.0.exe`
- `beam-lin-v0.7.0`

8. Approve the `release-smoke-test` environment if your repository requires manual approval.

9. Review the draft GitHub release created by the workflow and publish it.

## Packaging Notes

- Icecast is optional at runtime.
- The optional Icecast backend still depends on `traktor-nowplaying`, which may require either a patched dependency or an older Python version.
- On Linux, distro packages are preferred for `wxPython` and `dbus-python`.
