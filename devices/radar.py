import logging
from core import Hunter_RSSI
import serial
import io
import subprocess
import shlex
import explorerhat as eh
"""
Radar style ghost hunting device
Sweeps the are in 360 degrees for clues

Note:
class naming convention: device-type-navigator

"""


class PiMicroRadarCartesian_RSSI(Hunter_RSSI):
    device_type = 'radar'

    # Properties of hunt this hunter is attached to
    hunt_context = None
    # Interval between detection passes (in milliseconds)
    detection_interval = 300
    # Range of detection
    detection_range = 50
    # Angle of detection
    detection_angle = 360
    serial_address = '/dev/ttyACM0'
    serial = None
    sio = None
    iwargs = shlex.split('iwlist wlan0 scanning')
    egrepargs = shlex.spli("egrep 'Cell |ESSID|Quality'")

    # Clue detected.  Pass back
    def detected(self, hunt_response):
        pass

    # Nothing Found
    def notdetected(self):
        pass

    # Uses iwlist parsed with egrep to get nearby access points
    # Note: Requires sudo!
    def get_wifi(self):
        p1 = subprocess.Popen(self.iwargs, stdout=subprocess.PIPE)
        p2 = subprocess.Popen(
            self.egrepargs, stdin=p1.stdout, stdout=subprocess.PIPE)
        pass

    def get_BLE(self):
        pass

    # Read the sensor data from the microbit over the serial connection
    def get_microbit_sensor_data(self):
        data = {}
        if self.serial is None:
            self.init_serial()
        if self.serial is not None:
            data_line = self.sio.readline()
            if len(data_line) > 0:
                data = dict(x.split('=') for x in data_line.split(','))
            else:
                print("NO Microbit data")
            return data

    def init_serial(self):
        self.serial = serial.Serial(self.serial_address, 115200, timeout=1)
        self.sio = io.TextIOWrapper(io.BufferedRWPair(serial, serial))

    def getposition(self):
        position = super(PiMicroRadarCartesian_RSSI, self).getPosition()
        # Add the microbit information
        microbit_data = self.get_microbit_sensor_data()
        position['heading'] = microbit_data['heading']
        return position
