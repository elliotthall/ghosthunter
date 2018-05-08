"""
Hunter core library classes

All hunter devices should be derived from these objects.


"""
import asyncio
import functools
import logging
import time
from concurrent.futures import CancelledError

import websockets

import hunter.peripherals.microbit.utils as microbit_utils
import hunter.peripherals.uwb.uart as uwb
import hunter.utils as utils
from .ble import HunterBLE

# from bluepy.btle import Scanner

HUNT_BEGIN_MESSAGE = u'HUNT_BEGIN'
HUNT_END_MESSAGE = u'HUNT_END'
EVENT_UPDATE_MESSAGE_HEADER = u'available_events'
__author__ = 'elliotthall'


def stop_loop_callback(future):
    print(future.result())
    asyncio.get_event_loop().stop()


class HunterUwbMicrobit(HunterBLE):
    """
    Bluetooth Hunter using two interfaces over UART
        - attached Micro:Bit as an interface
        - DWM1001-DEV for internal positioning and ranging

    This class can:
        -Send/receive message to microbit over serial
        -Receive/send message from DWM1001-DEV
        -parse messages from both peripherials
    """
    microbit_serial_address = '/dev/ttyACM1'
    microbit_serial = None
    uwb_serial_address = '/dev/ttyACM0'
    uwb_serial = None

    def init_serial_connections(self):
        """Establish UART connections to UWB and Micro:bit
        Since addresses are assigned in the order deivces are connected
        Test to make sure """
        # Establish connections
        first_conn = utils.connect_serial(self.uwb_serial_address)
        second_conn = utils.connect_serial(self.microbit_serial_address)
        # Send an id message, verify this is a DWM
        first_conn.write(uwb.DWM_CFG_GET_MSG)
        return_type = first_conn.read()
        if return_type == uwb.DWM_RETURN_BYTE:
            # Yes, assign to uwb
            logging.debug('ACM0 assigned to uwb')
            self.uwb_serial = first_conn
            self.microbit_serial = second_conn
            # todo parse the cfg get and configure here?
        else:
            # No, asssign to micro:bit
            logging.debug('ACM1 assigned to uwb')
            self.microbit_serial = first_conn
            self.uwb_serial = second_conn
        return True

    def device_startup_tasks(self):
        """1. Connect UART to micro:bit and DWM1001-DEV
           2. Reset the micro:bit and DWM1001-DEV boards
           3. Confirm both boards are ready
           :return True if tasks successful
           """
        result = self.init_serial_connections()
        if not result:
            logging.error('UART connection failed!')
            return False
        else:
            self.reset_uwb()
            self.reset_microbit()
            # Give boards time to reset
            time.sleep(0.3)
            # Query boards
            # todo simplify?  Timeout?
            tasks = [
                self.event_loop.run_in_executor(
                    self.executor,
                    functools.partial(self.read_microbit_serial,
                                      self.microbit_serial,
                                      None)
                ),
                self.event_loop.run_in_executor(
                    self.executor,
                    functools.partial(uwb.dwm_serial_get_cfg,
                                      self.uwb_serial,
                                      None)
                )
            ]
            try:
                micro_result, uwb_cfg = self.event_loop.run_until_complete(
                    asyncio.wait_for(tasks,
                                     timeout=10,
                                     loop=self.event_loop
                                     )
                )
                if microbit_utils.MICROBIT_CODES['ready'] in micro_result:
                    # Microbit ready
                    logging.info('DWM1001-DEV ready.')
                else:
                    logging.error('Micro:bit startup failed!')
                    return False
                try:
                    # UWB confirm we got a config back and it's correct
                    # todo add further config tests
                    if 'tag' in uwb_cfg['mode']:
                        logging.info('DWM1001-DEV ready.')
                except IndexError:
                    logging.error('Getting uwb config on startup failed!')
                    return False
                # All done, return we are ready
                return True
            except asyncio.TimeoutError:
                logging.error('Peripheral startup timed out!')
                return False

    def reset_microbit(self):
        """Send a reset command to the attached micro:bit"""
        self.send_microbit_serial(self.microbit_serial,
                                  microbit_utils.MICROBIT_CODES['reset']
                                  )

    def reset_uwb(self):
        """ Send a reset command to the DWM board"""
        uwb.dwm_reset(self.uwb_serial)

    async def send_microbit_serial(self, serial_connection, message):
        if self.microbit_serial.is_open:
            return self.wrap_serial(serial_connection, message)
        else:
            logging.warning('Trying to send microbit msg over closed uart {}'.format(
                message
            ))

    async def wrap_serial(self, serial_connection, serial_function, message=None):
        """Wrap a command in a future
        used for uart communication
        :param serial_function: uart function
        :param serial_connection: uart connection for function
        :param message: message to send, none if receive
        """
        try:
            if message:
                future = self.event_loop.run_in_executor(
                    self.executor,
                    functools.partial(serial_function, serial_connection, message)
                )
            else:
                future = self.event_loop.run_in_executor(
                    self.executor,
                    functools.partial(serial_function, serial_connection)
                )
            return await asyncio.wait_for(future, 30, loop=self.event_loop)
        # except TypeError as e:
        #     logging.error("Bad microbit sent message: {}".format(e))
        except asyncio.TimeoutError:
            # check serial connection
            if serial_connection.is_open is False:
                # serial connection lost, try to reestablish
                serial_connection.open()

    def parse_microbit_serial_message(self, message):
        """Parse any messages from microbit and
        add to command queue as necesssary"""
        command = None
        # '{}::{}\n'
        if '{}::{}\n'.format(
                microbit_utils.MICROBIT_CODES['input'],
                microbit_utils.BUTTON_A
        ) in message:
            # Button a pressed
            command = self.COMMAND_TRIGGER
        self.command_queue.append(command)
        return command

    def read_microbit_serial(self):
        if self.microbit_serial.is_open:
            return self.wrap_serial(self.microbit_serial)
        else:
            logging.warning('Trying to read microbit msg over closed uart')

    async def receive_serial_message(self):
        """ Listen for JSON serial messages, pass to parser"""
        while True:
            try:
                future = self.event_loop.run_in_executor(
                    self.executor, self.read_microbit_serial)
                message = await asyncio.wait_for(
                    future, 30, loop=self.event_loop)
                logging.debug("Serial message received: {}".format(message))
                self.parse_microbit_serial_message(message)
            except asyncio.TimeoutError:
                # check serial connection
                if self.microbit_serial.is_open is False:
                    # serial connection lost, try to reestablish
                    self.connect_serial()

    def extra_device_functions(self):
        """ Add bluetooth scan to loop"""
        device_functions = super(HunterUwbMicrobit, self).extra_device_functions()
        device_functions.append(self.init_serial_connections())
        device_functions.append(self.receive_serial_message())
        return device_functions

    async def get_uwb_pos(self):
        # todo error trap
        self.wrap_serial(self.uwb_serial,
                         uwb.dwm_serial_get_loc
                         )


