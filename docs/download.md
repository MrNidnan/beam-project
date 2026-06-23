# Download Beam

## All Releases

- [Browse all GitHub releases](https://github.com/MrNidnan/beam-project/releases)

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
