# Quick Start Guide

## Goal

You are ready when:

- Beam shows the current song in the preview
- the display window is open
- the display is on your projector, TV, or second screen

## Running App from Code (macOs, Win, Linux)

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

### Notes

## 5-Minute Setup

1. Start Beam.
2. In Beam, choose your music player.
3. Click `Apply`.
4. Start playing a song in your player.
5. Check that Beam shows the song in the preview.
6. Click `Display` to open the audience screen.
7. Move that window to the projector or second monitor.

![Screenshot: Beam main window with player selection, preview, Apply, and Display highlighted](../docs/images/user-manual/beam_6_preview_display.jpg)

## Before a Real Event

Test these four things before people arrive:

- the correct music player is selected
- a song appears in the preview
- the display is on the correct screen
- the text is readable from a distance

## If Something Does Not Work

Start here:

- [User Manual - Troubleshooting.md](User%20Manual%20-%20Troubleshooting.md)
- [User Manual - Player Setup.md](User%20Manual%20-%20Player%20Setup.md)

## Want the Full Guide?

Go to [User Manual - Start Here.md](User%20Manual%20-%20Start%20Here.md).
