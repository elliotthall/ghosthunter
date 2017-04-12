import logging
import requests
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
    # Interval between detection passes (in milliseconds)
    detection_interval = 0
    # Range of detection
    detection_range = 0
    # Angle of detection
    detection_angle = 360
    # Navigation profile

    options = {}

    def __init__(self, hunt_context):
        super(HunterBase, self).__init__()
        self.hunt_context = hunt_context

    # Begin a detection sweep.
    def init_detection(self):
        logging.debug(self.uid+": begin detection sweep")
        # Tell the Hunt where we are
        hunt_response = self.broadcast_position().json()
        self.parse_response(hunt_response)
        # Finish  detection
        self.end_detection(hunt_response)

    def parse_response(self, hunt_response):
        detected = hunt_response.get('detected')
        if (detected):
            self.detected(hunt_response)
        else:
            self.notdetected(hunt_response)

    # Detection sweep finished, cleanup
    def end_detection(self, hunt_response):
        logging.debug(self.uid+": end detection sweep")

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

# Subclass of hunter that uses wifi and/or BLE for positioning


class Hunter_RSSI(HunterBase):
    navigator_name = 'RSSI'
    # Use wifi
    wifi = True
    # Use BLE
    BLE = True

    def __init__(self, hunt_context, wifi=True, BLE=True):
        super(Hunter_RSSI, self).__init__()
        self.hunt_context = hunt_context
        self.wifi = wifi
        self.BLE = BLE

    def get_wifi(self):
        pass

    def get_BLE(self):
        pass

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
