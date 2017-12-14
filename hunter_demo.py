import asyncio
import concurrent.futures
from concurrent.futures import CancelledError
from hunter.pi_microbit import HunterMicrobit


class HunterTest(HunterMicrobit):
    device_interval = 5
    hunt_url = 'ws://demos.kaazing.com/echo'
    # hunt_url = 'ws://127.0.0.1:8000/hunt/1/'

    MAC = '78:4f:43:6c:cc:0f'

    async def get_device_input(self):
        countdown = 0
        print('Getting input...')
        while True:
            try:
                await asyncio.sleep(3)
                if countdown == 2:
                    print('Order shutdown...')
                    self.command_queue.append(self.COMMAND_SHUTDOWN)
                    countdown += 1
                elif countdown < 2:
                    print("Input Again")
                    countdown += 1
            except CancelledError:
                break
        print("Input finished")
        return None

    async def websocket_echo(self):
        await self.send_server_message('GHOST!')
        return None

    async def serial_echo(self):
        await self.send_serial_message(b'PING\n')
        return None

    def extra_device_functions(self):
        """ Override with device-specific extra functions 
        you want to add to the loop"""
        extras = super(HunterTest, self).extra_device_functions()
        extras.append(self.websocket_echo())
        extras.append(self.serial_echo())
        return extras


def main():
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        hunter = HunterTest(loop, executor)
        websocket = loop.run_until_complete(hunter.get_ghost_server_socket())
        hunter.websocket = websocket
        loop.run_until_complete(hunter.connect_serial())
        try:
            hunter.bootup()
        finally:
            loop.run_until_complete(websocket.close())
            loop.run_until_complete(asyncio.gather(*asyncio.Task.all_tasks()))
            loop.close()
            hunter.serial.close()


if __name__ == '__main__':
    main()