"""
Simplified version of script for scratch performance.  No OOP, just what we need.
"""
import hunter.peripherals.uwb.uart as uwb
import time
import serial
import random
import asyncio
import concurrent.futures
from concurrent.futures import CancelledError
import logging
import hunter.utils as utils
from shapely.geometry import Point
from operator import itemgetter
import pdb

logging.basicConfig(
	level=logging.DEBUG, format='%(asctime)s %(levelname)s:%(message)s')
logging.getLogger(__name__).addHandler(logging.NullHandler())



""" Morse codes for morse decoder """
morse_codes = {'A': '.-', 'B': '-...', 'C': '-.-.',
               'D': '-..', 'E': '.', 'F': '..-.',
               'G': '--.', 'H': '....', 'I': '..',
               'J': '.---', 'K': '-.-', 'L': '.-..',
               'M': '--', 'N': '-.', 'O': '---',
               'P': '.--.', 'Q': '--.-', 'R': '.-.',
               'S': '...', 'T': '-', 'U': '..-',
               'V': '...-', 'W': '.--', 'X': '-..-',
               'Y': '-.--', 'Z': '--..',

               '0': '-----', '1': '.----', '2': '..---',
               '3': '...--', '4': '....-', '5': '.....',
               '6': '-....', '7': '--...', '8': '---..',
               '9': '----.'
               }

code_lookup = {v: k for k, v in
               morse_codes.items()
               }

class GhostHunter(object):
    """ This class contains all the various hunter detector
         functions, merged together for ease of deployment """

    microbit_serial_address = '/dev/ttyACM1'
    microbit_serial = None
    SEPARATOR = "::"
    uwb_serial_address = '/dev/ttyACM0'
    uwb_serial = None
    # last position object received from DWM board
    uwb_pos = None
    # tolerance (in mm) to ignore so that we don't mistake
    # fluctuation in uwb readings for hunter movement
    uwb_tolerance = 100
    # These are shapely geometries of things the device can detect
    # dict of lists split by level/room, updated by server as hunt develops
    detectable_things = None
    # Current level - in scratch this will be the room we're in
    current_level = 0

    #Is the main loop on?
    running = False
    DEBUG_MODE = False

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

    """ variable settings for all devices """

    # Ghost Radar
    radar_settings = {
        # Detection range (in mm)
        "device_range": 5000,
    }

    # Ectoscope
    ectoscope_settings = {
        # Detection range (in mm)
        "device_range": 500
    }

    # Spirit Signs
    spiritsign_settings = {
        # sigils that can be decoded
        'signs': {
            # empty sign for convenience of making real ones
            "90000:00000:00000:00000:00000": "Test",
            "90009:00000:00000:00000:90009": "BOO!"
        }
    }

    async def main_device_loop(self):
        """ Where the magic happens."""
        try:
            logging.debug("Starting main loop")
            while True:
                try:
                    # get position

                    # message from server

                    # message from microbit
                    microbit_message = self.microbit_read()
                    if microbit_message is not None:
                        pdb.set_trace()
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

    def hunt(self, message):
        msg = str(message, 'UTF-8')
        (code, value) = msg.split(self.SEPARATOR)
        result = None
        if code == self.microbit_device_codes['radar']:
            result = self.ghost_scan()
        elif code == self.microbit_device_codes['ectoscope']:
            result = self.ecto_scan()
        return result


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
            msg = code + bytes(self.SEPARATOR + message, 'utf-8') + b'\n'
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

    """ **************  Hunting functions *********************   """

    def scan(self, settings):
        """ Scan function used for both radar and ectoscope """
        logging.debug("Ghost radar scanning...")
        pos = self.uwb_pos
        if pos:
            # Compare current position in a 360 circle, see if intersects
            # with any phenomena
            detected_things = self.detect_things(
                pos['position']['x'],
                pos['position']['y'],
                settings['device_range'],
                self.current_level
            )
            if len(detected_things) > 0:
                # Something found, display proximity to nearest thing
                return self.thing_found(detected_things[0], settings)
        # todo return not found value to microbit
        return [self.MICROBIT_CODES['image'], '0']

    # def parse_microbit_serial_message(self, message):
    #     """Parse any messages from microbit and
    #     add to command queue as necesssary
    #
    #     :param message: line from micro:bit in bytes
    #     :return command from message, if present
    #     """
    #     command = None
    #     # '{}::{}\n'
    #     # code = message[0:1]
    #     # value = str(message[2:-1], 'UTF-8')
    #     msg = str(message, 'UTF-8')
    #     code = msg[0]
    #     pdb.set_trace()
    #     if code in self.microbit_device_codes.values():
    #         self.command_queue[self.COMMAND_HUNT] = message
    #
    #     return command

    def ghost_scan(self):
        """ Ghost radar scan"""
        return self.scan(self.radar_settings)

    def ecto_scan(self):
        """ Ecto scan """
        if self.DEBUG_MODE:
            # todo test value needed
            return random.random()
        else:
            return self.scan(self.ectoscope_settings)

    def telegraph_transmit(self, msg):
        """ Receive morse code from Micro:bit, return decoded letter """

        if self.DEBUG_MODE:
            letter = "A"
        else:

            if msg in code_lookup:
                letter = code_lookup[msg]
            else:
                # bad code
                letter = '?'
        return [self.MICROBIT_CODES['data'], letter]

    def decode_spiritsign(self, sign):
        """ receive microbit.Image of sigil, return decoded string """
        if self.DEBUG_MODE:
            translation = "TEST"
        else:
            if sign in self.spiritsign_settings['signs']:
                translation = self.spiritsign_settings['signs'][sign]
            else:
                # bad sign
                translation = '?'
        return [self.MICROBIT_CODES['data'], translation]


    #########  UWB Functions ######################

    def detect_things(self, x, y, device_range, level=0):
        """
        Use shapely to find 'detectable' objects
        :param level: to separate storeys of a building, or rooms
        :return: features found, None if nothing found
        """
        detected_things = list()
        if self.uwb_pos and self.detectable_things:

            # Make a point from current coordinates, buffer it
            detection_zone = Point(
                float(x), float(y)).buffer(device_range)
            # Get all detectable features for this level
            for thing in self.detectable_things[level]:
                if detection_zone.intersects(thing['geometry']):
                    detected_thing = thing
                    # distance between point of detection and player
                    detected_thing['distance'] = Point(
                        x, y).distance(thing['geometry'])
                    detected_things.append(detected_thing)
        # sort by nearest
        detected_things = sorted(detected_things, key=itemgetter('distance'))
        return detected_things

    # todo async?
    def thing_found(self, detected_thing, settings):
        """
        Display that a thing has been found using Micro:bit
        - log thing found in hunt log
        :param detected_thing: thing detected
        :return: true when done
        """

        # create microbit detection animation based on distance

        return [self.MICROBIT_CODES['data'],
                str(1 - (detected_thing['distance'] / settings['device_range']))
                ]




def main():
    #######     Startup            #########

    hunter = GhostHunter()

    # Test and open serials
    hunter.init_serial_connections()
    if hunter.microbit_serial is not None:
        hunter.microbit_reset()
    # Server?

    ####### Main command loop     #######
    hunter.running = True
    loop = asyncio.get_event_loop()
    #with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    loop.run_until_complete(asyncio.gather(
        hunter.main_device_loop()
    ))

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