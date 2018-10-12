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
import hunter.utils as utils
from shapely.geometry import Point
from hunter.devices import MainDevice
logging.basicConfig(
	level=logging.DEBUG, format='%(asctime)s %(levelname)s:%(message)s')
logging.getLogger(__name__).addHandler(logging.NullHandler())
import pdb

class GhostHunter(object):
    """ This class contains all the various hunter detector
         functions, merged together for ease of deployment """

    microbit_serial_address = '/dev/ttyACM1'
    microbit_serial = None
    uwb_serial_address = '/dev/ttyACM0'
    uwb_serial = None
    # last position object received from DWM board
    uwb_pos = None
    # tolerance (in mm) to ignore so that we don't mistake
    # fluctuation in uwb readings for hunter movement
    uwb_tolerance = 100

    def init_serial_connections(self):
        """Establish UART connections to UWB and Micro:bit
        Since addresses are assigned in the order deivces are connected
        Test to make sure """
        # Establish connections
        first_conn = utils.connect_serial(self.uwb_serial_address)
        second_conn = utils.connect_serial(self.microbit_serial_address)
        # Send an id message, verify this is a DWM
        first_conn.write(uwb.DWM_CFG_GET_MSG)
        return_type = first_conn.read()

        # Flush for safety
        first_conn.reset_input_buffer()
        first_conn.reset_output_buffer()
        second_conn.reset_output_buffer()
        second_conn.reset_input_buffer()
        if (int.from_bytes(return_type, byteorder='little')
                == uwb.DWM_RETURN_BYTE):
            # Yes, assign to uwb
            logging.debug('ACM0 assigned to uwb')
            self.uwb_serial = first_conn
            self.microbit_serial = second_conn
            # todo parse the cfg get and configure here?
        else:
            # No, asssign to micro:bit
            logging.debug('ACM1 assigned to uwb')
            self.microbit_serial = first_conn
            self.uwb_serial = second_conn
        return True

#######     Startup     #########

hunter = GhostHunter()

# Test and open serials
hunter.init_serial_connections()



# Main command loop
    # Run endless loop
    # get position
    # message from server
    # message from microbit
       # Do hunt
#finish
# close logs
# close serial



#uwb_serial_address = '/dev/ttyACM0'
#uwb_serial_address = '/dev/tty.usbmodem1451'
#uwb_serial = serial.Serial(uwb_serial_address, 115200, timeout=3)
#uwb.dwm_reset(uwb_serial)
#time.sleep(5)
#print(uwb.dwm_serial_get_loc(uwb_serial))
#uwb_serial.close()

