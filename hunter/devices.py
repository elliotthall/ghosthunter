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


class MainDevice(hunter_core.HunterUwbMicrobit):
    """ This class contains all the various hunter detector
     functions, merged together for ease of deployment """

     # devices specifc codes for doing hunt work
    microbit_device_codes = {
        'radar': b'\xa0',
        'ectoscope': b'\xa1',
        'telegraph': b'\xa2',
        'spiritsign': b'\xa3',
        'radio': b'\xa4',
    }

    """ variable settings for all devices """

    # Ghost Radar
    radar_settings = {
        # Detection range (in mm)
        "device_range": 5000
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
            "00000:00000:00000:00000:00000":"Test",
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

    def extra_device_functions(self):
        """ Add microbit, uwb listeners to loop"""
        # todo overriden to temporarily remove ble
        return [
            self.microbit_listen(),
            self.uwb_get_pos()
        ]

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
        leds = int(
            math.ceil(
                (1 - (detected_thing['distance'] / settings['device_range'])) * 25
            )
        )
        if leds == 0:
            # minimum reading of one
            leds = 1
        # send to microbit for display
        # todo Send result not image
        canvas = [['0'] * 5 for x in range(0, 5)]
        for x in range(0, leds):
            row = int(math.floor(x / 5))
            canvas[row][x - row * 5] = '9'
        # no delay
        image = "0;;"
        for y in range(0, 5):
            image += "".join(canvas[y])
            if y != 4:
                image += ":"
        logging.info(
            "Thing found, nearest: id {} at {}cm away, {} leds".format(
                detected_thing['id'],
                detected_thing['distance'],
                leds
            )
        )
        return [self.MICROBIT_CODES['image'], image]


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
        elif code == self.microbit_device_codes['radio']:
            result = self.tune_radio(value)
        if result is not None:            
            self.microbit_write(result[0], result[1])

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
        return False

    def parse_microbit_serial_message(self, message):
        """Parse any messages from microbit and
        add to command queue as necesssary

        :param message: line from micro:bit in bytes
        :return command from message, if present
        """
        command = None
        # '{}::{}\n'        
        code = message[0:1]
        value = str(message[2:-1], 'UTF-8')        
        if code in self.microbit_device_codes.values():
            self.command_queue[self.COMMAND_HUNT] = message            
        """
        if code == self.MICROBIT_CODES['input']:
            if int(value) == self.BUTTON_A:
                # Button a pressed
                command = self.COMMAND_HUNT
            if int(value) == self.BUTTON_B:
                command = self.COMMAND_SHUTDOWN
        elif code == self.MICROBIT_CODES['acc']:
            # todo do something with accelerometer data
            pass
        """
        #if command:
        #    self.command_queue[command] = value
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
