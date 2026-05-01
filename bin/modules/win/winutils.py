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
#
#    Revision History:
#
#    Version 1.0
#    	- Initial release
#
import logging
import subprocess
try:
    import pythoncom
    import win32com.client
except ImportError:
    pass


###############################################################
#
# Application running Windows-specific
#
###############################################################

def applicationrunning(appname):
    normalized_app_name = str(appname).strip().lower()
    if normalized_app_name == '':
        logging.debug("winutils.applicationrunning(): empty app name")
        return False

    for method_name, command in (
        ('wmic', ['wmic', 'process', 'get', 'Caption']),
        ('tasklist', ['tasklist', '/FO', 'CSV', '/NH']),
    ):
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
            )
        except Exception as error:
            logging.debug(
                "winutils.applicationrunning(%s): %s invocation failed: %s",
                appname,
                method_name,
                error,
                exc_info=True,
            )
            continue

        stdout = result.stdout or ''
        stderr = (result.stderr or '').strip()
        if result.returncode not in (0,):
            logging.debug(
                "winutils.applicationrunning(%s): %s returned code %s stderr=%s",
                appname,
                method_name,
                result.returncode,
                stderr,
            )
            continue

        for line in stdout.splitlines():
            if normalized_app_name in line.lower():
                logging.debug(
                    "winutils.applicationrunning(%s): found process via %s",
                    appname,
                    method_name,
                )
                return True

        logging.debug(
            "winutils.applicationrunning(%s): %s completed but process not found",
            appname,
            method_name,
        )

    logging.debug("winutils.applicationrunning(%s) = False", appname)
    return False