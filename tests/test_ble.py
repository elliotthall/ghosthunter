import asyncio
import concurrent.futures
import unittest
from unittest.mock import patch

from bluepy.btle import ScanEntry

from hunter.ble import HunterBLE
from .test_core import stop_loop


def get_mock_scan_entries():
    mock_entry_good = unittest.mock.create_autospec(ScanEntry)
    mock_entry_good.addr = 'MAC'
    mock_entry_good.rssi = -1
    mock_entry_good.getScanData.return_value = [('1', "Local Name", HunterBLE.ble_name_prefix)]
    mock_entry_bad = unittest.mock.create_autospec(ScanEntry)
    mock_entry_bad.addr = 'MAC'
    mock_entry_bad.rssi = -1
    mock_entry_bad.getScanData.return_value = [('1', "Local Name", 'Filter me out')]
    mock_entries = [mock_entry_good, mock_entry_bad]
    return mock_entries

def finish(future):
    print(future.result())
    asyncio.get_event_loop().stop()

class HunterBleTest(unittest.TestCase):
    def setUp(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)
        self.hunter = HunterBLE(loop, executor)

    @patch('hunter.ble.Scanner.scan')
    def test_get_ble_scan(self, scan_mock):
        self.hunter.ble_scan()
        scan_mock.assert_called_with(self.hunter.ble_scan_length)

    def test_get_ble_devices(self):
        mock_entries = get_mock_scan_entries()
        result = self.hunter.get_ble_devices(mock_entries)
        self.assertEqual(len(result), 1)
        good_entry = result[0]
        self.assertEqual(good_entry['MAC'], 'MAC')
        self.assertEqual(good_entry['Name'], self.hunter.ble_name_prefix)
        self.assertEqual(good_entry['RSSI'], -1)

    @patch('hunter.ble.Scanner.scan')
    @patch('hunter.ble.HunterBLE.get_ble_devices')
    def test_bluetooth_scan(self, mock_scan, mock_ble_devices):
        asyncio.ensure_future(stop_loop(self.hunter))
        asyncio.ensure_future(self.hunter.bluetooth_scan())
        mock_ble_devices.return_value = [{'MAC': 'MAC',
                                         "Name": 'Kontakt', "RSSI": -1}]
        self.hunter.event_loop.run_until_complete(asyncio.gather(
            stop_loop(self.hunter)
        ))



        # def test_extra_device_functions(self):
        #     extras = self.hunter.extra_device_functions()
        #     self.assertListEqual([self.hunter.bluetooth_scan()], extras)

        #
        # async def bluetooth_scan(self):
