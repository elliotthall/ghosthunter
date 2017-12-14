import unittest
import unittest.mock as mock
from hunter.core import Hunter
import asynctest
import asyncio
import warnings


class Hunter_test(unittest.TestCase):
    def setUp(self):
        loop = asyncio.get_event_loop()
        self.hunter = Hunter(loop)

    def test_shutdown(self):
        self.hunter.stop()
        result =  self.hunter.shutdown()
        self.assertEqual(result, True)
        self.assertEqual(self.hunter.event_loop.is_closed(), True)

    def test_boootup(self):
        mock_server_config = asynctest.CoroutineMock(return_value=True)
        mock_return_none = asynctest.CoroutineMock(return_value=None)
        self.hunter.server_config = mock_server_config
        self.hunter.get_server_messages = mock_return_none
        self.hunter.get_device_input = mock_return_none
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result = self.hunter.bootup(run_forever=False)
        self.assertEqual(result, True)
        mock_server_config.assert_called_once()
        self.hunter.stop()
        self.hunter.shutdown()


    def test_trigger(self):
        result = self.hunter.event_loop.run_until_complete(self.hunter.trigger())
        self.assertEqual(result, True)
        self.assertEqual(self.hunter.device_ready, True)



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
