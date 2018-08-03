import asyncio
import unittest
import warnings

import asynctest

from hunter.core import Hunter


async def command_queue(hunter, commands, delay=0.5):
    """ Feed the executor commands to test it"""
    try:
        for command in commands:
            hunter.command_queue.append(command)
            await asyncio.sleep(delay)
    except asyncio.CancelledError:
        pass
    return True




def finish(future):
    print(future.result())
    asyncio.get_event_loop().stop()


class Hunter_test(unittest.TestCase):
    def setUp(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.hunter = Hunter(loop)

    def tearDown(self):
        if not asyncio.get_event_loop().is_closed():
            asyncio.get_event_loop().close()

    def test_shutdown(self):
        self.hunter.cancel_events()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result = self.hunter.shutdown()
        self.assertEqual(result, True)
        self.assertEqual(self.hunter.event_loop.is_running(), False)

    def test_bootup(self):
        mock_server_config = asynctest.CoroutineMock(return_value=True)
        mock_return_none = asynctest.CoroutineMock(return_value=None)
        self.hunter.server_config = mock_server_config
        self.hunter.get_server_messages = mock_return_none
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result = self.hunter.bootup(run_forever=False)
        self.assertEqual(result, True)
        mock_server_config.assert_called_with()

    def test_trigger(self):
        result = self.hunter.event_loop.run_until_complete(self.hunter.hunt())
        self.assertEqual(result, True)
        self.assertEqual(self.hunter.device_ready, True)

    def test_get_ghost_server_socket(self):
        mock_return_none = asynctest.CoroutineMock(return_value=None)
        with asynctest.patch('websockets.connect', new=mock_return_none):
            result = self.hunter.event_loop.run_until_complete(self.hunter.get_ghost_server_socket())
        self.assertEqual(result, None)

    def test_stop(self):
        self.hunter.cancel_events()
        # Verify all tasks are cancelled
        for task in asyncio.Task.all_tasks():
            self.assertEqual(task.cancelled(), True)

    def test_execute_commands(self):
        commands = [self.hunter.COMMAND_HUNT, self.hunter.COMMAND_SHUTDOWN]
        mock_trigger = asynctest.CoroutineMock(return_value=True)
        self.hunter.hunt = mock_trigger
        asyncio.ensure_future(command_queue(self.hunter, commands))
        execute_task = asyncio.ensure_future(self.hunter.execute_commands())
        execute_task.add_done_callback(finish)
        self.hunter.event_loop.run_forever()
        mock_trigger.assert_called_with()

    def test_parse_server_message(self):
        self.hunter.parse_server_message(self.hunter.MESSAGE_SHUTDOWN)
        self.assertEqual(self.hunter.COMMAND_SHUTDOWN in self.hunter.command_queue, True)

    def test_get_server_messages(self):
        mock_websocket = asynctest.CoroutineMock()
        mock_websocket.recv = asynctest.CoroutineMock(return_value=self.hunter.MESSAGE_SHUTDOWN)
        self.hunter.websocket = mock_websocket
        try:
            self.hunter.event_loop.run_until_complete(asyncio.gather(
                self.hunter.get_server_messages(),
                self.hunter.execute_commands()))
        except asyncio.CancelledError:
            pass
        mock_websocket.recv.assert_called_with()

    def test_send_server_messages(self):
        mock_websocket = asynctest.CoroutineMock()
        mock_websocket.send = asynctest.CoroutineMock(side_effect=asyncio.TimeoutError)
        self.hunter.websocket = mock_websocket
        try:
            self.hunter.event_loop.run_until_complete(asyncio.gather(
                self.hunter.send_server_message('PING'),
            ))
        except asyncio.CancelledError:
            pass
        mock_websocket.send.assert_called_with('PING')



        # server_config



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