class Hunter(object):
    """
    Hunter

    The base class for all hunter devices.
    Runs a perpeutal event loop on the producer/consumer model.
    Commands are added to the command_queue from server messages or
    hardware input and consumed by device_specific functions
    in extra_device_functions.

    - Run perpetual event loop
    - Communicate with server via websockets
    - get input from device hardware

    """
    # This device's unique id
    uid = ''
    # uri for ghost hunt server
    hunt_url = ''

    # The main event loop for the device
    event_loop = None

    # The websocket for communication with the hunt server
    websocket = None
    # How long the device rests before ready to detect again (in seconds)
    device_interval = 0
    # Is the device ready to be triggered?
    devive_ready = False
    # Device commands that can be triggered
    COMMAND_SHUTDOWN = 'SHUTDOWN'
    COMMAND_TRIGGER = 'TRIGGER'

    # Shutdown message from server
    MESSAGE_SHUTDOWN = 'SHUTDOWN'

    # async events to run in loop
    event_queue = list()
    # Any commands received by socket, I/O e.g. trigger scan
    command_queue = list()

    def __init__(self, event_loop=None, **kwargs):
        if event_loop is None:
            self.event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.event_loop)
        else:
            self.event_loop = event_loop
        self.event_queue = [
            self.get_server_messages()
        ]
        # Add device specific functionality
        for command in self.extra_device_functions():
            self.event_queue.append(command)

    def device_startup_tasks(self):
        """ Override with device-specific startup tasks"""
        return True

    async def server_config(self):
        """ Establish server connection, get extra config if necessary"""
        await self.get_ghost_server_socket()
        # todo extra server vars?
        logging.info('Server config retrieved')
        return True

    async def get_ghost_server_socket(self):
        """ Instantiate connection to ghost server, or return if ready"""
        # todo add error trapping timeouts etc.
        websocket = await websockets.connect(self.hunt_url)
        return websocket

    def parse_server_message(self, message):
        """ Perform commands and modify variables based on server
        messages"""
        if self.MESSAGE_SHUTDOWN in message:
            self.command_queue.append(self.COMMAND_SHUTDOWN)
        return None

    async def get_server_messages(self):
        """ Retrieve any messages sent to device from server"""
        logging.debug("Get server messages...")
        while True:
            try:
                message = await asyncio.wait_for(
                    self.websocket.recv(), timeout=20)
                logging.debug(message)
                self.parse_server_message(message)
            except asyncio.TimeoutError:
                try:
                    pong_waiter = await self.websocket.ping()
                    await asyncio.wait_for(pong_waiter, timeout=10)
                except asyncio.TimeoutError:
                    # todo No response to ping in 10 seconds.  Attempt to
                    # reconnect
                    break
            except CancelledError:
                logging.debug("socket cancelled")
                break
        return None

    async def send_server_message(self, message):
        try:
            await self.websocket.send(message)
        except asyncio.TimeoutError:
            # todo reconnect attempt
            pass
        except CancelledError:
            # todo ensure last message attempt if cancelled during shutdown?
            print("send message cancelled")
        return None

    def extra_device_functions(self):
        """ Override with device-specific extra functions
        you want to add to the loop"""
        return list()

    def bootup(self, run_forever=True):
        """ Set up event loop and boot up"""
        logging.info("Starting up...")
        self.event_loop.run_until_complete(self.server_config())
        # device specific startup tasks e.g UART connections
        result = self.device_startup_tasks()
        if not result:
            logging.error("Device specific tasks failed!")
        for command in self.event_queue:
            asyncio.ensure_future(command)
        # Last, add the command parser
        execute_task = asyncio.ensure_future(
            self.execute_commands())
        execute_task.add_done_callback(stop_loop_callback)
        # start the main event loop
        self.device_ready = True
        if run_forever:
            self.event_loop.run_forever()
        return True

    def shutdown(self):
        """ Perform any final tasks such as logging before shutting down """
        logging.info("Shutting down...")
        # todo final report to server?
        logging.info("Closing websocket...")
        if self.websocket:
            self.event_loop.run_until_complete(self.websocket.close())
        self.event_loop.run_until_complete(
            asyncio.gather(*asyncio.Task.all_tasks()))
        return True

    async def trigger(self):
        """ Time device 'cooldown' after detection attempt """
        logging.info("triggering...")
        await asyncio.sleep(self.device_interval)
        self.device_ready = True
        logging.info("Recharged and ready")
        return True

    def cancel_events(self):
        for task in asyncio.Task.all_tasks():
            task.cancel()

    async def execute_commands(self):
        """ Main function to tell the hunter device to 'do something'
        based on notifications from bluetooth, user input, sockets etc.
        commands in while loop should be ordered by priority
        Should be overriden by device-sepecic functions
        """
        try:
            while True:
                try:
                    # Are there waiting commands?
                    if len(self.command_queue) > 0:
                        # Parse commands
                        if self.COMMAND_SHUTDOWN in self.command_queue:
                            break
                        elif self.COMMAND_TRIGGER in self.command_queue:
                            self.command_queue.remove(self.COMMAND_TRIGGER)
                            self.trigger()
                    await asyncio.sleep(0.1)
                except CancelledError:
                    logging.debug("execute_commands cancelled")
                    break
        finally:
            logging.debug("Stopping main loop")
        self.cancel_events()
        return True


