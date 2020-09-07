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


###############################################################
#
# Define operations
#
###############################################################

import os
import logging

from bin.Modules import traktorModule
from bin.Modules.Win import winutils


def run(maxtandalength, lastplaylist):

    #
    # Player Status
    #
    if winutils.applicationrunning("Traktor.exe"):
        playlist, playbackstatus = traktorModule.run(maxtandalength, lastplaylist)
    else:
        playbackstatus = 'PlayerNotRunning'
        emptyplaylist = []
        return emptyplaylist, playbackstatus

    return playlist, playbackstatus
