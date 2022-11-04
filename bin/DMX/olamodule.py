#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    Copyright (C) 2022 Piotr R. Sidorowicz http://http://www.beam-project.com
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
#       - Initial release
#
# This Python file uses the following encoding: utf-8
import time
import subprocess
import sys
import logging

import array
from ola.ClientWrapper import ClientWrapper
import sys

###############################################################
#
# Define operations
#
###############################################################

wrapper = None

def startOlad ():

    try:
        result = subprocess.run (["olad", "-f"], capture_output=True, text=True)

        logging.info(result.stdout, exc_info=True)
        logging.info(result.stderr, exc_info=True)
        logging.info("Olad started", exc_info=True)
        time.sleep(2)
    except Exception as e:
        logging.error(e, exc_info=True)
    return []

def stopOlad ():

    try:
        result = subprocess.run (["ps", "-C", "olad", "-o", "pid="], capture_output=True, text=True)
        pid = result.stdout
        if "" != pid.strip() :
            result = subprocess.run (["kill", pid.strip()], capture_output=True, text=True)
            logging.info(result.stdout, exc_info=True)
            logging.info(result.stderr, exc_info=True)
            logging.info("Olad stopped", exc_info=True)

    except Exception as e:
        logging.error(e, exc_info=True)

    return []


def DmxSent(status):
    if status.Succeeded():
        logging.debug("...DmxSent: Success!")
    else:
        logging.debug("Error: " + str(status.message))

    global wrapper

    if wrapper:
        wrapper.Stop()

def sendDMXrequest (universe: object, datalist: object) -> object:
    global wrapper

    logging.debug("... universe: %s", universe)
    # logging.debug("... Datalist: " + datalist)
    #datalist = [255, 0, 0, 0, 0, 0, 0, 255, 255, 255, 100, 0]
    data = array.array('B')
    for x in datalist:
        data.append(x)

    wrapper = ClientWrapper()
    client = wrapper.Client()
    client.SendDmx(universe, data, DmxSent)
    wrapper.Run()

## Broken. Do not use. Here be dragons
# def NewData(data):
#     logging.debug("...DmxReceived: " + list(data))
#
#     return ''
#
# def getDMXdata (universe: object) -> object:
#     global wrapper
#
#     wrapper = ClientWrapper()
#     client = wrapper.Client()
#     client.RegisterUniverse(universe, client.REGISTER, NewData)
#     wrapper.Run()
