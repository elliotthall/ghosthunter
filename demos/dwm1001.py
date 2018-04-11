#!/usr/bin/python3
import time

import spidev

"""
From firmware
Pin 19
MOSI
MOSI
Pin 21
MISO
MISO
Pin 23
SCLK
SCLK
Pin 25
GND
GND
Pin 24
CSN
CSN

Note: the connector J10 on the DWM1001 DEV board is compatible with Raspberry Pi 3 connector J8 header pins 1-26. Pin 
4 from J10 provides 5V power from Raspberry Pi to the DWM1001 DEV board.

"""

# "In the DWM1001 SPI scheme, the dummy bytes are octets of value 0xFF."
DUMMY_BYTE = 0xFF
DUMMY_MESSAGE = [DUMMY_BYTE]

# Delay
INIT_DELAY = 0.000005
PMSC_CONFIG_DELAY = 0.00015

# DW1000 TX/RX Modes
IDLE_MODE = 0x00
RX_MODE = 0x01
TX_MODE = 0x02

# Init spi
bus = 0
device = 0
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 80000

def send_api_message(dwm_message,delay=3000):
    """
    Send a message to the DWM chipset using its API codes.
    Wait for response until delay timeout.
    :return dwm byte response (see pdfs)
    """

    return dwm_response

# Test message, dwm_pos_get
msg = [0x02, 0x00]
result = spi.xfer2(msg)
print(result)

# NOTE: use tag_cfg to make sure hardware/pins ok!
# FULL DUPLEX MUST WRITE TO READ
# Write dummy to force read of single byte
# If byte is nonzero, response is ready
# read x bytes as the response
while True:
    try:
        # Write dummy to force read of single byte
        resp = spi.xfer2(DUMMY_MESSAGE)
        if resp[0] != 0:
            # If byte is nonzero, response is ready
            size = resp[0]
            dummy_get = []
            for x in range(1, size):
                dummy_get.append(DUMMY_BYTE)
            print
            "SIZE: {}\n".format(size)
            msg_return = spi.xfer2(dummy_get)
            print(msg_return)
            break
        time.sleep(0.3)
    except KeyboardInterrupt:
        pass
spi.close()
