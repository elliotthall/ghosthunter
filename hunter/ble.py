from bluepy.btle import Scanner, BTLEException
from .core import Hunter
import logging
"""
Bluetooth Low Energy version of Ghost Hunter
Elliott Hall 7/12/2017

Moved to its own file so that core functions can be tested on a Mac
"""

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

    # Uses bluepy https://github.com/IanHarvey/bluepy


    async def ble_scan(self):
        """ Run ble scan and return found devices"""
        devices = None
        try:
            scanner = Scanner()
            devices = scanner.scan(self.ble_scan_length)
        except BTLEException as blexception:
            logging.error(blexception)
        return devices

    async def get_ble_devices(self):
        """ Scan for bluetooth devices
         filter by prefix to only get relevant beacons
         :return: device list with dict {name, mac & RSSI} 
        """
        devices = await self.ble_scan()
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
                    # nearest = sorted(ble_devices, key=itemgetter('RSSI'), reverse=True)
        return ble_devices

    async def bluetooth_scan(self):
        """ Call bluetooth scan
        Log with ghost server when relevant devices found
        Determine distance?
        Pass to display where?
        :return: 
        """
        while True:
            scan_results = await self.get_ble_devices()
            if len(scan_results) > 0:
                for scan in scan_results:
                    logging.info("Discovered BLE device {}".format(scan))

    def extra_device_functions(self):
        """ Add bluetooth scan to loop"""
        return [self.bluetooth_scan()]
