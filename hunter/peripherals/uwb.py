"""
Functions for communicating with the API of the Decawave DWM1001-DEV UWB board
Board can be connected over spi or serial, so we have functions for both
"""
import logging
import time

import spidev

# "In the DWM1001 SPI scheme, the dummy bytes are octets of value 0xFF."
DUMMY_BYTE = 0xFF
DUMMY_MESSAGE = [DUMMY_BYTE]
UWB_SERIAL_BAUDRATE = 115200

# DWM byte codes
# ERROR CODES
DWM_ERROR_CODES = {0: 'no error',
                   1: 'unknown command or broken TLV frame',
                   2: 'internal error',
                   3: 'invalid parameter',
                   4: 'busy'
                   }

# API calls
DWM_LOC_GET_MSG = [0x0c, 0x00]
DWM_POS_GET_MSG = [0x02, 0x00]

# Return types
DWM_RETURN_BYTE = 0x40
DWM_POSITION_RETURN_TYPE = 0x41
DWM_POSITION_RETURN_EXPECTED_LENGTH = 13
DWM_LOC_GET_RETURN_TYPE = 0x49

def get_anchors_from_response(response):
    """
    Extract the anchor information from a loc_get response
    and return it as a list of dicts
    :param response: bytes from DWM1001
    :return: list of anchors
    """
    # todo get count byte
    # for each in count
    # parse anchor
    pass


def get_position_from_response(response):
    """
    Converts a byte array to a dict based on the position object.
    :param response: bytearray received from DWM1001-dev
    :returns dict formatted as below

    (From DWM1001-API-Guide)
    Position
    13-byte position information of the node (anchor or tag).
    position = x, y, z, qf : bytes 0-12, position coordinates and quality factor
    x : bytes 0-3, 32-bit integer, in millimeters
    y : bytes 4-7, 32-bit integer, in millimeters
    z : bytes 8-11, 32-bit integer, in millimeters
    qf : bytes 12, 8-bit integer, position quality factor in percent
    """
    if len(response) == 12:
        return {
            'x': int.from_bytes(response[0:3], byteorder='little'),
            'y': int.from_bytes(response[4:7], byteorder='little'),
            'z': int.from_bytes(response[8:11], byteorder='little'),
            'qf': response[12]
        }

    else:
        print('Bad UWB position response.')


def init_spi(bus=0, device=0, max_speed_hz=80000):
    # Init spi connection and return
    spi = spidev.SpiDev()
    spi.open(bus, device)
    spi.max_speed_hz = max_speed_hz
    return spi


# todo: make this async, and add a proper timeout
def spi_api_call(spi, message):
    """ NOTE: use tag_cfg to make sure hardware/pins ok!
    FULL DUPLEX MUST WRITE TO READ
    Write dummy to force read of single byte
    If byte is nonzero, response is ready
    read x bytes as the response
    """
    # Send message, should get dummy back
    result = spi.xfer2(message)
    if result != DUMMY_MESSAGE:
        print("BAD dummy response from spi dwm message!")
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
                msg_return = spi.xfer2(dummy_get)
                print(msg_return)
                break
            time.sleep(0.3)
        except KeyboardInterrupt:
            pass


def serial_api_call(serial_connection, message):
    """Make a call to the DWM1001-dev api
    over a serial connection
    :param serial_connection: connection to dwm board
    :param message: api_message to send (must be bytes or bytearray)
    :returns array of bytes, 0 if error
    """
    # Write
    serial_connection.write(message)
    # First byte is return code
    # then how long (in bytes) response is
    # and error code. (should be 0)
    (return_byte, response_length, error_code, return_object_type, return_object_type_length) = serial_connection.read(
        5)
    # Check the Error code
    if error_code == DWM_ERROR_CODES[0]:
        # All is well, return the rest of the response
        response = [return_object_type, return_object_type_length]
        return response.append(serial_connection.read(return_object_type_length))
    else:
        logging.error('DWM position call error: {}'.format(DWM_ERROR_CODES[error_code]))
        return 0


def dwm_serial_get_pos(serial_connection, message):
    """Make a dwm_get_pos call to the decawave
    and parse the response into something more friendly
    :param serial_connection: UART connection to DWM1001-DEV
    :param message: api code
    :returns position dict
    """
    response = serial_api_call(serial_connection, message)
    uwb_locations = {}
    if response != 0:
        # make sure we're getting what we expect
        if response[0] == DWM_POSITION_RETURN_TYPE:
            if response[1] != DWM_POSITION_RETURN_EXPECTED_LENGTH:
                logging.error("Bad dwm_get_pos response. Length wrong")
            else:
                uwb_locations['position'] = get_position_from_response(response[2:DWM_POSITION_RETURN_EXPECTED_LENGTH + 1])
        elif response[0] == DWM_LOC_GET_RETURN_TYPE:
            # more to do, get the anchors as well
            uwb_locations['anchors'] = get_anchors_from_response(response)
        else:
            logging.error("Bad dwm_get_pos return type: {}".format(response[0]))
        return uwb_locations


def dwm_serial_get_loc(serial_connection):
    """
    call dwm_loc_get:
    "Get last distances to the anchors (tag is currently ranging to) and the associated position. The interrupt is
    triggered when all TWR measurements have completed and the LE has finished. If the LE is disabled, the distances
    will just be returned. This API works the same way in both Responsive and Low-Power tag modes."

    :param serial_connection:connection to dwm-1001
    :return: dwm_loc dict with position and found anchors
    """
    return dwm_serial_get_pos(serial_connection, DWM_LOC_GET_MSG)

