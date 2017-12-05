import unittest
import unittest.mock as mock
import asyncio
import asynctest
from hunter.core import Hunter
from local import SKIP_WEBSOCKET

class Hunter(unittest.TestCase):
    def setUp(self):
        self.hunter = Hunter()

    def tearDown(self):
        self.hunter.shutdown()

    @mock.patch('hunter.core.Hunter.server_config', returns=True)
    def test_boootup(self):
        result = self.hunter.bootup(run_forever=False)
        self.assertEqual(result, True)

# class HunterRSSITest(unittest.TestCase):
#
#     def setUp(self):
#         context = {}
#         self.loop = asyncio.new_event_loop()
#         asyncio.set_event_loop(None)
#         self.hunter = HunterRSSI(context)
#         self.hunt_response={
#
#         }
#
#     def tearDown(self):
#         self.loop.close()
#
#     @unittest.skipIf(SKIP_WEBSOCKET, 'Skipping websocket calls to the fingerprint server')
#     def test_update_fingerprint_database(self):
#         # Query fingerprint db
#         # match its format against our mock
#         with mock.patch('hunter.core.HunterRSSI.update_fingerprint_database') as mock_update_fingerprint:
#             pass
#         pass
#
#     @unittest.skipIf(SKIP_WEBSOCKET, 'Skipping websocket calls to the hunt server')
#     def test_getwebsocket(self):
#         pass
#
#
#     @mock.patch('hunter.core.HunterRSSI.getwebsocket')
#     def test_bootup(self, Mockgetwebsocket):
#         Mockgetwebsocket.return_value = True
#         #self.loop.run_until_complete(self.hunter.bootup())
#         self.hunter.bootup(self.loop)
#         self.assertEqual(self.hunter.device_ready, True)


    # shutdown



    # async def listen_server(self):

    # def hunt_begin(self):

    # def hunt_ended(self):

    # async def get_ble_devices(self):

if __name__ == '__main__':
    unittest.main()