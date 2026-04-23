DMX support is available in the DMX branch.  This feature is currently only available for Linux and Mac. This is because Open Lighting Architecture server works only on these platforms.

For Beam to interact with a DMX controlled light, the olad server has to be configured correctly.
Olad configuration is outside of the scope of this document; please refer to [OLA site](https://www.openlighting.org/ola/) for installation and setup. 

Once it is setup correctly, i.e., it is possible to control the lights from the command line, Beam will also be able to do that.

What does Beam really do?

* On start-up, Beam launches olad (the OLA server).
* It sends colour change requests according to the current mood; a specific colour can be defined in mood settings.
* On shutdown, Beam turns the light off and shuts down olad.

Note: Beam uses Universe 1. Eventually, that may be changeable in setup, but for now it is hard-coded.
  
This build has been used successfully on Linux (Ubuntu and derivatives). It should also work on Mac, as per OLA installation instructions, but has not been tested there.

As for hardware, please see OLA documentation on compatibility.

My setup:

* DMX controller: [Enttec DMX USBPRO Mk2](https://www.enttec.com/product/rdm-products/rdm-protocol-controller/dmx-usb-pro-interface/)
* DMX fixture: [ADJ UB 6H](https://www.adj.com/ub-6h)
* [5 to 3 pin DMX adapter](https://www.adj.com/ac5pm3pfm)
* [3 pin DMX cable](https://www.adj.com/ac3pdmx10)

Config notes:

* The DMX controller I use, emulates a serial port (ttyUSB). Hence for the olad to work, make sure that you (username) are a member of the group associated with serial ports. Otherwise olad, that runs with your user permissions, will not have access the ttyUSB device. On Ubuntu it is 'dialout'; on other distros it may be 'tty'. 
```bash
sudo usermod -a -G dialout <username>  # To allow access to the /dev/ttyUSB#
```
Also, you will need to re-login for the group addition to take effect.

* Olad can be configured to use different profiles with ttyUSB (see /etc/ola/*) . Only one of them can talk to an interface an a time. Make sure only the one that is associated with your controller is enabled.