import logging
from core import Hunter_RSSI
import serial
import io

# import explorerhat as eh
"""
Radar style ghost hunting device
Sweeps the are in 360 degrees for clues

Note:
class naming convention: device-type-navigator

"""


class PiMicroRadar(Hunter_RSSI):
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
    def get_microbit_sensor_data(self):
        data = {}
        if self.serial is None:
            self.init_serial()
        if self.serial is not None:            
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

    def set_device_ready(self):
        self.device_ready = True
        if self.serial is None:
            self.init_serial()
        self.serial.write('device_ready=1\n'.encode())

    def init_serial(self):
        self.serial = serial.Serial(self.serial_address, 115200, timeout=3)

    def getposition(self):
        position = super(PiMicroRadar, self).getPosition()
        # Add the microbit information
        microbit_data = self.get_microbit_sensor_data()
        position['heading'] = microbit_data['heading']
        return position
