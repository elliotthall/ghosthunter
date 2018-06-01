import asyncio
import concurrent.futures
import json
import logging
import pdb

import aiohttp
from pyHS100 import SmartBulb
from shapely.geometry import Point

from hunter.devices import ProximityDevice
from local import (POLTERGEIST_LOGIN, POLTERGEIST_PASSWORD)

logging.basicConfig(
    level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')
logging.getLogger(__name__).addHandler(logging.NullHandler())

POLTERGEIST_URL = 'https://ghost-hunt.mozilla-iot.org'
PLUG_1_URI = POLTERGEIST_URL + '/things/zwave-c83406e1-4'
BULB_IP = '10.0.1.7'

"""
{'name': 'room1-plug1', 'type': 'smartPlug', 'description': '', 'href': 
'/things/zwave-c83406e1-4', 'properties': {'on': {'type': 'boolean', 'href': 
'/things/zwave-c83406e1-4/properties/on'}, 
'instantaneousPower': {'type': 
'number', 'unit': 'watt', 'href': 
'/things/zwave-c83406e1-4/properties/instantaneousPower'}, 
'voltage': {
'type': 'number', 'unit': 'volt', 'href': 
'/things/zwave-c83406e1-4/properties/voltage'}, 'current': {'type': 
'number', 'unit': 'ampere', 'href': 
'/things/zwave-c83406e1-4/properties/current'}}, 'actions': {}, 'events': {
},
"""


# This will go into poltergeist when ready
class PoltergeistEvent(object):
    """Base class for a poltergeist event, something done by the ghost with
     the smart home technology"""
    # Can this effect happen right now?
    active = False
    # has it already happened?
    triggered = False
    # Number of times it can happen, -1 for infinite
    trigger_limit = 1

    def __init__(self, *args, **kwargs):
        pass

    async def check_trigger(self, *args, **kwargs):
        """Check if this event should be triggered"""
        pass

    async def trigger_event(self, *args, **kwargs):
        """Do the spooky action at a distance"""
        pass


class SimpleAPIPoltergeistEvent(PoltergeistEvent):
    """If hunter intersects trigger area, send an API message """
    poltergeist_url = POLTERGEIST_URL

    api_header = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }
    session = None
    trigger_points = [
        # Turn on the radio plug
        {'id': 0,
         'geometry': Point(0, 0).buffer(500),
         'call_type': 'put',
         'uri': poltergeist_url + '/things/zwave-c83406e1-4/properties/on',
         'json': {'on': True},
         }
    ]

    def __init__(self, session=None, *args, **kwargs):
        super(SimpleAPIPoltergeistEvent, self).__init__(*args, **kwargs)
        if session is not None:
            self.session = session

        # Log in and get token

    async def poltergeist_login(self):
        url = self.poltergeist_url + '/login'

        login = {
            'email': POLTERGEIST_LOGIN,
            'password': POLTERGEIST_PASSWORD
        }
        self.session = aiohttp.ClientSession()
        response = await self.session.post(
            url, data=json.dumps(login), headers=self.api_header
        )

        if response.status == 200:
            r = await response.json()
            if 'jwt' in r:
                self.bearer_token = r['jwt']
                # Add the token to default header
                self.api_header['Authorization'] = 'Bearer {}'.format(
                    self.bearer_token
                )
            return True
        else:
            logging.warning('Bad connection to poltergeist code {}'.format(
                response.status_code
            )
            )
        return False

    async def check_trigger(self, *args, **kwargs):
        if 'hunter_position' in kwargs:
            hunter_position = kwargs['hunter_position']
            # Is the hunter's position intersecting with any trigger points?
            for event in self.trigger_points:
                if hunter_position.intersects(event['geometry']):
                    # We're in an event position, send api call.
                    await self.trigger(
                        hunter_position=hunter_position,
                        event=event
                    )
                    return True
        return False

    async def trigger(self, *args, **kwargs):
        # hunter_position = kwargs['hunter_position']
        event = kwargs['event']
        await self.poltergeist_call(event['call_type'],
                                    event['uri'],
                                    data=event['json']
                                    )
        self.triggered = True
        return True

    async def poltergeist_call(self, call_type,
                               uri,
                               headers=None,
                               data=None):
        """ Make rest api call to poltergeist"""
        if not self.session:
            await self.poltergeist_login()
        if not headers:
            headers = self.api_header
        try:

            if data is None:
                response = await self.session.request(call_type, uri,
                                                      headers=headers)
            else:
                response = await self.session.request(call_type, uri,
                                                      headers=headers,
                                                      data=json.dumps(data)
                                                      )

            return response
        except asyncio.CancelledError as cancelled:
            logging.debug('api call {} cancelled'.format(cancelled))
        return False


# r, g, b = (111, 121, 131)
# packed = int('%02x%02x%02x' % (r, g, b), 16)

