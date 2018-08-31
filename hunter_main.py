import asyncio
import concurrent.futures
from concurrent.futures import CancelledError
from hunter.core import HunterUwbMicrobit
from hunter.devices import MainDevice
import logging
from shapely.geometry import Point
logging.basicConfig(
	level=logging.DEBUG, format='%(asctime)s %(levelname)s:%(message)s')
logging.getLogger(__name__).addHandler(logging.NullHandler())

# normal
run_forever = True



def main():
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        hunter = MainDevice(loop, executor,
                            hunt_url='ws://demos.kaazing.com/echo',
                            MAC='78:4f:43:6c:cc:0f'
                            )
        hunter.detectable_things = {
            0: [
                {'id': 0,
                 'geometry': Point(3650, 3010),
                 'level': 0}                 
            ]
        }
        """
        {'id': 1,
                 'geometry': Point(40, 467).buffer(50),
                 'level': 0},
                 {'id': 2,
                 'geometry': Point(569, 778),
                 'level': 0},
                 """
        websocket = loop.run_until_complete(hunter.get_ghost_server_socket())
        hunter.websocket = websocket        
        try:
            if hunter.bootup() is True:
                logging.info("Startup complete, running loop...")
                if run_forever:
                    hunter.event_loop.run_forever()
        except KeyboardInterrupt:
            print('Interrupted')
            hunter.shutdown()
        finally:            
            loop.close()
            hunter.microbit_serial.close()


if __name__ == '__main__':
    main()