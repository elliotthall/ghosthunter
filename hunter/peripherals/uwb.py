"""
Functions for communicating with the API of the Decawave DWM1001-DEV UWB board
Board can be connected over spi or serial, so we have functions for both
"""
import time
import spidev

# "In the DWM1001 SPI scheme, the dummy bytes are octets of value 0xFF."
DUMMY_BYTE = 0xFF
DUMMY_MESSAGE = [DUMMY_BYTE]
UWB_SERIAL_BAUDRATE = 115200

# DWM byte codes
DWM_RETURN_BYTE = 0x40
DWM_ERROR_CODES = {1: 'unknown command or broken TLV frame',
                   2: 'internal error',
                   3: 'invalid parameter',
                   4: 'busy'
                   }

def response_to_position(response):
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
    return_byte, response_length, error_code = serial_connection.read(3)
