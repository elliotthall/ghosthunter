import asyncio
import logging
import functools
import serial

from .ble import HunterBLE


class HunterMicrobit(HunterBLE):
    """
    Bluetooth Hunter using attached Micro:Bit as an interface
    """
    serial_address = '/dev/ttyACM0'
    serial = None

    # Message to pass/receive from Micro:bit
    BUTTON_A_PRESSED = b"B_A_1\n"
    BUTTON_B_PRESSED = b"B_B_1\n"
    PING = b"PING\n"
    ECHO = b"ECHO\n"


    async def connect_serial(self):
        """ Connect to serial over usb"""
        try:
            self.serial = serial.Serial(self.serial_address, 115200, timeout=3)
            return True
        except asyncio.TimeoutError:
            logging.error("Serial connection failed!")
            raise IOError("Serial connection failed!")
        except asyncio.CancelledError:
            return None

    async def send_serial_message(self, message):
        """Send a message to the microbit
        NOTE: Must be bytestring, terminated with newline"""
        try:
            future = self.event_loop.run_in_executor(
                self.executor,
                functools.partial(self.serial.write, message)
            )
            await asyncio.wait_for(future, 30, loop=self.event_loop)
        except TypeError as e:
            logging.error("Bad microbit sent message: {}".format(e))
        except asyncio.TimeoutError:
            # check serial connection
            if self.serial.is_open is False:
                # serial connection lost, try to reestablish
                self.connect_serial()

    def parse_microbit_serial_message(self, message):
        """Parse any messages from microbit and 
        add to command queue as necesssary"""
        command = None
        if self.BUTTON_A_PRESSED in message:
            command = self.COMMAND_TRIGGER
        self.command_queue.append(command)
        return command

    def read_serial(self):
        return self.serial.readline()

    async def receive_serial_message(self):
        """ Listen for JSON serial messages, pass to parser"""
        while True:
            try:
                future = self.event_loop.run_in_executor(
                    self.executor, self.read_serial)
                message = await asyncio.wait_for(
                    future, 30, loop=self.event_loop)
                logging.debug("Serial message received: {}".format(message))
                self.parse_microbit_serial_message(message)
            except asyncio.TimeoutError:
                # check serial connection
                if self.serial.is_open is False:
                    # serial connection lost, try to reestablish
                    self.connect_serial()

    def extra_device_functions(self):
        """ Add bluetooth scan to loop"""
        device_functions = super(HunterMicrobit, self).extra_device_functions()
        device_functions.append(self.receive_serial_message())
        return device_functions
