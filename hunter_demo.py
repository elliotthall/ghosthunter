from hunter.core import Hunter
import asyncio

class HunterTest(Hunter):
    device_interval = 5

    async def get_device_input(self):
        print('Getting input...')
        await asyncio.sleep(self.device_interval)
        print ('Order shutdown...')
        return self.commands['SHUTDOWN']

if __name__ == '__main__':
    hunter = HunterTest()
    hunter.bootup()