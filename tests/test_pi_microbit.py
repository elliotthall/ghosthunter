import asyncio
import concurrent.futures
import unittest
from unittest.mock import patch
from bluepy.btle import ScanEntry
from hunter.pi_microbit import HunterMicrobit

class test_HunterMicrobit(unittest.TestCase):

    def setUp(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)
        self.hunter = HunterMicrobit(loop, self.executor)

    def tearDown(self):
        self.executor.shutdown()
        if not asyncio.get_event_loop().is_closed():
            asyncio.get_event_loop().close()

    def test_send_serial_message(self):
        pass

    #     def parse_microbit_serial_message(self, message):
    #         async def receive_serial_message(self):
