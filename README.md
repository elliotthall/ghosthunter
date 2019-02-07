# The Digital Ghost Hunt
### SEEK Ghost Detector Library

This library is part of [The Digital Ghost Hunt](digitalghosthunt.com) an AHRC-funded project in coding education and Immersive theatre.  If you have no idea what that is, visit our website first.  The rest will make more sense.

This repo contains the code for the SEEK Ghost Detector, a MORPH agent's best friend.  The detector is a Raspberry Pi 3 paired over USB to a [Micro:Bit](https://microbit.org/) (the primary interface) and a [Decawave DWM development board](https://www.decawave.com/product/dwm1001-development-board/) (for internal positioning during the show.)  Communication with both is done over UART.

Important scripts:

1. **hunter.py** - The main script that runs the detector.  I've left the detectable objects in the scratch in here so you get an idea of how it worked.
2. **uart.py** - A library for communication with the Decawave board over UART.  
3. **peripherals/microbit/** - These typescripts are written in MakeCode and are flashed on to the microbits.
4. **uwbproxytest.py** - I used this simple script to create the detectable phenomena in AR space.

This branch contains only the code we ended up using in the show, but develop and scratch have historical code I've left in for documentation purposes, and in case I find a use for it later.  

### Requirements


Python 3.5+

The hunter library uses asyncio, and thus requires at least Python 3.5.
(newer versions of Raspbian should have you covered but here is a guide to 
[Installing Python 3.5 on Pi](https://raspberrypi.stackexchange.com/questions/54365/how-to-download-and-install-python-3-5-in-raspbian/56632#56632))

* [pyserial](https://pythonhosted.org/pyserial/) - For uart communication between the Micro:Bit and UWB board
* [bitstring](https://pypi.org/project/bitstring/) - Used in bytestring communication with UWB board
* [shapely](https://pypi.org/project/Shapely/) - Geometry library for determining proximity to spooky phenomena (this needs other libraries see below)

### Other Libraries

Check the Shapely requirements and install the debian packages libgeos++ and python3-shapely if necessary.

### The Future

The Ghost Hunt has received follow on funding to do a new family show in summer 2019. We will haunt again.
