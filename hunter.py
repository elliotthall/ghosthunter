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
    #Is the main loop on?
    running = False

    microbit_device_codes = {
        'radar': 'G',
        'ectoscope': 'E',
        'telegraph': 'T',
        'spiritsign': 'S'
    }

    MICROBIT_CODES = {
        'ready': b'\x01',
        'id': b'\x08',
        'id_return': b'\x09',
        'hunt': b'\x10',
        'acc': b'\x11',
        'toggle_acc': b'\x15',
        'pixel': b'\x12',
        'image': b'\x13',
        'reset': b'\x14',
        'data': b'\x18',

    }

    async def main_device_loop(self):
        """ Where the magic happens."""
        try:
            self.running = True
            logging.debug("Starting main loop")
            self.log_position()
            while True:
                try:
                    # get position

                    # message from server

                    # message from microbit
                    microbit_message = self.microbit_read()
                    if microbit_message is not None:
                        # Do hunt
                        self.hunt(microbit_message)

                    await asyncio.sleep(0.1)
                except CancelledError:
                    logging.debug("execute_commands cancelled")
                    break
                except KeyboardInterrupt:
                    print('Interrupted')
                    break
        except CancelledError:
            logging.debug("execute_commands cancelled")
        finally:
            self.running = False
            logging.debug("Stopping main loop")

        return True

    def hunt(self,message):
        pass

    async def log_position(self):
        """ Get the uwb position if it can and log it"""
        while self.running is True:
            # Get uwb position
            # if it's not empty
            # have we got an xy for the room? log it
            #are we near any points of interest? log it
            logging.debug("Position logged")
            await asyncio.sleep(30)
        return True



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

    def close_serial_connections(self):
        if self.uwb_serial is not None:
            self.uwb_serial.close()
        if self.microbit_serial is not None:
            self.microbit_serial.close()

    # ********** Micro:Bit functions ****************

    def microbit_read(self):
            """
            If microbit port is open and data present, read and return
            :return: line from microbit serial
            """
            if self.microbit_serial.is_open:
                if self.microbit_serial.in_waiting > 0:
                    line = self.microbit_serial.readline()
                    return line
                else:
                    return None
            else:
                logging.warning('Trying to read microbit msg over closed uart')

    def microbit_write(self, code, message='0', delay=0.1):
        """
        Send a message to the Micro:bit in the format
        code:separator:message:\n
        :type message:str
        :type code:bytes
        :param code:
        :param message:
        :para, delay: wait before sending results (see note below)
        :return:
        """

        if self.microbit_serial.is_open:
            msg = code + self.SEPARATOR + bytes(message, 'utf-8') + b'\n'
            logging.debug("To mictobit: {}".format(msg))
            #pdb.set_trace()
            """ 
            Added this because returning results 'too fast'
            seems to break the micro:bit. Not sure why yet.
            """
            time.sleep(delay)
            self.microbit_serial.write(msg)
        else:
            logging.warning(
                'Trying to send microbit msg over closed uart {}'.format(
                    message
                ))

    def microbit_reset(self):
        """Send a reset command to the attached micro:bit"""
        self.microbit_write(
            self.MICROBIT_CODES['reset'],
            '0'
        )



def main():
    #######     Startup            #########

    hunter = GhostHunter()

    # Test and open serials
    hunter.init_serial_connections()

    # Server?

    ####### Main command loop     #######
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        loop.run_until_complete(hunter.main_device_loop())

    #####     finish      #############

    # close logs

    # close serial
    hunter.close_serial_connections()


#uwb_serial_address = '/dev/ttyACM0'
#uwb_serial_address = '/dev/tty.usbmodem1451'
#uwb_serial = serial.Serial(uwb_serial_address, 115200, timeout=3)
#uwb.dwm_reset(uwb_serial)
#time.sleep(5)
#print(uwb.dwm_serial_get_loc(uwb_serial))
#uwb_serial.close()


if __name__ == '__main__':
    main()