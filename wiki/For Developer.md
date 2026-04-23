# Common #

## Using the Python source ##

Running Beam from source requires the installation of Python3 plus some packages.

Download the beam sources :

```
https://bitbucket.org/beam-project/main/downloads/
beam-src-v0.5.zip
```

and unzip the folder "beam" in it to somewhere.
Move into that folder and start beam with a command like:

```
python beam.py
```

## Using the PyCharm IDE ##

File->New project->Create from existing sources
```
~\beam-project\beam
```
VCS->Enable version control system->Git
Pull

Using PyCharm has the advantage, that tracebacks can get doubleclicked to jump to the error position in the code.
And version control support is included to push/pull the commits.

Run beam (Shift-F10)

Debug beam (Shift-F9)

Step Over (F8)

Step Into (F7)



## Set a new Beam version number ##

In the file

resources/json/strings.json

there is a property like


```
  "version": "0.5.0.0",
```


that has to get adjusted to get displayed in the main window title.

PyCharm -> Git -> Commit -> Comment: "V0.5.0.0" -> Commit and Push

## Merge a Branch ##

Bitbucket -> Branches -> Merge


## Add a new Media Player ##

1) Create module source file for the operatig system

bin/modules/lin/strawberrymodule.py

```python
def run(MaxTandaLength):
[...]
    return playlist, playbackStatus
```

2) Import the module in nowplayingdata.py

```python

if platform.system() == 'Linux':
    from bin.modules.lin import audaciousmodule, rhythmboxmodule, clementinemodule, bansheemodule, spotifymodule, mixxxmodule, strawberrymodule

```

3)Include the function in NowPlayingData.readData(self, currentSettings):

```python
        if platform.system() == 'Linux':
            [...]
            if currentSettings._moduleSelected == 'Strawberry':
                self.currentPlaylist, self.PlaybackStatus = strawberrymodule.run(currentSettings._maxTandaLength)
```
       
4) Add new module to resources/json/beamsettings.json

```python

   {
      "Modules": [
        "Audacious",
        "Banshee",
        "Clementine",
        "Rhythmbox",
        "Spotify",
        "Mixxx",
        "Icecast",
        "Strawberry"
      ],
      "System": "Linux"
    },
	
```



# Windows #

## Install Python3 ##

Download & Install Python 3.9.9 from:

https://www.python.org/downloads/

Execute

```
python-3.9.9-amd64.exe
```

Python path configuration:

User Environment Path: +  C:\Users\<username>\AppData\Local\Programs\Python\Python39

```
python -m ensurepip
```

User Environment Path: + C:\Users\<username>\AppData\Local\Programs\Python\Python39\Scripts

```
pip3 install wxpython
pip3 install mutagen
pip3 install pypiwin32
pip3 install traktor_nowplaying
pip3 install pyinstaller
```

## Start Beam ##


```
python beam.py
```

or maybe

```
python3 beam.py
```

## Build an executable ##

```
pyinstaller --noconfirm --noconsole --clean --onefile --add-data="resources;resources" --add-data="docs;docs" --name="beam-win.exe" beam.py 
```

Run it:

```
.\dist\beam-win.exe
```

## Start Beam sources from the command line ##

```
cd C:\Users\<username>\beam-projec\beam
python beam.py
```


## Start Beam sources by a desktop shortcut ##

Desktop->New->Shortcut
Location of the item:
```
C:\Users\<username>\AppData\Local\Programs\Python\Python39\python.exe C:\Users\<username>\beam-projec\beam\beam.py
```
Name: 
```
Beam
```
Shortcut Context Menu->Properties->Start in: 
```
C:\Users\<username>\beam-project\beam
```


# Apple macOS #

Announced Jan 2022: Apple will not be including Python2 with its macOS 12.3 "Monterey" So you will have to install Python3 separately, Python2 does not get supported since 2020.

## Install Python3 ##

If you have successfully done it and you would write it down, please let us know.
Some possible hints:

https://www.geeksforgeeks.org/how-to-install-wxpython-on-macos/

```
pip3 install wxpython
pip3 install mutagen
pip3 install pypiwin32
pip3 install traktor_nowplaying
pip3 install ola
pip3 install pyinstaller
```

## Start Beam ##

If you have successfully done it and you would write it down, please let us know.

## Build an executable ##


```
cd ~/beam-project/beam
pyinstaller --noconfirm --clean --onefile --windowed --osx-bundle-identifier="com.beam-project.beam" --icon="resources/icons/icon_iOSapp/icon_iOSapp_512px.png" --add-data="resources:resources" --add-data="docs:docs" --name="beam-osx-v0.6.2.1" beam.py
```

## Technical steps supplied by Klaus ##

