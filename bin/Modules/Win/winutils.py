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

    cmd = 'WMIC PROCESS get Caption'
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    for line in proc.stdout:
        # line throws TypeError
        # a bytes-like object is required, not 'str'
        caption = line.decode('utf8')
        if appname in caption:
            proc.kill()
            logging.debug("winutils.AppplicationRunning() = True");
            return True
    proc.kill()

    logging.info("winutils.AppplicationRunning() = False")
    return False