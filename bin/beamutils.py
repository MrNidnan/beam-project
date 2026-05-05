#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    Copyright (C) 2014 Mikael Holber http://mywebsite.com
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#    or download it from http://www.gnu.org/licenses/gpl.txt
#
#
#    Revision History:
#
#    XX/XX/2014 Version 1.0
#       - Initial release
#
# This Python file uses the following encoding: utf-8
import os
import sys
import logging


def getProcessMemoryUsageBytes():
    try:
        import resource

        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        if sys.platform == 'darwin':
            return int(rss)
        return int(rss) * 1024
    except ImportError:
        if sys.platform == 'win32':
            import ctypes

            class ProcessMemoryCounters(ctypes.Structure):
                _fields_ = [
                    ('cb', ctypes.c_ulong),
                    ('PageFaultCount', ctypes.c_ulong),
                    ('PeakWorkingSetSize', ctypes.c_size_t),
                    ('WorkingSetSize', ctypes.c_size_t),
                    ('QuotaPeakPagedPoolUsage', ctypes.c_size_t),
                    ('QuotaPagedPoolUsage', ctypes.c_size_t),
                    ('QuotaPeakNonPagedPoolUsage', ctypes.c_size_t),
                    ('QuotaNonPagedPoolUsage', ctypes.c_size_t),
                    ('PagefileUsage', ctypes.c_size_t),
                    ('PeakPagefileUsage', ctypes.c_size_t),
                ]

            counters = ProcessMemoryCounters()
            counters.cb = ctypes.sizeof(ProcessMemoryCounters)
            if ctypes.windll.psapi.GetProcessMemoryInfo(
                ctypes.windll.kernel32.GetCurrentProcess(),
                ctypes.byref(counters),
                counters.cb,
            ):
                return int(counters.WorkingSetSize)
        return 0


def formatMemoryUsageMb(byteCount):
    if not byteCount:
        return 'n/a'
    return '%.2f MB' % (float(byteCount) / float(1024 * 1024))



#
# Linux ~, $HOME
# Windows %HOMEPATH%
#
def getUserHomePath():
    userhomepath = os.path.expanduser("~")

    return userhomepath


#
# directory where beam got started from
#
def getBeamHomePath():
    if getattr(sys, 'frozen', False):
        # PyInstaller one-file
        # application_path = os.path.dirname(sys.executable)
        apphomepath = sys._MEIPASS
        # print("Path PyInstaller: " + application_path)
    else:
        apphomepath = os.getcwd()
        # print("Path Python: " + appPath)

    # print(os.listdir(appPath))
    return apphomepath


def _is_valid_resources_root(resources_path):
    if not os.path.isdir(resources_path):
        return False

    strings_path = os.path.join(resources_path, 'json', 'strings.json')
    return os.path.isfile(strings_path)


def _get_frozen_resources_candidates():
    candidates = []
    meipass_path = getattr(sys, '_MEIPASS', '')
    if meipass_path:
        candidates.append(os.path.join(meipass_path, 'resources'))
        candidates.append(meipass_path)

    executable_dir = os.path.dirname(sys.executable)
    candidates.append(os.path.join(executable_dir, 'resources'))
    candidates.append(os.path.normpath(os.path.join(executable_dir, '..', 'Resources', 'resources')))
    candidates.append(os.path.normpath(os.path.join(executable_dir, '..', 'Resources')))

    unique_candidates = []
    seen_candidates = set()
    for candidate in candidates:
        normalized_candidate = os.path.normcase(os.path.normpath(candidate))
        if normalized_candidate in seen_candidates:
            continue
        seen_candidates.add(normalized_candidate)
        unique_candidates.append(candidate)

    return unique_candidates



def getRelativePath(filepath):
    ## userhomepath = getUserHomePath()
    ## beamconfigpath = os.path.join(os.path.expanduser("~"), ".beam")

    beamhomepath = os.path.join(getBeamHomePath(), '');
    if filepath.startswith(beamhomepath):
        filepath = filepath.removeprefix(beamhomepath)

    return filepath

def getBeamResourcesPath():
    if getattr(sys, 'frozen', False):
        for resources_path in _get_frozen_resources_candidates():
            if _is_valid_resources_root(resources_path):
                return resources_path

    return os.path.join(getBeamHomePath(), "resources")

#
# config directory in user ~/.beam/"
def getBeamConfigPath():
    userhomepath = getUserHomePath()
    beamconfigpath = os.path.join(os.path.expanduser("~"), ".beam")

    return beamconfigpath





# for GUI
logLevelList = ["Critical", "Error", "Warning", "Info", "Debug"]

def setLogLevel(loglevelname):
    loglevelid = getLogLevelId(loglevelname)
    rootLogger = logging.getLogger()
    rootLogger.setLevel(loglevelid)


def getLogLevelId(loglevelname):
    try:
        logLevelDict = {
            'Debug': logging.DEBUG,
            'Info': logging.INFO,
            'Warning': logging.WARNING,
            'Error': logging.ERROR,
            'Critical': logging.CRITICAL
        }
        # set now loglevelname from configfile
        loglevelid = logLevelDict[loglevelname]
    except Exception as e:
        logging.error("beam: unknown loglevelname: '" + loglevelname + "', using Debug'")
        loglevelid = logging.DEBUG

    return loglevelid


def mergeDict(sourceDict, targetDict):
    for key, value in sourceDict.items():
        # Add new key values
        if key not in targetDict:
            # insert key
            targetDict[key] = sourceDict[key]
            continue
        else:
            # update key
            if isinstance(value, (str, int, float)):
                targetDict[key] = sourceDict[key]
            if isinstance(value, dict):
                mergeDict(targetDict[key], sourceDict[key])
            if isinstance(value, list):
                # updateList(original[key], update[key])
                # keep lists in targetDict
                pass
    return targetDict


def complementDict(sourceDict, targetDict):
    for key, value in sourceDict.items():
        # Add new key values
        if key not in targetDict:
            # insert key
            targetDict[key] = sourceDict[key]
            continue

    return targetDict


def updateList(original, update):
    # Make sure the order is equal, otherwise it is hard to compare the items.
    assert len(original) == len(update), "Can only handle equal length lists."

    for idx, (val_original, val_update) in enumerate(zip(original, update)):
        if not isinstance(val_original, type(val_update)):
            raise ValueError(f"Different types! {type(val_original)}, {type(val_update)}")
        if isinstance(val_original, dict):
            original[idx] = mergeDict(original[idx], update[idx])
        if isinstance(val_original, (tuple, list)):
            original[idx] = updateList(original[idx], update[idx])
        if isinstance(val_original, (str, int, float)):
            original[idx] = val_update

    return original
