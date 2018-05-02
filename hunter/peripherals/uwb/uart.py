"""
Functions for communicating with the API of the Decawave DWM1001-DEV UWB board over UART

"""
import logging

import bitstring

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
DWM_LOC_GET_MSG = [0x0C, 0x00]
# just position determined by location engine
DWM_POS_GET_MSG = [0x02, 0x00]
# dwm1001-dev configuration
DWM_CFG_GET_MSG = [0x08, 0x00]
# set board as tag, must reset
DWM_CFG_TAG_MSG = [0x03, 0x04]
DWM_SET_TAG_MSG = b'\x05\x02'
DWM_RESET = [0x14, 0x00]

# Return types
DWM_RETURN_BYTE = 0x40
DWM_POSITION_RETURN_TYPE = 0x41
POSITION_LENGTH = 13
ANCHOR_LENGTH = 20
DWM_LOC_GET_RETURN_TYPE = 0x49

# standard config for tag
# binary string that will be joined and converted
# to two bytes for set_tag_cfg
tag_cfg = {
    # (* BYTE 0 *)
    'low_power_en': '1',
    'loc_engine_en': '1',
    'r1': '0',
    'led_en': '0',
    'ble_en': '1',
    'fw_update_en': '1',
    'uwb_mode': '10',
    # (* BYTE 1 *)
    'b1_reserved': '00000',
    'accel_en': '1',
    'meas_mode': '00'
}


def get_anchors_from_response(serial_connection):
    """
    Extract the anchor information from a loc_get response
    and return it as a list of dicts

    Each anchor response consists of:

            2 bytes UWB address (For Tag, different for anchor)
            4-byte distance
            1-byte distance quality factor
            position in standard 13 byte format

            20 bytes in total

    :param serial_connection: connection to dwm
    :return: list of anchors
    """
    anchors = {}
    # get count byte

    return_type, length, anchor_count = serial_connection.read(3)
    if return_type == DWM_LOC_GET_RETURN_TYPE:
        # for each in count
        for x in range(0, anchor_count):
            # parse anchor
            anchor_bytes = serial_connection.read(20)
            uwb_address = int.from_bytes(anchor_bytes[0:2], byteorder='little')
            anchors[uwb_address] = {
                'distance': int.from_bytes(anchor_bytes[2:6], byteorder='little'),
                'qf': anchor_bytes[6],
                'position': get_position_from_response(anchor_bytes[7:20])
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

    if len(response) == POSITION_LENGTH:
        return {
            'x': int.from_bytes(response[0:3], byteorder='little'),
            'y': int.from_bytes(response[4:7], byteorder='little'),
            'z': int.from_bytes(response[8:11], byteorder='little'),
            'qf': response[12]
        }

    else:
        print('Bad UWB position response.')


def serial_api_call(serial_connection, message, call_type='get'):
    """Make a get call to the DWM1001-dev api
    over a serial connection
    :param serial_connection: connection to dwm board
    :param message: api_message to send (must be bytes or bytearray)
    :param call_type: get or set api call
    :returns array of bytes, 0 if error
    """
    # Write
    serial_connection.write(message)
    # First byte is return code
    # then how long (in bytes) response is
    # and error code. (should be 0)
    (return_byte, response_length, error_code) = serial_connection.read(3)
    # Check the Error code
    if int(error_code) == 0:
        # All is well, return the rest of the response
        if call_type == 'get':
            (return_object_type, return_object_type_length) = \
                serial_connection.read(2)
            response = [return_object_type, return_object_type_length]
            response.append(serial_connection.read(return_object_type_length))
            return response
        else:
            return return_byte, response_length, error_code
    else:
        logging.error('DWM position call error: {}'.format(DWM_ERROR_CODES[int(error_code)]))
        return error_code


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
                    bytearray(response[2]))
            if message == DWM_LOC_GET_MSG:
                # more to do, get the anchors as well
                uwb_locations['anchors'] = get_anchors_from_response(
                    serial_connection)
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


def dwm_reset(serial_connection):
    """Send the reset command to the DWM board"""
    serial_api_call(serial_connection, DWM_RESET, 'set')


def dwm_serial_get_cfg(serial_connection):
    """ Retrieve the current config as two bytes and pass to parser.

    :param serial_connection:
    :return:
    """
    response = serial_api_call(serial_connection, DWM_CFG_GET_MSG)
    return get_cfg_from_response(response[2])


def get_cfg_from_response(response):
    """
    parse get_cfg response

    2 config bytes - (2) denotes attribute that is two bits, all others 1
(* BYTE 0 *)
 low_power_en
 loc_engine_en
 reserved
 led_en
 ble_en
 fw_update_en
 (2)uwb_mode
(* BYTE 1 *)
(2) reserved
mode : 0 - tag, 1 - anchor
initiator
bridge
accel_en
(2)meas_mode : 0 - TWR, 1-3 not supported

    :param response: 2 bytes from dwm_cfg_get
    :return: dict of dwm configuration
    """
    try:
        cfg_bytes = bitstring.BitArray(bytes=response)
        cfg = {
            'low_power_en': cfg_bytes[0],
            'loc_engine_en': cfg_bytes[1],
            'reserved': cfg_bytes[2],
            'led_en': cfg_bytes[3],
            'ble_en': cfg_bytes[4],
            'fw_update_en': cfg_bytes[5],
        }
        cfg['uwb_mode'] = cfg_bytes[6:8].int * -1
        if cfg_bytes[10]:
            cfg['mode'] = 'anchor'
        else:
            cfg['mode'] = 'tag'
        cfg['initiator'] = cfg_bytes[11]
        cfg['bridge'] = cfg_bytes[12]
        cfg['accel_en'] = cfg_bytes[13]
        # ignoring meas_mode for the moment
        return cfg
    except IndexError:
        logging.error("Bad cfg response {}".format(response))


def set_tag_cfg(serial_connection, tag_cfg):
    """Set the attached dwm to tag configuration
    2 bytes sent, bit configuration:
    (* BYTE 0 *) (bit 7) low_power_en (bit 6) loc_engine_en (bit 5) reserved (bit 4) led_en (bit 3) ble_en (bit 2) fw_update_en (bits 0-1) uwb_mode
    (* BYTE 1 *) (bits 3-7) reserved (bit 2) accel_en (bits 0-1) meas_mode : 0 - TWR, 1-3 reserved

    :param serial_connection:
    :param tag_cfg configuration dict to be made into bytes
    :return: error_code
    """
    cfg_string = ''.join(tag_cfg.values())
    cfg_tag = bitstring.BitArray(bin=cfg_string)
    (return_byte, response_length, error_code) = serial_api_call(serial_connection,bytearray(DWM_SET_TAG_MSG)+cfg_tag.bytes,'set')
    return error_code
