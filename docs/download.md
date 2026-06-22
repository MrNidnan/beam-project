# Download Beam

The easiest way to get Beam is from the GitHub releases page:

**<https://github.com/MrNidnan/beam-project/releases>**

Open the latest release and download the file that matches your system. Look at
the release date to make sure you are getting a recent build.

> **Note about platforms:** Which ready-to-run files exist depends on what each
> release actually provides. If there is no packaged build for your system in the
> latest release, you can always [run Beam from source](#run-from-source-all-platforms).
> Beam does not ship installers for platforms that are not listed in a release.

## Windows

1. Download the Windows build from the latest release.
2. Copy it to a folder you like.
3. Double-click it to start, or run it from a command line to see log output if
   something goes wrong.

## Linux

1. Download the Linux build from the latest release.
2. Copy it to a folder you like.
3. Start it from your file manager, or run it from a shell to see log output.

If you are on Linux and use the network/browser display, you may need to open the
firewall port. See [Network Display](../network-display).

## macOS

A prebuilt macOS app may not always be available. If the latest release does not
include a macOS build, [run Beam from source](#run-from-source-all-platforms)
instead. A packaging guide for collaborators lives in
[BUILD_MACOS.md](../BUILD_MACOS).

## Run from source (all platforms)

If there is no packaged build for your system, you can run Beam directly with
Python 3 and the dependencies in `requirements.txt`.

Clone or download the repository, open a terminal in the project root, and create
a virtual environment.

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

### macOS

Use the same Python steps as Linux. See the collaborator packaging guide in
[BUILD_MACOS.md](../BUILD_MACOS) and the build notes in
[../BUILD.md](https://github.com/MrNidnan/beam-project/blob/master/BUILD.md).

## Having trouble?

See [Troubleshooting](../troubleshooting), or report an issue:
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
