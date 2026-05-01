# Known Bugs

At the moment, this fork does not track any confirmed current known bugs on this page.

The older entries that used to be listed here were already fixed in newer releases and are kept below only as historical notes.

If you run into a problem, start here instead:

- [Quick Start Guide.md](Quick%20Start%20Guide.md)
- [User Manual - Troubleshooting.md](User%20Manual%20-%20Troubleshooting.md)
- [FAQ.md](FAQ.md)
- [../CHANGELOG.md](../CHANGELOG.md)

## Historical Fixed Issues

### Windows startup failure on some systems

Older Beam versions could fail on Windows with locale or encoding-related startup errors.

Current status:

- fixed in this fork
- Windows executable startup failures on non-UTF-8 system locales were fixed in `v0.7.1.2`
- Windows startup reliability was improved again in later releases

See [../CHANGELOG.md](../CHANGELOG.md) for the release history.

### Executable background paths pointing into temporary `_MEI...` folders

Older Beam versions could save background paths that pointed into PyInstaller temporary extraction folders, which then broke after the next restart.

Current status:

- fixed in older Beam releases and superseded by the newer background asset handling in this fork
- the current fork supports bundled backgrounds, managed imported backgrounds under the user's `.beam` folder, and compatibility with older saved paths

See also:

- [User Manual - Customize the Display.md](User%20Manual%20-%20Customize%20the%20Display.md)
- [README.md](../README.md)
- [../CHANGELOG.md](../CHANGELOG.md)

## Reporting New Issues

If you find a real current bug, it is more useful to record:

- the Beam version
- your operating system
- the selected music player
- the steps needed to reproduce the problem
- the contents of `beamlog.txt` from your user `.beam` folder
