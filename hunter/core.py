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
from bluepy.btle import Scanner, BTLEException

import hunter.peripherals.microbit.utils as microbit_utils
import hunter.peripherals.uwb.uart as uwb
import hunter.utils as utils

# from bluepy.btle import Scanner

HUNT_BEGIN_MESSAGE = u'HUNT_BEGIN'
HUNT_END_MESSAGE = u'HUNT_END'
EVENT_UPDATE_MESSAGE_HEADER = u'available_events'
__author__ = 'elliotthall'


def stop_loop_callback(future):
    print(future.result())
    asyncio.get_event_loop().stop()


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


class HunterBLE(Hunter):
    """ Hunter with added Bluetooth low energy support
    """
    # Bluetooh options
    # Length of time to scan
    ble_scan_length = 5.0
    # Sleep intervals between scans
    ble_scan_rest = 0.0
    # filter out devices that don't have this prefix
    ble_name_prefix = "Kontakt"
    current_ble_devices = list()

    # Uses bluepy https://github.com/IanHarvey/bluepy

    def __init__(self, event_loop=None, executor=None, **kwargs):
        super(HunterBLE, self).__init__(event_loop, **kwargs)
        self.executor = executor

    def ble_scan(self):
        """ Run ble scan and return found devices"""
        devices = None
        try:
            scanner = Scanner()
            devices = scanner.scan(self.ble_scan_length)
        except BTLEException as blexception:
            logging.error(blexception)
        return devices

    def get_ble_devices(self, devices):
        """ Scan for bluetooth devices
         filter by prefix to only get relevant beacons
         :return: device list with dict {name, mac & RSSI}
        """
        ble_devices = list()
        if devices:
            for dev in devices:
                # Get name
                name = None
                for (adtype, desc, value) in dev.getScanData():
                    if "Local Name" in desc:
                        name = value
                        # Does name prefix exist in local name?
                if (name is not None and self.ble_name_prefix in name):
                    ble_devices.append({'MAC': dev.addr,
                                        "Name": name, "RSSI": dev.rssi})
                    # Use nearest beacon for database
        return ble_devices

    async def bluetooth_scan(self):
        """ Call bluetooth scan
        Log with ghost server when relevant devices found
        Determine distance?
        Pass to display where?
        :return:
        """
        logging.info('Bluetooth starting up...')
        while True:
            try:

                devices = await self.event_loop.run_in_executor(
                    self.executor, self.ble_scan)
                scan_results = self.get_ble_devices(devices)
                if len(scan_results) > 0:
                    for scan in scan_results:
                        logging.info("Discovered BLE device {}".format(scan))
                # write results to class
                self.current_ble_devices = scan_results
            except CancelledError:
                logging.info("Bluetooth finished")
                break
        return True

        # return scan_results

    def extra_device_functions(self):
        """ Add bluetooth scan to loop"""
        device_functions = super(HunterBLE, self).extra_device_functions()
        device_functions.append(self.bluetooth_scan())
        return device_functions


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
        # Flush for safety
        first_conn.reset_input_buffer()
        first_conn.reset_output_buffer()
        second_conn.reset_output_buffer()
        second_conn.reset_input_buffer()
        if (int.from_bytes(return_type, byteorder='little')
                == uwb.DWM_RETURN_BYTE):
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
            try:
                micro_result =self.microbit_serial.readline()
                if microbit_utils.MICROBIT_CODES['ready'] in micro_result:
                # Microbit ready
                    logging.info('Micro:bit ready.')
                else:
                    logging.error('Micro:bit startup failed!')
                    return False
                uwb_cfg = uwb.dwm_serial_get_cfg(self.uwb_serial)
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
        self.microbit_serial.write('{}::{}'.format(
            microbit_utils.MICROBIT_CODES['reset'],
            0
        ))

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
