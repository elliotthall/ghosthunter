import asyncio
import concurrent.futures
import unittest
from unittest.mock import patch

from hunter.ble import HunterBLE


class HunterBleTest(unittest.TestCase):
    def setUp(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)
        self.hunter = HunterBLE(loop, executor)

    @patch('hunter.ble.Scanner.scan', autospec=True)
    def test_get_ble_devices(self, scan_mock):
        self.hunter.ble_scan()
        scan_mock.assert_called_with(self.hunter.ble_scan_length)

    # def test_get_ble_devices(self):


    def test_extra_device_functions(self):
        extras = self.hunter.extra_device_functions()
        self.assertEqual(self.hunter.bluetooth_scan in extras, True)

#
# async def bluetooth_scan(self):
