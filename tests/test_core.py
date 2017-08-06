import unittest
import unittest.mock as mock
import asyncio

from hunter.core import HunterRSSI
from local import SKIP_WEBSOCKET


class HunterRSSITest(unittest.TestCase):

    def setUp(self):
        context = {}
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(None)
        self.hunter = HunterRSSI(context)

    @unittest.skipIf(SKIP_WEBSOCKET, 'Skipping websocket calls to the fingerprint server')
    def test_update_fingerprint_database(self):
        # Query fingerprint db
        # match its format against our mock
        with mock.patch('hunter.core.HunterRSSI.update_fingerprint_database') as mock_update_fingerprint:
            pass
        pass

    @unittest.skipIf(SKIP_WEBSOCKET, 'Skipping websocket calls to the hunt server')
    def test_getwebsocket(self):
        pass

    @mock.patch('hunter.core.HunterRSSI.update_fingerprint_database')
    @mock.patch('hunter.core.HunterRSSI.getwebsocket')
    def test_bootup(self, MockUpdateFingerprints, Mockgetwebsocket):
        MockUpdateFingerprints.return_value = True
        Mockgetwebsocket.return_value = True
        self.loop.run_until_complete(self.hunter.bootup())
        self.assertEqual(self.hunter.device_ready, True)

    # shutdown



    # async def listen_server(self):

    # def hunt_begin(self):

    # def hunt_ended(self):

    # async def get_ble_devices(self):