class LightBulbPoltergeistEvent(SimpleAPIPoltergeistEvent):
    light = None
    light_on = False
    light_location = None
    effect_range = 5000

    def __init__(self, *args, **kwargs):
        super(LightBulbPoltergeistEvent, self).__init__()
        if 'light_location' in kwargs:
            self.light_location = kwargs['light_location']
        self.light = SmartBulb(BULB_IP)

    async def check_trigger(self, *args, **kwargs):
        if 'hunter_position' in kwargs:
            hunter_position = kwargs['hunter_position']
            # get the plug 1 (radio) status and wattage
            # if on and 0 (radio has been turned off)
            if self.light_on is not True:
                response = await self.poltergeist_call(
                    'get',
                    PLUG_1_URI + '/properties/on'
                )
                r = await response.json()
                print(r)
                pdb.set_trace()
                if r['on'] == True:
                    response = await self.poltergeist_call(
                        'get',
                        PLUG_1_URI + '/properties/instantaneousPower'
                    )
                    r = await response.json()
                    wattage = r['instantaneousPower']
                    if wattage == 0:
                        # Turn on light
                        self.trigger()
            elif self.light_on is True:
                # Light is on, change brightness for position
                distance = hunter_position.distance(self.light_location)
                brightness = (1 - (distance / self.effect_range)) * 100
                self.light.brightness = brightness
        await asyncio.sleep(0.2)
        return True

    async def trigger(self, *args, **kwargs):
        # hunter_position = kwargs['hunter_position']
        # hsv = colorsys.rgb_to_hsv(0.0,0.0,0.8)
        # conver to int!
        # light.hsv=(hsv[0]*360,hsv[1]*100,hsv[2]*100)
        self.light.brightness = 50
        return True


class SymposiumHunter(ProximityDevice):
    """ Demo device for sharing.  Will integrate some of the REST stuff  later
    if needed in main classes.
    """
    # hed = {'Authorization': 'Bearer ' + auth_token}
    bearer_token = ''

    poltergeist_url = 'https://ghost-hunt.mozilla-iot.org'
    poltergeist_events = None

    api_header = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }
    session = None

    # Event triggers for poltergeist effects
    # simple trigger placed here for now, may evolve into their
    # own classes for more complex events.
    poltergeist_things = [
        # Turn on the radio plug
        {'id': 0,
         'geometry': Point(0, 0).buffer(500),
         'call_type': 'put',
         'uri': poltergeist_url + '/things/zwave-c83406e1-4/properties/on',
         'json': {'on': True},
         }
    ]

    def __init__(self, *args, **kwargs):
        super(SymposiumHunter, self).__init__(*args, **kwargs)
        self.poltergeist_events = [
            SimpleAPIPoltergeistEvent()
        ]

    # Log in and get token
    async def poltergeist_login(self):
        url = self.poltergeist_url + '/login'

        login = {
            'email': POLTERGEIST_LOGIN,
            'password': POLTERGEIST_PASSWORD
        }
        self.session = aiohttp.ClientSession()
        response = await self.session.post(
            url, data=json.dumps(login), headers=self.api_header
        )

        if response.status == 200:
            r = await response.json()
            if 'jwt' in r:
                self.bearer_token = r['jwt']
                # Add the token to default header
                self.api_header['Authorization'] = 'Bearer {}'.format(
                    self.bearer_token
                )
            return True
        else:
            logging.warning('Bad connection to poltergeist code {}'.format(
                response.status_code
            )
            )
        return False

    def device_startup_tasks(self):
        super(SymposiumHunter, self).device_startup_tasks()
        # self.poltergeist_login()
        return True

    async def poltergeist_call(self, call_type,
                               uri,
                               headers=None,
                               data=None):
        """ Make rest api call to poltergeist"""
        if not self.session:
            await self.poltergeist_login()
        if not headers:
            headers = self.api_header
        try:

            if data is None:
                response = await self.session.request(call_type, uri,
                                                      headers=headers)
            else:
                response = await self.session.request(call_type, uri,
                                                      headers=headers,
                                                      data=json.dumps(data)
                                                      )
            r = await response.text()
            print(r)
            return response
        except asyncio.CancelledError as cancelled:
            logging.debug('api call {} cancelled'.format(cancelled))
        return False

    async def uwb_pos_updated(self, new_position):
        """For the demo we're going to check the new position
        against our event triggers, and call the poltergeist as
        necessary"""
        hunter_position = Point(float(new_position['position']['x']),
                                float(new_position['position']['y']), 0)
        # Is the hunter's position intersecting with any trigger points?
        # for thing in self.poltergeist_things:
        #     if hunter_position.intersects(thing['geometry']):
        #         # We're in an event position, send api call.
        #         await self.poltergeist_call(thing['call_type'],
        #                                     thing['uri'],
        #                                     data=thing['json']
        #                                     )        

        for event in self.poltergeist_events:
            await event.check_trigger(
                hunter_position=hunter_position
            )
        return True




def main():
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        hunter = SymposiumHunter(loop, executor,
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
            hunter.bootup()
        except KeyboardInterrupt:
            print('Interrupted')
            hunter.shutdown()
        finally:
            loop.close()
            hunter.microbit_serial.close()


if __name__ == '__main__':
    main()
