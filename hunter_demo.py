import asyncio
import concurrent.futures
from concurrent.futures import CancelledError
from hunter.ble import HunterBLE


class HunterTest(HunterBLE):
    device_interval = 5
    hunt_url = 'ws://demos.kaazing.com/echo'
    # hunt_url = 'ws://127.0.0.1:8000/hunt/1/'
    countdown = 0
    MAC = '78:4f:43:6c:cc:0f'

    async def get_device_input(self):
        while True:
            try:
                print('Getting input...')
                await asyncio.sleep(3)
                if self.countdown == 2:
                    print('Order shutdown...')
                    self.command_queue.append(self.COMMAND_SHUTDOWN)
                    return None
                else:
                    print("Again")
                    self.countdown += 1
                    asyncio.ensure_future(self.get_device_input())
            except CancelledError:
                break
        return None

    async def ghost_echo(self):
        websocket = await self.get_ghost_server_socket()
        await websocket.send('GHOST!')
        return None

    def extra_device_functions(self):
        """ Override with device-specific extra functions 
        you want to add to the loop"""
        extras = super(HunterTest, self).extra_device_functions()
        extras.append(self.ghost_echo())
        return extras

    async def func1(self):
        print('Func1 begin')
        await asyncio.sleep(2)
        print('Func1 end')

    async def func2(self):
        print('Func2 begin')
        await asyncio.sleep(5)
        print('Func2 end')

    async def func3(self):
        print('Func3 begin')
        await asyncio.sleep(3)
        print('Func3 end')

    async def test_heartbeat(self):
        while True:
            try:
                self.func1()
                self.func2()
                self.func3()
            except KeyboardInterrupt:
                break
        self.shutdown()


# todo command_consumer
# todo wrap ble in executor

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        hunter = HunterTest(loop, executor)
        try:
            hunter.bootup()
        finally:
            loop.stop()
            loop.close()

