import asyncio
import logging
import functools
import serial


def connect_serial(address):
    """ Connect to serial over usb
    :type address: basestringg
    :param address: UART address to connect to
    :return connection
    """
    try:
        return serial.Serial(address, 115200, timeout=3)
    except (serial.SerialTimeoutException, IOError):
        logging.error("Serial connection to {} failed!".format(
            address
        ))


# async def send_serial_message(serial_connection, message):
#     """Send a message to the microbit"""
#     try:
#         future = self.event_loop.run_in_executor(
#             self.executor,
#             functools.partial(serial_connection.write, message)
#         )
#         serial = await asyncio.wait_for(future, 30, loop=self.event_loop)
#     except asyncio.TimeoutError:
#         # check serial connection
#         if serial_connection.is_open is False:
#             # serial connection lost, try to reestablish
#             self.connect_serial()
#
#
#
# async def receive_serial_message(serial_connection):
#     """ Listen for JSON serial messages, pass to parser"""
#     while True:
#         try:
#             future = self.event_loop.run_in_executor(
#                 self.executor, serial_connection.readline())
#             serial = await asyncio.wait_for(
#                 future, 30, loop=self.event_loop)
#             self.parse_microbit_serial_message(serial)
#         except asyncio.TimeoutError:
#             # check serial connection
#             if serial_connection.is_open is False:
#                 # serial connection lost, try to reestablish
#                 self.connect_serial()