"""
class HunterOld(object):
    # The device's type name. e.g. radar
    device_type = ''

    # Canonical name of the navigator profile
    navigator_name = ''

    # Properties of hunt this hunter is attached to
    hunt_context = None
    # How long the device rests before ready to detect again (in seconds)
    device_interval = 0
    # Range of detection
    detection_range = 0
    # Angle of detection
    detection_angle = 360
    # Device is ready to scan
    device_ready = False
    # If the hunt has begun, begin allowing event discovery
    hunt_begun = False
    # The main event loop for the device
    event_loop = None
    # The websocket for communication with the hunt server
    websocket = None

    options = {}

    def __init__(self, hunt_context):
        super(HunterOld, self).__init__()
        self.hunt_context = hunt_context

    def get_async_events(self):
        return [self.device_recharge()]

    # connect to Hunt websocket, reconnect if lost
    async def getwebsocket(self):
        if self.websocket is None or self.websocket.open is False:
            logging.debug("Establishing websocket connection")
            await websockets.getwebsocket(HUNT_URL)
        return self.websocket

    # Activate the device
    # Overwrite this with your object's bootup
    # but remember to toggle ready and broadcast
    def bootup(self, loop):
        pass

    def shutdown(self):
        self.event_loop.cancel_events()
        self.event_loop.close()

    # Time device 'cooldown' after detection attempt
    async def device_recharge(device):
        if device.device_ready is False:
            await time.sleep(device.device_interval)
            device.device_ready is True

    # Send the device's position and properties
    # to hunt server
    async def broadcast_position(self):
        try:
            # Check if socket open, otherwise try to reconnect
            await self.getwebsocket()
            await self.websocket.send(self.serialize())
        except websockets.exceptions.ConnectionClosed:
            logging.warning("websocket connection lost")
        except websockets.exceptions.InvalidURI:
            logging.error("Bad websocket URI")

    # Begin a detection sweep.
    async def init_detection(self):
        logging.debug(self.uid + ": begin detection sweep")
        # Query hunt
        hunt_response = await self.send_detection_request()
        await self.parse_response(hunt_response)
        # Finish  detection
        self.reset_device(hunt_response)

    def parse_response(self, hunt_response):
        detected = hunt_response.get('detected')
        if (detected):
            self.detected(hunt_response)
        else:
            self.notdetected(hunt_response)

    # Detection sweep finished, cleanup
    def end_detection(self, hunt_response):
        logging.debug(self.uid + ": end detection sweep")
        self.device_ready = False

    # Serialize device's properties
    def serialize(self):
        return {"hunt_uid": self.hunt_context['hunt_uid'],
                "uid": self.uid,
                "device_type": self.device_type,
                "navigator_name": self.navigator_name,
                "detection_interval": self.detection_interval,
                "detection_range": self.detection_range,
                "detection_angle": self.detection_angle,
                "position": self.getposition(),
                "options": self.options
                }

    # Clue detected.  Do something
    def detected(self, hunt_response):
        pass

    # Nothing Found
    def notdetected(self):
        pass

    # Return the device's current position
    # in the units of the navigation profile
    def getposition(self):
        pass

    # Device is ready to scan again
    def set_device_ready(self):
        self.device_ready = True
"""
# class HunterRSSI(HunterOld):
#     navigator_name = 'RSSI'
#     # Use wifi
#     # todo shutting this off for now
#     wifi = False
#     # Use BLE
#     BLE = True
#     # The serialized version of the fingerprint database
#     fingerprints = None
#     # time database was downloaded
#     fingerprint_timestamp = None
#     # Events that are active and could be detected by device
#     available_events = None
#
#
#     # id of the point in fingerprint database of current location
#     # todo or just ble uid?
#     current_location = {"x": 0, "y": 0, "z": 0}
#
#     # Wifi variables
#     # commands for getting/parsing wifi report
#     iwargs = shlex.split('iwlist wlan0 scanning')
#     egrepargs = shlex.split("egrep 'Cell |ESSID|Quality'")
#
#     def __init__(self, hunt_context, wifi=False, BLE=True):
#         super(HunterRSSI, self).__init__(hunt_context)
#         self.hunt_context = hunt_context
#         self.wifi = wifi
#         self.BLE = BLE
#
#         # send timestamp to navigator
#         # download new db if out of date
#         # instantiate when ready
#
#     def update_fingerprint_database(self, response):
#         if response != "0":
#             # Update the database
#             new_database = json.loads(response)
#             self.fingerprint_timestamp = new_database['timestamp']
#             self.fingerprints = new_database['fingerprints']
#         return True
#
#     # listen on websocket for updates from server
#     async def listen_server(self):
#         # todo error trap
#         server_update = await self.websocket.recv()
#         if HUNT_BEGIN_MESSAGE in server_update:
#             # hunt begin
#             self.hunt_begin()
#         elif HUNT_END_MESSAGE in server_update:
#             # Hunt over
#             self.hunt_ended()
#         elif EVENT_UPDATE_MESSAGE_HEADER in server_update:
#             # update available events
#             # todo Something else happen here, notify other parts of event change?
#             new_events = json.loads(server_update)
#             self.available_events = new_events[EVENT_UPDATE_MESSAGE_HEADER]
#
#     def hunt_begin(self):
#         self.hunt_begun = True
#
#     def hunt_ended(self):
#         # todo cooldown, send final data state?
#         self.shutdown()
#
#     def get_async_events(self):
#         return [self.device_recharge(), self.update_position(), self.listen_server()]
#
#     # Activate the device
#     def bootup(self, loop):
#         super(HunterRSSI, self).bootup()
#         # Setup the event loop
#         if loop is None:
#             raise RuntimeError("No event loop passed")
#         if loop.is_closed():
#             raise RuntimeError("Event loop already closed")
#         self.loop = loop
#
#         print("Connecting to server...")
#         try:
#             ready = yield from asyncio.wait_for(self.getwebsocket(), 10, loop=self.loop)
#         except asyncio.TimeoutError:
#             raise asyncio.TimeoutError("Connection to hunt server failed!")
#
#         asyncio.ensure_future(self.get_async_events(), loop=self.loop)
#
#         print("Device ready")
#         self.device_ready = True
#         # try:
#         #     self.loop.run_forever()
#         # finally:
#         #     self.loop.close()
#
#     # Uses iwlist parsed with egrep to get nearby access points
#     # Note: Requires sudo!
#     async def get_wifi(self):
#         iwprocess = subprocess.Popen(self.iwargs, stdout=subprocess.PIPE)
#         egrepprocess = subprocess.Popen(
#             self.egrepargs, stdin=iwprocess.stdout, stdout=subprocess.PIPE)
#         wifi_report = egrepprocess.communicate()
#         wifi = list()
#         for access_point in wifi_report:
#             point = None
#             if access_point is not None:
#                 for line in access_point.split('\n'):
#                     if 'Cell' in line:
#                         # New access point
#                         # Example: Cell 03 - Address: 00:8A:AE:DB:B6:E6
#                         point = {}
#                         m = re.search('Address\: (.*)$', line)
#                         if m is not None:
#                             point['Address'] = m.group(1)
#                     elif 'ESSID' in line:
#                         # ESSID:"SKY15622"\n
#                         m = re.search('ESSID\:\s*\"(.*)\"', line)
#                         if m is not None:
#                             point['ESSID'] = m.group(1)
#                     elif 'Signal' in line:
#                         # Quality=36/70  Signal level=-74 dBm
#                         # todo Quality as well?
#                         m = re.search('Signal level\=\s*(.*) dBm', line)
#                         if m is not None:
#                             point['RSSI'] = m.group(1)
#                 if point is not None:
#                     wifi.append(point)
#         return wifi
#
#     # Return the last scan results
#     def get_ble(self):
#         return self.ble_scan_data
#
#
#     # Uses bluepy https://github.com/IanHarvey/bluepy
#     # Scan for bluetooth devices, filter by prefix
#     # to only get relevant beacons, return mac & RSSI
#     async def get_ble_devices(self):
#         devices = await self.ble_scan()
#         # Clear the last scan
#         ble_devices = list()
#         for dev in devices:
#             # Get name
#             for (adtype, desc, value) in dev.getScanData():
#                 if "Local Name" in desc:
#                     name = value
#                     # Does name prefix exist in local name?
#                     if (name is not None and self.ble_name_prefix in name):
#                         ble_devices.append({'MAC': dev.addr,
#                                             "Name": name, "RSSI": dev.rssi})
#         # Use nearest beacon for database
#         nearest = sorted(ble_devices, key=itemgetter('RSSI'), reverse=True)
#         self.ble_scan_data = ble_devices
#
#     # currently only straight ble lookup
#     # todo modify by rssi if possible
#     async def get_fingerprint_from_signals(self, new_position_data):
#         ble_data = new_position_data['ble']
#         try:
#             return self.fingerprints[ble_data[0]['MAC']]
#         except IndexError:
#             logging.warning("Beacon with MAC {} not found in fingerprints!".format(ble_data[0]['MAC']))
#
#     # Return wifi and/or BLE signal information
#     async def getsignals(self):
#         if self.wifi:
#             wifi = self.get_wifi()
#         else:
#             wifi = {}
#         if self.BLE:
#             # Is this right? How to do in paralell?
#             BLE = await self.get_ble_devices()
#         else:
#             BLE = {}
#         position = {'RSSI': {'wifi': wifi, 'ble': BLE}}
#         return position
#
#     async def update_position(self):
#         new_position_data = await self.getsignals()
#         new_location = self.get_fingerprint_from_signals(new_position_data)
#         if new_location != self.current_location:
#             # Location has changed
#             self.current_location = new_location
#             self.broadcast_position()
