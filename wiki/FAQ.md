# Common

## Where shall I address questions, suggestions, feedback?

Please use our facebook app page for a post or a message:

https://www.facebook.com/beamtheproject/

## Why is there no layout panel?

That's the default mood, so it's now in the mood panel.

## Where do I find a logfile

A logfile 'beamlog.txt' will be written in the subdirectory '$USERHOME/.beam'.

On Windows this might e.g. be 'C:\Users\<USERNAME>\\.beam\beamlog.txt' .

## Why is there no config file '$USERHOME/.beam/beamconfig.json'

If it's not there, then it gets created by the "Apply" button.

## Where are profile configurations stored?

Beam stores profile data in `$USERHOME/.beam`.

- `beamprofiles.json` keeps the active profile and the list of available profiles.
- `profiles/default.json` stores the built-in `Default` profile.
- `profiles/<profile-id>.json` stores the full configuration for each additional profile.
- `beamconfig.json` is still written as a compatibility copy of the active profile.

## How can I change the log level?

That's not implemented in the config panel yet. In the config file '$USERHOME/.beam/beamconfig.json' there is a property

"LogLevel": "Info",

This can get changed to:

- "Debug":
- "Info"
- "Warning"
- "Error"
- "Critical"

## Beam: Directory <dirname> does not exist, logging to stdout only

The directory get's created by the "Apply" button.

## WARNING : BeamSettings.loadConfig(): configfile in old directory, ignored: '<filename>'

Beam versions since 0.4.4.5 store their configuration and log file not in the user home but in a subdirectory ".beam" there. If you do not need the "BeamConfing.json"
for legacy versions of Beam, you can rename or delete that file in your user home directory.

## Why does a double click not maximize the display screen?

There is a technical issue with the framework. Use <F11> to toggle the maximized mode.

# Windows

## Error installing wxpython

"distutils.errors.DistutilsPlatformError: Microsoft Visual C++ 14.2 or greater is required. Get it with "Microsoft C++ Build Tools": https://visualstudio.microsoft.com/visual-cpp-build-tools/"

- Goto https://visualstudio.microsoft.com/de/downloads/
- Into section "Buildtools für Visual Studio 2022"
- Download vs_BuildTools.exe
- Install "Visual Studio Build Tools 2022"
