import asyncio
from core import Hunter_RSSI
import time
from devices.radar import PiMicroRadarCartesian_RSSI

# todo refactor radar to use async

# todo then detection loop?

trigger = False



async def main():
    hunt_context = {}
    print("Pi Microbit Ghost Radar version 0.1")
    device = PiMicroRadarCartesian_RSSI(hunt_context)
    device.device_ready = False



if __name__ == '__main__':
    event_loop = asyncio.get_event_loop()
    try:
        event_loop.run_until_complete(main())
    finally:
        event_loop.close()

