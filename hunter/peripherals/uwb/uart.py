"""
Functions for communicating with the API of the Decawave DWM1001-DEV UWB board
Board can be connected over spi or serial, so we have functions for both
"""
import logging

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
# full location message with position and nearby anchors
DWM_LOC_GET_MSG = [0x0c, 0x00]
# just position determined by location engine
DWM_POS_GET_MSG = [0x02, 0x00]
# dwm1001-dev configuration
DWM_CFG_GET_MSG = [0x08, 0x00]
# set board as tag, must reset
DWM_CFG_TAG_MSG = [0x03, 0x04]

# Return types
DWM_RETURN_BYTE = 0x40
DWM_POSITION_RETURN_TYPE = 0x41
POSITION_LENGTH = 13
ANCHOR_LENGTH = 20
DWM_LOC_GET_RETURN_TYPE = 0x49


def get_anchors_from_response(response):
    """
    Extract the anchor information from a loc_get response
    and return it as a list of dicts

    Each anchor response consists of:

            2 bytes UWB address
            4-byte distance
            1-byte distance quality factor
            position in standard 13 byte format

            20 bytes in total

    :param response: bytes from DWM1001
    :return: list of anchors
    """
    anchors = {}
    # get count byte
    return_type, length, anchor_count = response[0:2]
    if return_type == DWM_LOC_GET_RETURN_TYPE:
        # for each in count
        for x in range(0, (anchor_count - 1)):
            # parse anchor
            anchor_bytes = response[
                           x * ANCHOR_LENGTH:(x + 1) * ANCHOR_LENGTH]
            uwb_address = int.from_bytes(response[0:1], byteorder='little')
            anchors[uwb_address] = {
                'distance': int.from_bytes(response[2:5], byteorder='little'),
                'qf': int.from_bytes(response[6], byteorder='little'),
                'position': get_position_from_response(response[7:19])
            }
    else:
        logging.error('Bad return type for anchor: {}'.format(return_type))
    # todo order anchors by distance?
    return anchors


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
        if response[0] == DWM_POSITION_RETURN_TYPE or response[0] == DWM_LOC_GET_RETURN_TYPE:
            if response[1] != POSITION_LENGTH:
                logging.error("Bad dwm_get_pos response. Length wrong")
            else:
                uwb_locations['position'] = get_position_from_response(
                    response[2:POSITION_LENGTH + 1])
            if response[0] == DWM_LOC_GET_RETURN_TYPE:
                # more to do, get the anchors as well
                uwb_locations['anchors'] = get_anchors_from_response(
                    response[3 + POSITION_LENGTH:])
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


def get_cfg_from_response(response):
    """

    :param response:
    :return:
    """
    try:
        cfg_bytes = response[2:3]

    except IndexError:
        logging.error("Bad cfg response {}".format(response))


def dwm_serial_get_cfg(serial_connection):
    """ Retrieve the current config as two bytes and pass to parser.

    :param serial_connection:
    :return:
    """
    response = serial_api_call(serial_connection, DWM_CFG_TAG_MSG)

# todo Add functions to get/set the board config at startup