import asyncio
import concurrent.futures
import unittest
from unittest.mock import patch
from bluepy.btle import ScanEntry
from hunter.ble import HunterBLE


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
        mock_entry = unittest.mock.create_autospec(ScanEntry)
        mock_entry.addr='MAC'
        mock_entry.rssi = -1
        mock_entry.getScanData.return_value = [('1', "Local Name", self.hunter.ble_name_prefix)]
        mock_entries = [mock_entry]
        import pdb; pdb.set_trace()
        result = self.hunter.get_ble_devices(mock_entries)
        self.assertEqual(len(result),len(mock_entries))


    # def test_extra_device_functions(self):
    #     extras = self.hunter.extra_device_functions()
    #     self.assertListEqual([self.hunter.bluetooth_scan()], extras)

#
# async def bluetooth_scan(self):
