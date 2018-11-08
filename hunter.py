"""
Simplified version of script for scratch performance.  No OOP, just what we
need.
"""
import asyncio
import logging
import math
import random
import time
from concurrent.futures import CancelledError
from operator import itemgetter
import pdb
from uuid import getnode as get_mac
from shapely.geometry import Point

import hunter.peripherals.uwb.uart as uwb
import hunter.utils as utils
# using MAC address as 48bit integer to keep logs unique across devices
mac = get_mac()
logging.basicConfig(filename='/home/pi/ghosthunt/ghosthunter/SEEK-{}.log'.format(mac),
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
    # Commands sent TO Micro:Bit
    OUT_SEPARATOR = "::"
    # Message FROM Micro:Bit
    IN_SEPARATOR = ";;"
    # Pi command channel for telling microbit to do things
    command_channel = '$'
    # Return channel for returning results of microbit requests
    return_channel = '}'

    uwb_serial_address = '/dev/ttyACM0'
    uwb_serial = None
    # The position from the last reading
    current_pos = None
    # previous position object received from DWM board
    # used to look for radio timeouts
    last_pos = None
    # UWB returns last seen, we need to stop it detecting
    # 'ghost' (pun intended) signals from radios no longer there
    pos_exact_matches = 0
    # tolerance (in mm) to ignore so that we don't mistake
    # fluctuation in uwb readings for hunter movement
    uwb_tolerance = 100
    # These are shapely geometries of things the device can detect
    # dict of lists split by level/room, updated by server as hunt develops
    # Room ids: 0 = Porter's MEss
    # 1 = downstairs fire escape
    # 2 = Outside Member's Bar
    # 3 = LAB test
    detectable_things = {
        0: [{'id': 0,
             'name': 'Inside Door near stairs',
             'geometry': Point(1498, 487),
             },
            {'id': 1,
             'name': 'step 1',
             'geometry': Point(2087, 1291),
             },
            {'id': 2,
             'name': 'step 2',
             'geometry': Point(3332, 1834),
             },
            {'id': 3,
             'name': 'step 3',
             'geometry': Point(2576, 3070),
             },
            {'id': 4,
             'name': 'step 4',
             'geometry': Point(2382, 4155),
             },
            {'id': 5,
             'name': 'step 5',
             'geometry': Point(931, 4727),
             },

            ],
        1: [
            {'id': 0,
             'name': 'Outside Door',
             'geometry': Point(-200, 1090),
             },

            {'id': 1,
             'name': 'Inside Door',
             'geometry': Point(1080, 1350),
             },
            {'id': 2,
             'name': 'Room 1',
             'geometry': Point(2310, 2870),
             },
            {'id': 3,
             'name': 'Lamp',
             'geometry': Point(2300, 6180),
             },
        ],
        2: [
            {'id': 1,
             'name': 'step 1',
             'geometry': Point(537, 3741),
             },
            # {'id': 2,
            # 'name': 'step 2',
            # 'geometry': Point(997, 2857),
            # },
            {'id': 3,
             'name': 'step 3',
             'geometry': Point(1107, 2022),
             },
            {'id': 4,
             'name': 'step 4',
             'geometry': Point(744, 1829),
             },
            # {'id': 5,
            # 'name': 'step 5',
            # 'geometry': Point(674, 962),
            # },

        ],
        3: [
            {'id': 1,
             'name': 'step 1',
             'geometry': Point(1150, 407),
             },
            {'id': 2,
             'name': 'step 2',
             'geometry': Point(3267, 1735),
             },
        ]

    }
    initiators = {
        33157: {
            'name': 'Porters mess door ID 8185',
            'room': 0,
        },
        49591: {
            'name': 'Members bar above cable port',
            'room': 2,
        },
        20625: {
            'name': 'Lab',
            'room': 3,
        },

    }
    # These are ids of anchors serving as beacons for detection
    # DB92 = 56210
    detectable_anchors = {
        33157: {
            'name': 'Porters mess door ID 8185',
            'initiator': 0,
        },
        49591: {
            'name': 'Members bar above cable port',
            'room': 2,
        },
        56210: {
            'name': 'GMeter Test 1'
        },
        20625: {
            'name': 'GMeter Test 1'
        },
        51744: {
            'name': 'CA20'
        },
        22801: {
            'name': '5911'
        }
    }

    # Current level - in scratch this will be the room we're in
    current_level = 0

    # Is the main loop on?
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
        'device': 'G',
        "device_range": 5000,
    }

    # Ectoscope
    ectoscope_settings = {
        # Detection range (in mm)
        'device': 'E',
        "device_range": 1000,
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
            while self.running:
                try:

                    # message from microbit
                    microbit_message = self.microbit_read()
                    if microbit_message is not None:
                        # pdb.set_trace()
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
        (code, value) = msg.split(self.IN_SEPARATOR)
        result = None
        if code == self.microbit_device_codes['radar']:
            result = self.ghost_scan()
        elif code == self.microbit_device_codes['ectoscope']:
            result = self.ecto_scan()
        elif code == self.microbit_device_codes['telegraph']:
            result = self.telegraph_transmit()
        return result

    async def log_position(self):
        """ Get the uwb position if it can and log it"""
        while self.running is True:
            # Get uwb position
            # if it's not empty
            # have we got an xy for the room? log it
            # are we near any points of interest? log it
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
        print("\n{}".format(return_type))
        # Flush for safety
        first_conn.flush()
        first_conn.reset_input_buffer()
        first_conn.reset_output_buffer()
        # second_conn.reset_output_buffer()
        # second_conn.reset_input_buffer()
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
            self.uwb_serial.flush()
            self.uwb_serial.close()
        if self.microbit_serial is not None:
            self.microbit_serial.flush()
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

    def microbit_write(self, message='0', channel=return_channel, delay=0.1):
        """
        Send a message to the Micro:bit in the format
        code:separator:message:\n
        :type message:str
        :type code:bytes        
        :param message:
        :para, delay: wait before sending results (see note below)
        :return:
        """

        if self.microbit_serial.is_open:
            msg = bytes(message + channel, 'utf-8')
            logging.debug("To microbit: {}".format(msg))
            # pdb.set_trace()
            """ 
            Added this because returning results 'too fast'
            seems to break the micro:bit. Not sure why yet.
            """
            # time.sleep(delay)
            self.microbit_serial.write(msg)
        else:
            logging.warning(
                'Trying to send microbit msg over closed uart {}'.format(
                    message
                ))

    def microbit_reset(self):
        """Send a reset command to the attached micro:bit"""
        self.microbit_write(
            'reset' + self.OUT_SEPARATOR,
            self.command_channel
        )

    def microbit_showstring(self, text):
        """Send a command to the attached micro:bit to show a string"""
        self.microbit_write(
            'text' + self.OUT_SEPARATOR + text,
            self.command_channel
        )

    """ **************  Hunting functions *********************   """

    def scan(self, settings):
        """ Scan function used for both radar and ectoscope
        :return int 0-10 proximity to something
        """
        # pdb.set_trace()
        pos = self.current_pos
        proximity = 0
        if pos and self.last_pos != pos:
            # Compare current position in a 360 circle, see if intersects
            # with any phenomena
            detected_things = self.detect_things(
                pos,
                settings['device_range'],
                settings['device'],
            )
            if len(detected_things) > 0:
                # Something found, display proximity to nearest thing
                thing = detected_things[0]
                full_proximity = (1 - thing['distance'] / settings[
                    'device_range']) * 10
                if full_proximity > 0 and full_proximity < 1:
                    proximity = 1
                else:
                    proximity = math.floor(full_proximity)
        # return not found value to microbit                
        self.microbit_write(str(proximity))
        self.last_pos = pos
        return proximity

    def ghost_scan(self):
        """ Ghost radar scan"""
        logging.debug("Ghost radar scanning...")
        return self.scan(self.radar_settings)

    def ecto_scan(self):
        """ Ecto scan """
        logging.debug("Ecto scan...")
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

    #   UWB Functions

    async def get_position(self):
        """ Query the uwb board for a position every second"""
        logging.debug("Starting uwb position loop")
        while self.running:
            self.current_pos = uwb.dwm_serial_get_loc(self.uwb_serial)
            await asyncio.sleep(1)
        logging.debug("Stopped uwb position loop")
        return True

    def uwb_reset(self):
        """ Send a reset command to the DWM board"""
        uwb.dwm_reset(self.uwb_serial)

    def detect_things(self, pos, device_range, device):
        """
        Use shapely to find 'detectable' objects
        :param level: to separate storeys of a building, or rooms
        :return: features found, None if nothing found
        """
        detected_things = list()
        # get pos and anchors
        anchors = pos['anchors']
        x = pos['position']['x']
        y = pos['position']['y']
        room = -1

        # First are any visible anchors in our detect list?
        for anchor_id in anchors.keys():
            if anchor_id in self.initiators:
                initiator = self.initiators[anchor_id]
                room = initiator['room']
            if device == 'G':
                # G Meter
                if anchor_id in self.detectable_anchors:
                    anchor = anchors[anchor_id]
                    # are they in range?
                    logging.debug('Anchor detected {}'.format(anchor))
                    if device_range >= anchor['distance']:
                        detected_things.append(anchor)

        # todo Are we on a grid?
        if pos and self.detectable_things and room >= 0:

            # Make a point from current coordinates, buffer it
            detection_zone = Point(
                float(x), float(y)).buffer(device_range)
            # Get all detectable features for this level
            for thing in self.detectable_things[room]:
                if detection_zone.intersects(thing['geometry']):
                    detected_thing = thing
                    # distance between point of detection and player
                    detected_thing['distance'] = Point(
                        x, y).distance(thing['geometry'])
                    detected_things.append(detected_thing)
        # sort by nearest
        detected_things = sorted(detected_things, key=itemgetter('distance'))
        return detected_things


def main():
    #######     Startup            #########

    hunter = GhostHunter()
    # hunter.uwb_serial_address = '/dev/tty.usbmodem1451'
    # hunter.microbit_serial_address = '/dev/tty.usbmodem1442'
    startup_result = "R"
    # Test and open serials
    hunter.init_serial_connections()
    if hunter.uwb_serial is not None:
        hunter.uwb_serial.write(uwb.DWM_LOC_GET_MSG)
        time.sleep(0.3)
        (return_byte, response_length, error_code) = hunter.uwb_serial.read(3)
        
        if (error_code == 0):
            logging.debug('UWB responding')
            hunter.uwb_serial.flush()
        else:
            #pdb.set_trace()    
            if error_code < 4:
                logging.warning('UWB NOT responding! error code {}'.format(uwb.DWM_ERROR_CODES[error_code]))
                # uh oh UWB isn't responding
                startup_result = "U"
            elif error_code == 4:
                logging.warning("UWB busy, waiting to retry...")
                time.sleep(3)
                hunter.uwb_serial.write(uwb.DWM_LOC_GET_MSG)
                time.sleep(0.3)
                (return_byte, response_length, error_code) = hunter.uwb_serial.read(3)
                if error_code !=0:
                    logging.warning('UWB NOT responding! error code {}'.format(uwb.DWM_ERROR_CODES[error_code]))


    #    
    if hunter.microbit_serial is not None:
        hunter.microbit_reset()
        time.sleep(2)
        hunter.microbit_showstring(startup_result)

    ####### Main command loop     #######
    hunter.running = True
    loop = asyncio.get_event_loop()
    # with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    try:
        loop.run_until_complete(asyncio.gather(
            hunter.main_device_loop(),
            hunter.get_position(),
        ))
    except KeyboardInterrupt:
        print('Interrupt called')
        hunter.running = False
    finally:
        # close serial
        hunter.uwb_reset()
        hunter.microbit_reset()
        time.sleep(2)
        hunter.close_serial_connections()

    #####     finish      #############

    # close logs


if __name__ == '__main__':
    main()
