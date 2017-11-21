from hunter.core import Hunter
import asyncio

class HunterTest(Hunter):
    device_interval = 5

    async def get_device_input(self):
        print('Getting input...')
        await asyncio.sleep(3)
        print ('Order shutdown...')
        self.command_queue.append(self.commands['SHUTDOWN'])
        return None

if __name__ == '__main__':
    hunter = HunterTest()
    hunter.bootup()