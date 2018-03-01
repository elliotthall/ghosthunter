import RPi.GPIO as GPIO
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

Note: the connector J10 on the DWM1001 DEV board is compatible with Raspberry Pi 3 connector J8 header pins 1-26. Pin 4 from J10 provides 5V power from Raspberry Pi to the DWM1001 DEV board.

"""


# "In the DWM1001 SPI scheme, the dummy bytes are octets of value 0xFF."
DUMMY = [0xFF]

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

# Test message, dwm_pos_get
msg= [0x02,0x00]
spi.writebytes(msg)
# FULL DUPLEX MUST WRITE TO READ
# Write dummy to force read of single byte
# If byte is nonzero, response is ready
# read x bytes as the response

	try:
		while True:
			# Write dummy to force read of single byte
			resp = spi.xfer(DUMMY)
			if resp[0] != 0:
				# If byte is nonzero, response is ready
				size = resp[0]
				dummy_get =[DUMMY for x in range(1, size)]				
				msg_return = spi.xfer(dummy_get)
				print (msg_return)
	except KeyboardInterrupt:
		pass
