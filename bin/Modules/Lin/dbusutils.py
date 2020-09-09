#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    Copyright (C) 2014 Mikael Holber http://http://www.beam-project.com
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
# An Mpris2 angepasst von Dominik und Peter Wenger 27.11.18

# will only get used by linux modules
import logging

import dbus
# import importlib
# dbus_specs = importlib.util.find_spec("dbus")
# dbus = importlib.util.module_from_spec(dbus_specs)
# dbus_specs.loader.exec_module(dbus)


def getDbusSession(serviceStr, objectStr, ownerStr = None):
    sessBus = dbus.SessionBus()
    if ownerStr:
        sessBus.name_has_owner(ownerStr)
    dbusSess = sessBus.get_object(serviceStr, objectStr)
    # player = bus.get_object('org.mpris.MediaPlayer2.clementine', '/org/mpris/MediaPlayer2')

    return dbusSess


def getDbusPlayerValue(dbusSess, propertyStr, interfaceStr='org.freedesktop.DBus.Properties'):
    objectStr = 'org.mpris.MediaPlayer2.Player'
    dbusPropVal = dbusSess.Get(objectStr, propertyStr, dbus_interface=interfaceStr)
    # StatusString = player.Get('org.mpris.MediaPlayer2.Player', 'PlaybackStatus', dbus_interface='org.freedesktop.DBus.Properties')
    return dbusPropVal


def getDbusInterface(dbusObj, interfaceStr):
    dbusInterface = dbus.Interface(dbusObj, interfaceStr)
    return dbusInterface


def getDbusSessionStatus(serviceStr):
    try:
        dbusSess = getDbusSession(serviceStr, "/org/mpris/MediaPlayer2")
        playbackStatus = getDbusPlayerValue(dbusSess, 'PlaybackStatus')
    except Exception as e:
        logging.debug(e)
        dbusSess = None
        playbackStatus = 'PlayerNotRunning'

    return dbusSess, playbackStatus