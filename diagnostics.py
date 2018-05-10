"""
Functions to test the ghost detector hardware
NOT unit tests, must be run on the hardware
"""

import logging
import sys
import time
import serial
import asyncio
import hunter.peripherals.uwb.uart as uwb
from hunter.core import HunterUwbMicrobit
import concurrent.futures
from concurrent.futures import CancelledError
import hunter.exceptions as exceptions


logging.basicConfig(stream=sys.stdout,
                    level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s:%(message)s')



tag_cfg = {
    # (* BYTE 0 *)
    'low_power_en': '0',
    'loc_engine_en': '1',
    'r1': '0',
    'led_en': '1',
    'ble_en': '1',
    'fw_update_en': '1',
    'uwb_mode': '10',
    # (* BYTE 1 *)
    'b1_reserved': '00000',
    'accel_en': '1',
    'meas_mode': '00'
}

uwb_serial_address = '/dev/cu.usbmodem1431'


def uwb_diagnostics():
    """Hardware tests for the DWM1001-DEV"""
    logging.info("Opening connection on {}".format(uwb_serial_address))
    serial_connection = serial.Serial(uwb_serial_address, 115200, timeout=3)
    logging.info("Setting tag configuration")
    uwb.set_tag_cfg(serial_connection, tag_cfg)
    time.sleep(0.5)
    logging.info("Resetting board")
    uwb.dwm_reset(serial_connection)
    time.sleep(1)
    logging.info("Getting updated dwm config")
    cfg = uwb.dwm_serial_get_cfg(serial_connection)
    logging.info("DWM1001-DEV config: {}".format(cfg))
    logging.info("Location test")
    loc = uwb.dwm_serial_get_loc(serial_connection)
    logging.info("get_loc : {}".format(loc))
    serial_connection.close()

def microbit_diagnostics(hunter):
    # serial_connection = serial.Serial(uwb_serial_address, 115200, timeout=3)
    logging.debug("Opening Micro:Bit connection on {}".format(uwb_serial_address))

    # test reset
    hunter.microbit_flush()
    hunter.microbit_reset()

    # image
    hunter.microbit_flush()
    logging.debug('Testing image')
    image = "500;;90009:90009:90009:90009:90009,99099:90009:90009:99099:90009"
    m = hunter.MICROBIT_CODES['image']+b'\xFF' + bytes(image, 'utf-8') + b'\n'
    hunter.microbit_serial.write(m)

    # turn on acc
    logging.debug('Toggle acc on')
    hunter.microbit_flush()
    hunter.microbit_toggle_acc(1)

    # get acc data
    acc= hunter.microbit_read()
    # verify

    logging.debug('ACC data:{}')
    # off
    hunter.microbit_toggle_acc(0)


    # prompt for input test
    hunter.microbit_flush()
    return True



def startup_test(hunter):
    """ Run the bootup, confirm hardware is responding"""
    # do startup, return true if done
    #hunter.init_serial_connections()
    hunter.bootup()

def general_function_test(hunter):
    """ Test the general functions
     - Get a position from the board
     - Send a display command to the micro:bit
     - prompt and wait for button input
     - Acceleremoter?
    """
    # do startup, return true if done
    pass

# todo Add device-specifc tests when ready

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        hunter = HunterUwbMicrobit(loop, executor)
        hunter.hunt_url = 'ws://demos.kaazing.com/echo'
        hunter.MAC = '78:4f:43:6c:cc:0f'
        try:
            if startup_test(hunter):
                general_function_test(hunter)
        finally:
            hunter.shutdown()
            loop.close()
