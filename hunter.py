"""
Simplified version of script for scratch performance.  No OOP, just what we need.
"""
import hunter.peripherals.uwb.uart as uwb
import time
import serial
import asyncio
import concurrent.futures
from concurrent.futures import CancelledError
import logging
from shapely.geometry import Point
logging.basicConfig(
	level=logging.DEBUG, format='%(asctime)s %(levelname)s:%(message)s')
logging.getLogger(__name__).addHandler(logging.NullHandler())


#uwb_serial_address = '/dev/ttyACM0'
uwb_serial_address = '/dev/tty.usbmodem1451'
uwb_serial = serial.Serial(uwb_serial_address, 115200, timeout=3)
#uwb.dwm_reset(uwb_serial)
#time.sleep(5)
#print(uwb.dwm_serial_get_loc(uwb_serial))
#uwb_serial.close()


