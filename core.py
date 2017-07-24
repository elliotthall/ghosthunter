import asyncio
import logging
import re
import shlex
import subprocess
import time

import requests
import websockets
from bluepy.btle import Scanner

from local import (
    HUNT_URL,
    HUNT_DETECTION_URI
)

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
    # The main event loop for the device
    event_loop = None
    # The websocket for communication with the hunt server
    websocket = None

    options = {}

    def __init__(self, hunt_context):
        super(HunterBase, self).__init__()
        self.hunt_context = hunt_context

    def get_async_events(self):
        return [self.device_recharge()]

    # todo connect to Hunt websocket
    async def connect(self):
        self.websocket = websockets.connect(HUNT_URL)

    # todo send timestamp to navigator
    # download new db if out of date
    # instantiate when ready
    async def update_fingerprint_database(self):
        pass

    # Activate the device
    # Overwrite this with your object's bootup
    # but remember to toggle ready and broadcast
    async def bootup(self):

        # todo Query navigator for fingerprint database
        self.update_fingerprint_database()
        # Setup the event loop
        self.event_loop = asyncio.get_event_loop()
        self.event_loop.run_forever(self.get_async_events())
        retries = 0
        while self.device_ready is False and retries < 5:
            self.connect()
            if self.websocket:
                self.send_device_ready()
                self.device_ready = True
            else:
                retries += 1
                logging.warning("Connection to hunt server failed.  Retrying...")
        if retries == 5:
            raise IOError("Connection to hunt server failed.")

    def shutdown(self):
        self.event_loop.stop()
        self.event_loop.close()

    # Time device 'cooldown' after detection attempt
    async def device_recharge(device):
        if device.device_ready == False:
            await time.sleep(device.device_interval)
            device.device_ready = True

    # Send the device's position and properties
    # to hunt server via REST
    # todo websockets
    def broadcast_position(self):
        try:
            hunt_response = requests.post(
                self.hunt_context['broadcast_url'],
                json=self.serialize(), timeout=5)
            # If it's not 200, raise an exception
            hunt_response.raise_for_status()
            return hunt_response
        except requests.exceptions.Timeout as timeouterror:
            logging.error("Request timed out:" + timeouterror)
        except requests.exceptions.ConnectionError as connecterror:
            logging.error("Error connecting to hunt server:" + connecterror)
        except requests.exceptions.HTTPError as httperror:
            logging.error("Error in broadcast:" + httperror)

    # Query the hunt server with device's attribute and
    # current location.
    # Receive all active events it can "see"
    async def send_detection_request(self):
        # todo is this right? Error trap when correct
        async with websockets.connect(HUNT_DETECTION_URI) as websocket:
            await websocket.send(self.serialize())
            hunt_response = await websocket.recv()
            return hunt_response

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


# Subclass of hunter that uses wifi and/or BLE for positioning
class Hunter_RSSI(HunterBase):
    navigator_name = 'RSSI'
    # Use wifi
    # todo shutting this off for now
    wifi = False
    # Use BLE
    BLE = True
    # The serialized version of the fingerprint database
    fingerprints = None

    # Bluetooh options
    # Length of time to scan
    ble_scan_length = 3.0
    # Sleep intervals between scans
    ble_scan_rest = 2.0
    ble_name_prefix = "Kontakt"
    ble_fingerprints = {}
    stopevent = None

    # id of the point in fingerprint database of current location
    current_location_id = None

    # Wifi variables
    # commands for getting/parsing wifi report
    iwargs = shlex.split('iwlist wlan0 scanning')
    egrepargs = shlex.split("egrep 'Cell |ESSID|Quality'")

    def __init__(self, hunt_context, wifi=True, BLE=True):
        super(Hunter_RSSI, self).__init__(hunt_context)
        self.hunt_context = hunt_context
        self.wifi = wifi
        self.BLE = BLE

    def get_async_events(self):
        return [self.device_recharge(), self.update_position()]

    # Activate the device
    def bootup(self):
        super(Hunter_RSSI, self).bootup()

    # Uses iwlist parsed with egrep to get nearby access points
    # Note: Requires sudo!
    async def get_wifi(self):
        iwprocess = subprocess.Popen(self.iwargs, stdout=subprocess.PIPE)
        egrepprocess = subprocess.Popen(
            self.egrepargs, stdin=iwprocess.stdout, stdout=subprocess.PIPE)
        wifi_report = egrepprocess.communicate()
        wifi = list()
        for access_point in wifi_report:
            point = None
            if access_point is not None:
                for line in access_point.split('\n'):
                    if 'Cell' in line:
                        # New access point
                        # Example: Cell 03 - Address: 00:8A:AE:DB:B6:E6
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
                if point is not None:
                    wifi.append(point)
        return wifi

    # Return the last scan results
    def get_ble(self):
        return self.ble_fingerprints

    async def ble_scan(self):
        scanner = Scanner()
        return scanner.scan(self.ble_scan_length)

    # Uses bluepy https://github.com/IanHarvey/bluepy
    # Scan for bluetooth devices, filter by prefix
    # to only get relevant beacons, return mac & RSSI
    async def get_ble_devices(self):

        devices = await self.ble_scan()
        # Clear the last scan
        ble_fingerprints = {}
        for dev in devices:
            # Get name
            for (adtype, desc, value) in dev.getScanData():
                if "Local Name" in desc:
                    name = value
                    # Does name prefix exist in local name?
                    if (name is not None and self.ble_name_prefix in name):
                        ble_fingerprints[dev.addr] = {
                            "Name": name, "RSSI": dev.rssi}
                    break
        self.ble_fingerprints = ble_fingerprints

    # todo Accept new location data and find closest match
    # in fingerprint database with K-nearest algorithim
    @staticmethod
    async def get_fingerprint_from_signals(self, new_position_data):
        pass

    # Return wifi and/or BLE signal information
    async def getsignals(self):
        if self.wifi:
            wifi = await self.get_wifi()
        else:
            wifi = {}
        if self.BLE:
            BLE = await self.get_ble_devices()
        else:
            BLE = {}
        position = {'RSSI': {'wifi': wifi, 'BLE': BLE}}
        return position

    async def update_position(self):
        new_position_data = await self.getsignals()
        new_location = await self.get_fingerprint_from_signals(new_position_data)
        if new_location != self.current_location_id:
            # Location has changed
            self.current_location_id = new_location
            self.broadcast_position()
