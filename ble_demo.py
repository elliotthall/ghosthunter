import asyncio
from core import HunterRSSI
import time
from devices.radar import PiMicroRadar

# todo refactor radar to use async

# todo then detection loop?

trigger = False



async def main():
    hunt_context = {}
    print("Pi Microbit Ghost Radar version 0.1")
    device = PiMicroRadar(hunt_context)
    device.device_ready = False
    fake_fingerprints = {
        "cf:a7:21:12:06:b8":{"x":5,"y":2,"z":0}
    }
    device.fingerprints = fake_fingerprints
    await device.update_position()
    print (device.current_location)




if __name__ == '__main__':
    event_loop = asyncio.get_event_loop()
    try:
        event_loop.run_until_complete(main())
    finally:
        event_loop.close()

