"""
Test package for specific hunter devices.  Proximity only so far.
"""
import asyncio
import unittest

from shapely.geometry import Point

import hunter.devices as devices


class ProximityDevice_test(unittest.TestCase):

    def setUp(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.hunter = devices.ProximityDevice(loop)
        self.hunter.uwb_pos = {
            'position': {
                'x': 0.0,
                'y': 0.0,
                'z': 0.0,
                'qf': 100,
            }
        }

    def tearDown(self):
        if not asyncio.get_event_loop().is_closed():
            asyncio.get_event_loop().close()

    def test_thing_found(self):
        pass

    def test_detect_things(self):
        detected_things = self.hunter.detect_things(
            self.hunter.uwb_pos['position']['x'],
            self.hunter.uwb_pos['position']['y'])
        # deal with nothing in detectable things
        self.assertEqual(len(detected_things), 0)

        self.hunter.detectable_things = {
            0: [
                {'id': 0,
                 'geometry': Point(300, 0),
                 'level': 0}
            ]
        }        
        detected_things = self.hunter.detect_things(
            self.hunter.uwb_pos['position']['x'],
            self.hunter.uwb_pos['position']['y'])
        # found at least one thing
        self.assertGreaterEqual(len(detected_things), 1)
        # thing found has id 0
        self.assertEqual(detected_things[0]['id'], 0)
        # one point too far away
        self.hunter.detectable_things[0][0]['geometry'] = Point(600, 0)
        detected_things = self.hunter.detect_things(
            self.hunter.uwb_pos['position']['x'],
            self.hunter.uwb_pos['position']['y'])
        self.assertEqual(len(detected_things), 0)
        self.hunter.detectable_things[0][0]['geometry'] = Point(300, 0)
        self.hunter.detectable_things[0].append(
            {'id': 1,
             'geometry': Point(400, 0),
             'level': 0}
        )

        # two valid points, make sure nearest is returned first
        detected_things = self.hunter.detect_things(
            self.hunter.uwb_pos['position']['x'],
            self.hunter.uwb_pos['position']['y'])
        self.assertGreaterEqual(len(detected_things), 2)
        hunter_position = Point(
            self.hunter.uwb_pos['position']['x'],
            self.hunter.uwb_pos['position']['y']
        )
        self.assertEqual(hunter_position.distance(detected_things[0]['geometry']),
                         300
                         )

        # shapes?

        # def detect_things(self, x, y, level=0):
        # async def trigger(self):?
