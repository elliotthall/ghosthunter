import asyncio
import unittest
import warnings
import asynctest
from hunter.ble import HunterBLE
import concurrent.futures

class HunterBleTest(unittest.TestCase):

    def setUp(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)
        self.hunter = HunterBLE(loop, executor)

    def test_get_ble_devices(self):
        mock_return_none = asynctest.CoroutineMock(return_value=None)
        with asynctest.patch('scanner.scan', new=mock_return_none):
            result = self.hunter.ble_scan()
            self.assertEqual(result, None)