```
### I didn't have Xcode on my system and installed it at some point via the AppStore.
 
MacBookPro:DEV UserName$ /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  ==> This script will install:
  /usr/local/bin/brew
  /usr/local/share/doc/homebrew
  /usr/local/share/man/man1/brew.1
  /usr/local/share/zsh/site-functions/_brew
  /usr/local/etc/bash_completion.d/brew
  /usr/local/Homebrew
  ...
  ==> Updating Homebrew...
  ==> Installation successful!
  ==> Next steps:
  - Run these commands in your terminal to add Homebrew to your PATH:
    echo >> /Users/UserName/.bash_profile
    echo 'eval "$(/usr/local/bin/brew shellenv)"' >> /Users/UserName/.bash_profile
    eval "$(/usr/local/bin/brew shellenv)"
 
MacBookPro:DEV UserName$ echo >> /Users/UserName/.bash_profile
MacBookPro:DEV UserName$ echo 'eval "$(/usr/local/bin/brew shellenv)"' >> /Users/UserName/.bash_profile
MacBookPro:DEV UserName$ eval "$(/usr/local/bin/brew shellenv)"
 
MacBookPro:DEV UserName$ brew install python
  ==> Downloading https://ghcr.io/v2/homebrew/core/python/3.13/manifests/3.13.1
  ...
  ==> Installing python@3.13
  ...
  Python is installed as
    /usr/local/bin/python3
 
 
MacBookPro:DEV UserName$ brew install pipx
 
MacBookPro:DEV UserName$ pipx install wxPython
  installed package wxpython 4.2.2, installed using Python 3.13.1
 
MacBookPro:DEV UserName$ pipx ensurepath
  Success! Added /Users/UserName/.local/bin to the PATH environment variable.
 
MacBookPro:DEV UserName$ python3 -m venv /Users/UserName/.local/pipx/venvs
MacBookPro:DEV UserName$ source /Users/UserName/.local/pipx/venvs/bin/activate
 
(venvs) MacBookPro:master UserName$ python3 -m pip install setuptools
(venvs) MacBookPro:master UserName$ pip install --upgrade pip
 
(venvs) MacBookPro:wxPython-4.1.1 UserName$ python3 -m pip install setuptools
  Installing collected packages: setuptools
  Successfully installed setuptools-75.8.0
 
(venvs) MacBookPro:bin UserName$ brew install wxmac
  ==> Auto-updating Homebrew...
  ==> Auto-updated Homebrew!
 
### THE PYTHON MODULES CAN NOW BE INSTALLED
 
(venvs) MacBookPro:wxPython-4.1.1 UserName$ python3 -m pip install setuptools
(venvs) MacBookPro:wxPython-4.1.1 UserName$ python3 setup.py install
 
(venvs) MacBookPro:master UserName$ python3 -m pip install mutagen
(venvs) MacBookPro:master UserName$ python3 -m pip install wxpython
(venvs) MacBookPro:master UserName$ python3 -m pip install pypiwin32
(venvs) MacBookPro:master UserName$ python3 -m pip install traktor_nowplaying
(venvs) MacBookPro:master UserName$ python3 -m pip install ola
(venvs) MacBookPro:master UserName$ python3 -m pip install pyinstaller
 
### There are still other modules missing that are no longer part of the Python3 package and must be installed later:
(venvs) MacBookPro:master UserName$ python3 -m pip install legacy-cgi
(venvs) MacBookPro:master UserName$ python3 -m pip install numpy
 
### If you have logged out in the meantime or created a new terminal window, it must be sourced:
$ python3 -m venv /Users/UserName/.local/pipx/venvs
$ source /Users/UserName/.local/pipx/venvs/bin/activate
 
### Another problem: The icons do not have the correct format.
'/Users/UserName/Beam/master/resources/icons/icon_iOSapp/icon_iOSapp_512px.png' which exists but is not in the correct format. 
  On this platform, only ('icns',) images may be used as icons. 
  Please install Pillow or convert your 'png' file to one of ('icns',) and try again.
### I did the conversion manually using Preview. That works too.
 
 
pyinstaller --noconfirm --clean --onefile --windowed --osx-bundle-identifier="com.beam-project.beam" \ 
  --icon="resources/icons/icon_iOSapp/icon_iOSapp_512px.icns" --add-data="resources:resources" \
  --add-data="docs:docs" --name="beam-osx-v0.6.2.1" beam.py
 
  198 INFO: PyInstaller: 6.11.1, contrib hooks: 2025.1
  199 INFO: Python: 3.13.1
  215 INFO: Platform: macOS-15.3-x86_64-i386-64bit-Mach-O
  215 INFO: Python environment: /Users/UserName/.local/pipx/venvs/pyinstaller
  216 INFO: wrote /Users/UserName/Beam/master/beam-osx-v0.6.2.1.spec
  ...
  13109 INFO: Building BUNDLE BUNDLE-00.toc
  13116 INFO: Signing the BUNDLE...
  13218 INFO: Building BUNDLE BUNDLE-00.toc completed successfully.

```


# Linux #

Distributions where the executable gets tested:

* Ubuntu 20.04 LTS
* Mint 20 Chinnamon

## Install Python3 ##

These are instructions for a global installation.

A virtual environment installation might have advantages if you use Python also for other applications.

```
sudo apt-get -y install python3
sudo apt-get -y install python3-pip
sudo apt-get -y install python3-wxgtk4.0
sudo apt-get -y install python3-mutagen
sudo apt-get -y install python3-setuptools
sudo apt-get -y install python3-dev
sudo apt-get -y install python3-dbus

sudo pip3 install traktor_nowplaying
sudo pip3 install ola
sudo pip3 install pyinstaller
```


Now you can run Beam from your source directory:

```
python beam.py
```

or maybe

```
python3 beam.py
```

## Build an executable ##

```
cd ~/beam-project/beam
pyinstaller --noconfirm --noconsole --clean --onefile --add-data="resources:resources" --add-data="docs:docs" --name="beam-lin" beam.py
```

Run it:

```
$ chmod u+x ./dist/beam-lin
$ ./dist/beam-lin
```