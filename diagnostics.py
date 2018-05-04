import logging
import sys
import time
import serial
import hunter.peripherals.uwb.uart as uwb

logging.basicConfig(stream=sys.stdout,
                    level=logging.INFO,
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
    # logging.info("Setting tag configuration")
    # uwb.set_tag_cfg(serial_connection, tag_cfg)
    # time.sleep(0.5)
    # logging.info("Resetting board")
    # uwb.dwm_reset(serial_connection)
    # time.sleep(1)
    # logging.info("Getting updated dwm config")
    cfg = uwb.dwm_serial_get_cfg(serial_connection)
    logging.info("DWM1001-DEV config: {}".format(cfg))
    logging.info("Location test")
    loc = uwb.dwm_serial_get_loc(serial_connection)
    logging.info("get_loc : {}".format(loc))
    serial_connection.close()


if __name__ == '__main__':
    uwb_diagnostics()
