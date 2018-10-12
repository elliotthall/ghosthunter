""" Specific ghost detectors derived from the core library.
These devices are what the student will select and use."""
import logging
import math
import random
from operator import itemgetter
import pdb

from shapely.geometry import Point

import hunter.core as hunter_core

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


class MainDevice(object):
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
    # These are shapely geometries of things the device can detect
    # dict of lists split by level/room, updated by server as hunt develops
    detectable_things = None
    # Current level - in scratch this will be the room we're in
    current_level = 0

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

     # devices specifc codes for doing hunt work
    microbit_device_codes = {
        'radar': 'G',
        'ectoscope': 'E',
        'telegraph': 'T',
        'spiritsign': 'S'
        #'radio': b'\xa4',
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
        'signs':{
            # empty sign for convenience of making real ones
            "90000:00000:00000:00000:00000":"Test",
            "90009:00000:00000:00000:90009": "BOO!"
        }
    }

    # paranormalradio_settings = {
    #
    # }

    # Use diagnostics rather than attempt to get live data
    DEBUG_MODE = False

    trigger_animation = ("00000:00000:00300:00000:00000," +
                         "00000:07770:07070:07770:00000," +
                         "99999:90009:90009:90009:99999")



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

    def device_startup_tasks(self):
        """1. Connect UART to micro:bit and DWM1001-DEV
           2. Reset the micro:bit and DWM1001-DEV boards
           3. Confirm both boards are ready
           :return True if tasks successful
           """
        result = self.init_serial_connections()
        if not result:
            logging.error('UART connection failed!')
            return False
        else:
            self.uwb_reset()
            self.microbit_reset()
            # Give boards time to reset
            time.sleep(3)
            # Query boards
            try:
                micro_result = self.microbit_serial.readline()
                if self.MICROBIT_CODES['ready'] in micro_result:
                    # Microbit ready
                    logging.info('Micro:bit ready.')
                else:
                    logging.error('Micro:bit startup failed!')
                    return False
                uwb_cfg = uwb.dwm_serial_get_cfg(self.uwb_serial)
                try:
                    # UWB confirm we got a config back and it's correct
                    # todo add further config tests
                    if 'tag' in uwb_cfg['mode']:
                        logging.info('DWM1001-DEV ready.')
                except IndexError:
                    logging.error('Getting uwb config on startup failed!')
                    return False
                # All done, return we are ready
                return True
            except asyncio.TimeoutError:
                logging.error('Peripheral startup timed out!')
                return False




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


    def hunt(self):
        """ Parse the micro:bit message and use the relevant function
        to return output

        'radar': b'\x30',
        'ectoscope': b'\x31',
        'telegraph': b'\x32',
        'spiritsign': b'\x33',
        'radio': b'\x34',
        """
        command = self.command_queue[self.COMMAND_HUNT]
        code = command[0:1]
        value = str(command[2:-1], 'UTF-8')
        result = None
        if code == self.microbit_device_codes['radar']:
            result = self.ghost_scan()
        elif code == self.microbit_device_codes['ectoscope']:
            result = self.ecto_scan()
        elif code == self.microbit_device_codes['telegraph']:
            result = self.telegraph_transmit(value)
        elif code == self.microbit_device_codes['spiritsign']:
            result = self.decode_spiritsign(value)
        if result is not None:            
            self.microbit_write(result[0], result[1])
        del self.command_queue[self.COMMAND_HUNT]
        self.device_ready = True

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

    def parse_microbit_serial_message(self, message):
        """Parse any messages from microbit and
        add to command queue as necesssary

        :param message: line from micro:bit in bytes
        :return command from message, if present
        """
        command = None
        # '{}::{}\n'        
        #code = message[0:1]
        #value = str(message[2:-1], 'UTF-8')        
        msg = str(message, 'UTF-8')
        code =  msg[0]  
        pdb.set_trace()
        if code in self.microbit_device_codes.values():
            self.command_queue[self.COMMAND_HUNT] = message            
        
        return command

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
                translation =  self.spiritsign_settings['signs'][sign]
            else:
                # bad sign
                translation = '?'
        return [self.MICROBIT_CODES['data'], translation]

    def tune_radio(self,msg):
        """ ?"""
        if self.DEBUG_MODE:
            return "00000:09000:90909:00090:00000"
