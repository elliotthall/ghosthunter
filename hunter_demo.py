import asyncio
import websockets
from hunter.core import Hunter


class HunterTest(Hunter):
    device_interval = 5
    hunt_url = 'ws://demos.kaazing.com/echo'
    countdown = 0

    async def get_device_input(self):
        print('Getting input...')
        await asyncio.sleep(3)
        if self.countdown == 2:
            print('Order shutdown...')
            self.shutdown()
        else:
            print("Again")
            self.countdown += 1
            asyncio.ensure_future(self.get_device_input())
        return None

    async def ghost_echo(self):
        websocket = await self.get_ghost_server_socket()
        await websocket.send('GHOST!')
        return None

    def extra_device_functions(self):
        """ Override with device-specific extra functions 
        you want to add to the loop"""
        return [self.ghost_echo()]


if __name__ == '__main__':
    hunter = HunterTest()
    hunter.bootup()
