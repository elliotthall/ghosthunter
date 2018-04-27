import time
import serial

serial_address = '/dev/tty.usbmodem231'
serial_connection = serial.Serial(serial_address, 115200, timeout=3)

def serial_api_call(serial_connection, message):
    """Make a call to the DWM1001-dev api
    over a serial connection
    Write dummy to force read of single byte
    If byte is nonzero, response is ready
    read x bytes as the response
    """
    serial_connection.write(message)
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


class position_response(dwm_response):
    """
    Converts the bytearray response of the decawave
    into something we can use
    """
    # int.from_bytes(b'y\xcc\xa6\xbb', byteorder='little')