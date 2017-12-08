import logging

from bluepy.btle import Scanner, BTLEException
import asyncio
from .core import Hunter

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

    def __init__(self, event_loop=None, executor=None, **kwargs):
        super(HunterBLE,self).__init__(event_loop,**kwargs)
        self.executor = executor


    def ble_scan(self):
        """ Run ble scan and return found devices"""
        devices = None
        try:
            scanner = Scanner()
            devices = scanner.scan(self.ble_scan_length)
        except BTLEException as blexception:
            logging.error(blexception)
        return devices

    def get_ble_devices(self, devices):
        """ Scan for bluetooth devices
         filter by prefix to only get relevant beacons
         :return: device list with dict {name, mac & RSSI} 
        """
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
        print('Begin scan...')
        devices = await self.event_loop.run_in_executor(self.executor, self.ble_scan)
        import pdb; pdb.set_trace()
        scan_results = self.get_ble_devices(devices.result())

        if len(scan_results) > 0:
            for scan in scan_results:
                logging.info("Discovered BLE device {}".format(scan))
        # Schedule another scan
        #asyncio.ensure_future(self.get_device_input())
        return scan_results


    def extra_device_functions(self):
        """ Add bluetooth scan to loop"""
        return [self.bluetooth_scan()]
