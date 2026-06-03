# -*- encoding: utf-8 -*-
#    Copyright (C) 2014 Mikael Holber http://www.beam-project.com
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
# Platform facade for the OS-level "Now Playing" source. Picks the right backend
# the same way the per-app modules split win/lin: Windows -> SMTC (smtcmodule),
# Linux -> MPRIS (mprismodule). Both backends expose the identical public API
# (aumid_friendly_name / list_sessions / run_with_details / run), so the UI and
# nowplayingdata talk only to this facade and never import an OS module directly.

import platform

_backend = None
if platform.system() == 'Windows':
    from bin.modules.win import smtcmodule as _backend
elif platform.system() == 'Linux':
    from bin.modules.lin import mprismodule as _backend


def is_available():
    # True only on a platform with a Now Playing backend. Note this does not
    # check whether the backend's optional dependency imported - run_with_details
    # reports that via details['route'] == 'unavailable'.
    return _backend is not None


def aumid_friendly_name(identifier):
    if _backend is None:
        return identifier
    return _backend.aumid_friendly_name(identifier)


def list_sessions(timeout=5):
    if _backend is None:
        return []
    return _backend.list_sessions(timeout)


def run_with_details(MaxTandaLength, preferred_aumid=''):
    if _backend is None:
        return [], 'PlayerNotRunning', {'route': 'unavailable', 'aumid': '', 'appName': '', 'sessionCount': 0}
    return _backend.run_with_details(MaxTandaLength, preferred_aumid)


def run(MaxTandaLength, preferred_aumid=''):
    if _backend is None:
        return [], 'PlayerNotRunning'
    return _backend.run(MaxTandaLength, preferred_aumid)
