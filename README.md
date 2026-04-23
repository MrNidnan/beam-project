# Beam-project

Check the local [wiki/Home.md](wiki/Home.md) for project information.

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
