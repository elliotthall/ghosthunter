""" Specific ghost detectors derived from the core library.
These devices are what the student will select and use."""
import asyncio
import logging
import math
from concurrent.futures import CancelledError
from operator import itemgetter
from shapely.geometry import Point

import hunter.core as hunter_core


class ProximityDevice(hunter_core.HunterUwbMicrobit):
    """Ping-type radar detection.
    Short range(?), 360 degree FOV
    Detect anomalies and use micro:bit LEDs to display
    their rough proximity in a hotter/colder fashion"""
    # Device detection range (in cm)
    device_range = 500

    trigger_animation = ("00000:00000:00300:00000:00000,"
                         + "00000:07770:07070:07770:00000,"
                         + "99999:90009:90009:90009:99999")

    def detect_things(self, x, y, level=0):
        """
        Use shapely to find 'detectable' objects
        :param level: to separate storeys of a building, or rooms
        :return: features found, None if nothing found
        """
        detected_things = list()
        if self.uwb_pos and self.detectable_things:
            # Make a point from current coordinates, buffer it
            detection_zone = Point(x, y).buffer(self.device_range)
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
    def thing_found(self, x, y, detected_thing):
        """
        Display that a thing has been found using Micro:bit
        - log thing found in hunt log
        :param x: x pos at time of detection
        :param y: y pos at time of detection
        :param detected_thing: thing detected
        :return: true when done
        """

        # create microbit detection animation based on distance
        leds = int(math.ceil(1 - (detected_thing['distance'] / self.device_range) * 25))
        # send to microbit for display
        # todo make this COOLER
        canvas = [['0'] * 5 for x in range(0, 5)]
        for x in range(0, leds):
            row = int(math.floor(x / 5))
            canvas[row][x - row * 5] = '9'
        image = ""
        for y in range(0, 5):
            image += "".join(canvas[y])
            if y != 4:
                image += ":"
        self.microbit_write(self.MICROBIT_CODES['image'], image)
        return True

    async def trigger(self):
        """ Time device 'cooldown' after detection attempt """
        logging.info("triggering...")
        # todo Trigger animation?
        # todo Fresh get pos here?
        pos = self.uwb_pos
        if pos:
            # Compare current position in a 360 circle, see if intersects with any phenomena
            detected_things = self.detect_things(
                pos['position']['x'],
                pos['position']['y'],
                self.current_level
            )
            if len(detected_things) > 0:
                # Something found, display proximity to nearest thing
                self.thing_found(detected_things[0])
        await asyncio.sleep(self.device_interval)
        self.device_ready = True
        logging.info("Recharged and ready")
        return True

    async def execute_commands(self):
        """
        """
        try:
            while True:
                try:
                    # Are there waiting commands?
                    if len(self.command_queue) > 0:
                        # Parse commands
                        if self.COMMAND_SHUTDOWN in self.command_queue:
                            break
                        elif self.COMMAND_TRIGGER in self.command_queue:
                            self.command_queue.remove(self.COMMAND_TRIGGER)
                            self.trigger()
                    await asyncio.sleep(0.1)
                except CancelledError:
                    logging.debug("execute_commands cancelled")
                    break
        finally:
            logging.debug("Stopping main loop")
        self.cancel_events()
        return True
