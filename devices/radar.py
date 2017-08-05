import logging
from core import HunterRSSI
import serial
import io

# import explorerhat as eh
"""
Radar style ghost hunting device
Sweeps the are in 360 degrees for clues

Note:
class naming convention: device-type-navigator

Additions to Event Loop:
- Check serial connection for input from micrbit

"""


class PiMicroRadar(HunterRSSI):
    device_type = 'radar'

    # Properties of hunt this hunter is attached to
    hunt_context = None
    # Interval between detection passes (in milliseconds)
    detection_interval = 300
    # Range of detection
    detection_range = 50
    # Angle of detection
    detection_angle = 360
    # Default for Pis
    serial_address = '/dev/ttyACM0'
    serial = None
    sio = None

    def get_async_events(self):
        async_events = super(PiMicroRadar, self).get_async_events()
        async_events.append(self.listen_microbit())
        return async_events

    # Clue detected.  Pass back
    def detected(self, hunt_response):
        if self.serial is None:
            self.init_serial()
        detected_string = 'detected=1'
        try:
            if hunt_response.get('clue_heading'):
                detected_string += ',clue_heading='
                +hunt_response['clue_heading']
            if hunt_response.get('clue_distance'):
                detected_string += ',clue_distance='
                +hunt_response['clue_distance']
            detected_string += '\n'
            self.serial.write(detected_string.encode())
        except KeyError:
            logging.error('Bad Microbit input {}'.format(hunt_response))

    # Nothing Found
    def notdetected(self, hunt_response):
        if self.serial is None:
            self.init_serial()
        self.serial.write(b'detected=0\n')

    # Read the sensor data from the microbit over the serial connection
    async def listen_microbit(self):
        data = {}
        if self.serial is None:
            self.init_serial()
        if self.serial is not None:
            # Check for messages from microbit first
            microbit_response = self.serial.readline()
            if microbit_response and len(microbit_response) > 0:
                # Parse the microbit message
                if "begin_detection" in microbit_response:
                    await self.init_detection()

            # Request sensor data
            self.serial.write(b'request_sensor_data=1\n')
            data_line = self.serial.readline()
            try:
                if len(data_line) > 0:
                    data = dict(x.split('=') for x in data_line.split(','))
                else:
                    print("No Microbit data returned")
            except ValueError:
                print ("Bad data from microbit {}".format(data_line))
        return data

    async def init_detection(self):
        pass

    def send_device_ready(self):
        self.device_ready = True
        if self.serial is None:
            self.init_serial()
        self.serial.write('device_ready=1\n'.encode())

    def init_serial(self):
        self.serial = serial.Serial(self.serial_address, 115200, timeout=3)

    def getposition(self):
        position = super(PiMicroRadar, self).getPosition()
        # Add the microbit information
        microbit_data = self.listen_microbit()
        position['heading'] = microbit_data['heading']
        return position
