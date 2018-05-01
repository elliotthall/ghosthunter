"""Functions to communicate with the DWM1001-DEV over serial peripherhal interfacet (SPI)
IMPORTANT NOTE: these functions are still at the experimental stage and are not complete
the project is currently using the UART functions."""
import spidev
import time

# "In the DWM1001 SPI scheme, the dummy bytes are octets of value 0xFF."
DUMMY_BYTE = 0xFF
DUMMY_MESSAGE = [DUMMY_BYTE]


def init_spi(bus=0, device=0, max_speed_hz=80000):
    # Init spi connection and return
    spi = spidev.SpiDev()
    spi.open(bus, device)
    spi.max_speed_hz = max_speed_hz
    return spi


# todo: add a proper timeout
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