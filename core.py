import logging
import requests
import subprocess
import shlex
import re
from bluepy.btle import Scanner
import timer
import threading

logging.getLogger(__name__).addHandler(logging.NullHandler())
__author__ = 'elliotthall'
# This is the base object from which all hunter devices should be derived.


class HunterBase(object):
    # This device's unique id
    uid = ''
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

    options = {}

    def __init__(self, hunt_context):
        super(HunterBase, self).__init__()
        self.hunt_context = hunt_context

    # Activate the device
    # Overwrite this with your object's bootup
    # but remember to toggle ready and broadcast
    def bootup(self):
        # Do some setup stuff here
        self.device_ready = True
        self.send_device_ready()

    # Begin a detection sweep.
    def init_detection(self):
        logging.debug(self.uid+": begin detection sweep")
        # Tell the Hunt where we are
        hunt_response = self.broadcast_position().json()
        self.parse_response(hunt_response)
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
        logging.debug(self.uid+": end detection sweep")

    def reset_device(self, hunt_response):
        self.end_detection(hunt_response)
        # Start timer for device ready flag
        device_ready = threading.Timer(
            self.device_interval, self.set_device_ready)
        device_ready.setName('device_ready_timer')
        device_ready.start()

    # Send the device's position and properties
    # to hunt server via REST
    def broadcast_position(self):
        try:
            hunt_response = requests.post(
                self.hunt_context['broadcast_url'],
                json=self.serialize(), timeout=5)
            # If it's not 200, raise an exception
            hunt_response.raise_for_status()
            return hunt_response
        except requests.exceptions.Timeout as timeouterror:
            logging.error("Request timed out:"+timeouterror)
        except requests.exceptions.ConnectionError as connecterror:
            logging.error("Error connecting to hunt server:"+connecterror)
        except requests.exceptions.HTTPError as httperror:
            logging.error("Error in broadcast:"+httperror)

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


# Subclass of hunter that uses wifi and/or BLE for positioning
class Hunter_RSSI(HunterBase):
    navigator_name = 'RSSI'
    # Use wifi
    wifi = True
    # Use BLE
    BLE = True

    # Bluetooh options
    # Length of time to scan
    ble_scan_length = 5.0
    ble_name_prefix = "GHunt"
    ble_fingerprints = {}

    # Wifi variables
    # commands for getting/parsing wifi report
    iwargs = shlex.split('iwlist wlan0 scanning')
    egrepargs = shlex.spli("egrep 'Cell |ESSID|Quality'")

    def __init__(self, hunt_context, wifi=True, BLE=True):
        super(Hunter_RSSI, self).__init__()
        self.hunt_context = hunt_context
        self.wifi = wifi
        self.BLE = BLE

    # Activate the device
    def bootup(self):
        # Begin scanning thread
        if self.BLE:
            # todo kwargs instead?
            d = threading.Thread(name='ble_thread', target=self.ble_thread)
            d.setDaemon(True)
            d.start()

        self.set_device_ready()

    # Uses iwlist parsed with egrep to get nearby access points
    # Note: Requires sudo!
    def get_wifi(self):
        iwprocess = subprocess.Popen(self.iwargs, stdout=subprocess.PIPE)
        egrepprocess = subprocess.Popen(
            self.egrepargs, stdin=iwprocess.stdout, stdout=subprocess.PIPE)
        wifi_report = egrepprocess.communicate()
        wifi = list()
        point = None
        for line in wifi_report.split('\n'):
            if 'Cell' in line:
                # New access point
                # Example: Cell 03 - Address: 00:8A:AE:DB:B6:E6
                if point is not None:
                    wifi.append(point)
                point = {}
                m = re.search('Address\: (.*)$', line)
                if m is not None:
                    point['Address'] = m.group(1)
            elif 'ESSID' in line:
                # ESSID:"SKY15622"\n
                m = re.search('ESSID\:\s*\"(.*)\"', line)
                if m is not None:
                    point['ESSID'] = m.group(1)
            elif 'Signal' in line:
                # Quality=36/70  Signal level=-74 dBm
                # todo Quality as well?
                m = re.search('Signal level\=\s*(.*) dBm', line)
                if m is not None:
                    point['RSSI'] = m.group(1)

    # Return the last scan results
    def get_BLE(self):
        return self.ble_fingerprints

    def ble_thread(self):
        while True:
            self.ble_scan()
            timer.sleep(5)

    # Uses bluepy https://github.com/IanHarvey/bluepy
    # Scan for bluetooth devices, filter by prefix
    # to only get relevant beacons, return mac & RSSI
    def ble_scan(self):
        scanner = Scanner()
        devices = scanner.scan(self.ble_scan_length)
        # Clear the last scan
        self.ble_fingerprints = {}
        for dev in devices:
            # Get name
            for (adtype, desc, value) in dev.getScanData():
                if "Local Name" in desc:
                    name = value
                # Does name prefix exist in local name?
                if (name is not None and self.ble_name_prefix in name):
                    self.ble_fingerprints[dev.addr] = {
                        "Name": name, "RSSI": dev.rssi}

    # Return wifi and/or BLE signal information
    def getposition(self):
        if self.wifi:
            wifi = self.get_wifi()
        else:
            wifi = {}
        if self.BLE:
            BLE = self.get_BLE()
        else:
            BLE = {}
        position = {'RSSI': {'wifi': wifi, 'BLE': BLE}}
        return position
