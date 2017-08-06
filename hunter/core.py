import asyncio
import json
import logging
import re
import shlex
import subprocess
import time
from operator import itemgetter

import websockets
from bluepy.btle import Scanner

from local import (
    HUNT_URL,
    NAVIGATOR_URL
)

HUNT_BEGIN_MESSAGE = u'HUNT_BEGIN'
HUNT_END_MESSAGE = u'HUNT_END'
EVENT_UPDATE_MESSAGE_HEADER = u'available_events'

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
    # If the hunt has begun, begin allowing event discovery
    hunt_begun = False
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

    # connect to Hunt websocket, reconnect if lost
    async def getwebsocket(self):
        if self.websocket is None or self.websocket.open is False:
            logging.debug("Establishing websocket connection")
            await websockets.getwebsocket(HUNT_URL)
        return self.websocket

    # Activate the device
    # Overwrite this with your object's bootup
    # but remember to toggle ready and broadcast
    async def bootup(self):
        pass

    def shutdown(self):
        self.event_loop.stop()
        self.event_loop.close()

    # Time device 'cooldown' after detection attempt
    async def device_recharge(device):
        if device.device_ready == False:
            await time.sleep(device.device_interval)
            device.device_ready = True

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
Subclass of hunter that uses wifi and/or BLE for positioning


- Recharge (if previously activated)
- Determine location
    - Send change to server if changed
- Listen for new information from server

"""


class HunterRSSI(HunterBase):
    navigator_name = 'RSSI'
    # Use wifi
    # todo shutting this off for now
    wifi = False
    # Use BLE
    BLE = True
    # The serialized version of the fingerprint database
    fingerprints = None
    # time database was downloaded
    fingerprint_timestamp = None
    # Events that are active and could be detected by device
    available_events = None

    # Bluetooh options
    # Length of time to scan
    ble_scan_length = 3.0
    # Sleep intervals between scans
    ble_scan_rest = 2.0
    ble_name_prefix = "Kontakt"
    ble_scan_data = {}

    # id of the point in fingerprint database of current location
    # todo or just ble uid?
    current_location = {"x": 0, "y": 0, "z": 0}

    # Wifi variables
    # commands for getting/parsing wifi report
    iwargs = shlex.split('iwlist wlan0 scanning')
    egrepargs = shlex.split("egrep 'Cell |ESSID|Quality'")

    def __init__(self, hunt_context, wifi=False, BLE=True):
        super(HunterRSSI, self).__init__(hunt_context)
        self.hunt_context = hunt_context
        self.wifi = wifi
        self.BLE = BLE

        # send timestamp to navigator
        # download new db if out of date
        # instantiate when ready

    async def update_fingerprint_database(self):
        async with websockets.connect(NAVIGATOR_URL) as websocket:
            await websocket.send(self.fingerprint_timestamp)
            response = await websocket.recv()
            if response != "0":
                # Update the database
                new_database = json.loads(response)
                self.fingerprint_timestamp = new_database['timestamp']
                self.fingerprints = new_database['fingerprints']
            return True

    # listen on websocket for updates from server
    async def listen_server(self):
        # todo error trap
        server_update = await self.websocket.recv()
        if HUNT_BEGIN_MESSAGE in server_update:
            # hunt begin
            self.hunt_begin()
        elif HUNT_END_MESSAGE in server_update:
            # Hunt over
            self.hunt_ended()
        elif EVENT_UPDATE_MESSAGE_HEADER in server_update:
            # update available events
            # todo Something else happen here, notify other parts of event change?
            new_events = json.loads(server_update)
            self.available_events = new_events[EVENT_UPDATE_MESSAGE_HEADER]

    def hunt_begin(self):
        self.hunt_begun = True


    def hunt_ended(self):
        # todo cooldown, send final data state?
        self.shutdown()

    def get_async_events(self):
        return [self.device_recharge(), self.update_position(), self.listen_server()]

    # Activate the device
    def bootup(self):
        super(HunterRSSI, self).bootup()
        print("Getting Fingerprint Databse...")
        try:
            ready = yield from asyncio.wait_for(self.update_fingerprint_database(), 5)
        except asyncio.TimeoutError:
            raise asyncio.TimeoutError("Connection to fingerprint db failed!")
        print("Connecting to server...")
        try:
            ready = yield from asyncio.wait_for(self.getwebsocket(), 5)
        except asyncio.TimeoutError:
            raise asyncio.TimeoutError("Connection to hunt server failed!")
        # Setup the event loop
        self.loop = asyncio.get_event_loop()
        asyncio.ensure_future(self.get_async_events())
        print("Device ready")
        self.device_ready = True
        # try:
        #     self.loop.run_forever()
        # finally:
        #     self.loop.close()

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
        return self.ble_scan_data

    async def ble_scan(self):
        scanner = Scanner()
        return scanner.scan(self.ble_scan_length)

    # Uses bluepy https://github.com/IanHarvey/bluepy
    # Scan for bluetooth devices, filter by prefix
    # to only get relevant beacons, return mac & RSSI
    async def get_ble_devices(self):
        devices = await self.ble_scan()
        # Clear the last scan
        ble_devices = list()
        for dev in devices:
            # Get name
            for (adtype, desc, value) in dev.getScanData():
                if "Local Name" in desc:
                    name = value
                    # Does name prefix exist in local name?
                    if (name is not None and self.ble_name_prefix in name):
                        ble_devices.append({'MAC': dev.addr,
                                            "Name": name, "RSSI": dev.rssi})
        # Use nearest beacon for database
        nearest = sorted(ble_devices, key=itemgetter('RSSI'), reverse=True)
        self.ble_scan_data = ble_devices

    # currently only straight ble lookup
    # todo modify by rssi if possible
    async def get_fingerprint_from_signals(self, new_position_data):
        ble_data = new_position_data['ble']
        try:
            return self.fingerprints[ble_data[0]['MAC']]
        except IndexError:
            logging.warning("Beacon with MAC {} not found in fingerprints!".format(ble_data[0]['MAC']))

    # Return wifi and/or BLE signal information
    async def getsignals(self):
        if self.wifi:
            wifi = self.get_wifi()
        else:
            wifi = {}
        if self.BLE:
            # Is this right? How to do in paralell?
            BLE = await self.get_ble_devices()
        else:
            BLE = {}
        position = {'RSSI': {'wifi': wifi, 'ble': BLE}}
        return position

    async def update_position(self):
        new_position_data = await self.getsignals()
        new_location = self.get_fingerprint_from_signals(new_position_data)
        if new_location != self.current_location:
            # Location has changed
            self.current_location = new_location
            self.broadcast_position()
