# Windows 11 Beam startup fails#

2022-12-10 20:43:22 : ERROR : C++ assertion "strcmp(setlocale(0, 0), "C") == 0" failed at ..\..\src\common\intl.cpp(1694) in wxLocale::GetInfo(): You probably called setlocale() directly instead of using wxLocale and now there is a mismatch between C/C++ and Windows locale.
Things are going to break, please only change locale by creating wxLocale objects to avoid this!
Traceback (most recent call last):
  File "beam.py", line 86, in <module>
  File "bin\mainframe.py", line 64, in __init__
wx._core.wxAssertionError: C++ assertion "strcmp(setlocale(0, 0), "C") == 0" failed at ..\..\src\common\intl.cpp(1694) in wxLocale::GetInfo(): You probably called setlocale() directly instead of using wxLocale and now there is a mismatch between C/C++ and Windows locale.
Things are going to break, please only change locale by creating wxLocale objects to avoid this!


# Error dialog: Failed to load image from file ... #

It happens if you use an executable and select a new background image (and then apply).
In that case we have something in the config "~.beam\beamconfig.json" like

```
"Background":  "C:\\Users\\Martin\\AppData\\Local\\Temp\\_MEI61802\\resources\\backgrounds
\\bg1920x1080px_darkBlue.jpg",
```

That temporary extraction folder ("_MEI61802") changes at the next start. 
It should be a relative path then like:

```
"Background":  "resources\\backgrounds\\bg1920x1080px_darkBlue.jpg",
```

or so.

## Workaround

Do not change a background image file when using an executable version. 

a) Delete "~.beam\beamconfig.json" so that a new config file gets created.

b) To not lose the configuration, open the config file and correct it manually.

## Fixed in V0.5.0.4