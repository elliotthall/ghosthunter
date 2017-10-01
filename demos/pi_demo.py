from bluepy.btle import Scanner
import serial
import asyncio
from operator import itemgetter

# Beacon to look for
ble_name_prefix = "Kontakt"
serial_address = '/dev/ttyACM0'
serial = None
ble_scan_length = 3.0


async def ble_scan():
    scanner = Scanner()
    return scanner.scan(ble_scan_length)

# Uses bluepy https://github.com/IanHarvey/bluepy
# Scan for bluetooth devices, filter by prefix
# to only get relevant beacons, return mac & RSSI

# Scan for bluetooth
# find beacon
# write to serial


async def get_ble_devices():
    devices = await ble_scan()
    # Clear the last scan
    ble_devices = list()
    for dev in devices:
        # Get name
        for (adtype, desc, value) in dev.getScanData():
            if "Local Name" in desc:
                name = value
                # Does name prefix exist in local name?
                if (name is not None and ble_name_prefix in name):
                    ble_devices.append({'MAC': dev.addr,
                                        "Name": name, "RSSI": dev.rssi})
    # Use nearest beacon for database
    nearest = sorted(ble_devices, key=itemgetter('RSSI'), reverse=True)
    if nearest is not None:
        if serial is not None:
            serial.write('RSSI={}\n'.format(nearest[0]['RSSI']))
        else:
            print("SERIAL CONNECTION not established")


if __name__ == '__main__':
    serial = serial.Serial(serial_address, 115200, timeout=3)
    event_loop = asyncio.get_event_loop()
    event_loop.create_task(get_ble_devices())
    try:
        event_loop.run_forever()
    finally:
        event_loop.close()
