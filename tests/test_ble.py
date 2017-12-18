import asyncio
import unittest
import warnings
from unittest.mock import patch
import asynctest
from hunter.ble import HunterBLE
import concurrent.futures

class HunterBleTest(unittest.TestCase):

    def setUp(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)
        self.hunter = HunterBLE(loop, executor)

    @patch('hunter.ble.Scanner')
    def test_get_ble_devices(self, scan_mock):
        result = self.hunter.ble_scan()
        scan_mock.assert_called()

