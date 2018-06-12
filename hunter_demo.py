import asyncio
import concurrent.futures
import json
import logging
import pdb
import aiohttp
from shapely.geometry import Point

from hunter.devices import ProximityDevice
from local import (POLTERGEIST_LOGIN, POLTERGEIST_PASSWORD)

logging.basicConfig(
    level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')
logging.getLogger(__name__).addHandler(logging.NullHandler())

POLTERGEIST_URL = 'http://10.0.1.2:8888'
# http://hassbian.local:8123/api/services/switch/turn_off
HA_API_URL = 'http://hassbian.local:8123/api'
HA_ENTITY_PLUG1_1 = \
    "switch" \
    ".wenzhou_tkb_control_system_tz69_smart_energy_plug_in_switch_switch_2"
HA_ENTITY_PLUG1_2 = \
    "switch.wenzhou_tkb_control_system_tz69_smart_energy_plug_in_switch_switch"

PLUG_1_URI = POLTERGEIST_URL + '/things/zwave-c83406e1-4'
BULB_IP = '10.0.1.5'

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
    active = True
    # has it already happened?
    triggered = False
    # Number of times it can happen, -1 for infinite
    num_triggered = 0
    trigger_limit = 1
    # Chain events?
    next_event = None
    next_event_delay = 5

    def __init__(self, *args, **kwargs):
        if 'active' in kwargs:
            self.active = kwargs['active']
        if 'next_event' in kwargs:
            self.next_event = kwargs['next_event']

    async def check_trigger(self, *args, **kwargs):
        """Check if this event should be triggered"""
        pass

    async def trigger_event(self, *args, **kwargs):
        """Do the spooky action at a distance"""
        pass

    async def finish(self, *args, **kwargs):
        """Optional 'big(ish) finish' for an event"""
        pass


class MozillaSimplePoltergeistEvent(PoltergeistEvent):
    """If hunter intersects trigger area, send an API message """
    poltergeist_url = POLTERGEIST_URL

    api_header = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }
    session = None
    login = False
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
        super(MozillaSimplePoltergeistEvent, self).__init__(*args, **kwargs)
        if 'trigger_points' in kwargs:
            self.trigger_points = kwargs['trigger_points']

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
                    self.num_triggered += 1
                    self.active = False
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
        # HACK will improve in real code
        asyncio.sleep(self.next_event_delay)
        self.next_event.active = True
        return True

    async def poltergeist_call(self, call_type,
                               uri,
                               headers=None,
                               data=None):
        """ Make rest api call to poltergeist"""
        if self.session is None:
            if self.login:
                self.session = aiohttp.ClientSession()
            else:
                self.session = aiohttp.ClientSession()
        if not headers:
            headers = self.api_header
        try:
            logging.info('api call {}'.format(
                uri))
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

class LightBulbPoltergeistEvent(PoltergeistEvent):
    light_on = False
    light_location = None
    effect_range = 3000
    finish_range = 500
    api_header = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }
    session = None
    login = False

    def __init__(self, *args, **kwargs):
        super(LightBulbPoltergeistEvent, self).__init__(*args, **kwargs)
        if 'light_location' in kwargs:
            self.light_location = kwargs['light_location']
        if 'light_on' in kwargs:
            self.light_on = kwargs['light_on']

    async def poltergeist_call(self, call_type,
                               uri,
                               headers=None,
                               data=None):
        """ Make rest api call to poltergeist"""
        if self.session is None:
            if self.login:
                self.session = aiohttp.ClientSession()
            else:
                self.session = aiohttp.ClientSession()
        if not headers:
            headers = self.api_header
        try:
            logging.info('api call {} with data {}'.format(
                uri, data
            ))
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

    async def check_trigger(self, *args, **kwargs):
        if self.active and 'hunter_position' in kwargs:
            hunter_position = kwargs['hunter_position']
            # get the plug 1 (radio) status and wattage
            # if on and 0 (radio has been turned off)

            if self.light_on is not True:
                # sensor.wenzhou_tkb_control_system_tz69_smart_energy_plug_in_switch_power_2
                response = await self.poltergeist_call(
                    'get',
                    HA_API_URL +
                    '/states/switch.wenzhou_tkb_control_system_tz69_smart_energy_plug_in_switch_switch',
                )
                r = await response.json()

                if 'state' in r:
                    state = r['state']

                    if 'off' in state:
                        # switch 1 is powered off
                        # data = {
                        #     "entity_id": "light.tplink_light"
                        # }
                        # response = await self.poltergeist_call(
                        #     'post',
                        #     HA_API_URL + '/services/light/turn_on',
                        #     data=data
                        # )
                        data = {
                            "on": True
                        }
                        response = await self.poltergeist_call(
                            'put',
                            POLTERGEIST_URL + '/1/properties/on',
                            data=data
                        )
                        await asyncio.sleep(0.5)
                        self.light_on = True
            elif self.light_on is True:
                # Light is on, toggle flicker
                distance = hunter_position.distance(self.light_location)
                if distance < self.finish_range:
                    # finish event
                    await self.finish(
                        hunter_position=hunter_position,
                    )

                elif distance < self.effect_range:
                    await self.trigger(
                        hunter_position=hunter_position,
                        distance=distance
                    )
                    await asyncio.sleep(0.5)
            else:
                await asyncio.sleep(0.1)
        return True

    async def trigger(self, *args, **kwargs):
        # hunter_position = kwargs['hunter_position']
        # hsv = colorsys.rgb_to_hsv(0.0,0.0,0.8)
        # conver to int!
        # light.hsv=(hsv[0]*360,hsv[1]*100,hsv[2]*100)
        distance = kwargs['distance']
        flicker_data = {
            "flicker": {
                "input": {
                    "num_flickers": 2
                }
            }
        }
        response = await self.poltergeist_call(
            'post',
            POLTERGEIST_URL + '/1/actions',
            data=flicker_data
        )
        # brightness = int(100 - ((distance/self.effect_range) * 100))

        # data = {
        #     "brightness":brightness
        # }
        # response = await self.poltergeist_call(
        #     'put',
        #     POLTERGEIST_URL + '/1/properties/brightness',
        #     data=data
        # )

        return True

    async def finish(self, *args, **kwargs):
        # hsv = colorsys.rgb_to_hsv(0.0, 0.0, 0.8)
        # data = {
        #     "on":False
        # }
        # response = await self.poltergeist_call(
        #     'put',
        #     POLTERGEIST_URL + '/1/properties/on',
        #     data=data
        # )
        data = {"entity_id": HA_ENTITY_PLUG1_1}
        response = await self.poltergeist_call(
            'post',
            HA_API_URL + '/services/switch/turn_off',
            data=data
        )
        data = {
            "play": {
                "input": {
                    "file":
                        "/Users/ehall/projects/ghost/ghosthunt-poltergeist"
                        "/assets/2 spooky 4 me 3.wav"
                }
            }
        }
        response = await self.poltergeist_call(
            'post',
            POLTERGEIST_URL + '/0/actions',
            data=data
        )
        self.active = False
        return True


class SymposiumHunter(ProximityDevice):
    """ Demo device for sharing.  Will integrate some of the REST stuff  later
    if needed in main classes.
    """
    # hed = {'Authorization': 'Bearer ' + auth_token}
    bearer_token = ''
    login = False

    poltergeist_url = 'https://ghost-hunt.mozilla-iot.org'
    poltergeist_events = None

    api_header = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }
    session = None

    def __init__(self, *args, **kwargs):
        super(SymposiumHunter, self).__init__(*args, **kwargs)
        if 'poltergeist_events' in kwargs:
            self.poltergeist_events = kwargs['poltergeist_events']

    # Log in and get token
    async def poltergeist_login(self):
        url = self.poltergeist_url + '/login'

        login = {
            'email': POLTERGEIST_LOGIN,
            'password': POLTERGEIST_PASSWORD
        }
        if self.session is None:
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

        for event in self.poltergeist_events:
            if event.active:
                await event.check_trigger(
                    hunter_position=hunter_position
                )
        return True


def main():
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        detectable_things = {
            0: [
                {'id': 0,
                 'name': 'Stay Puft Marshmallow Man',
                 'geometry': Point(1074, 3521),
                 'level': 0}
            ]
        }
        # Set up the events and room detectables
        plug_trigger_events = [{'id': 0,
                                'geometry': detectable_things[0][0][
                                    'geometry'].buffer(500),
                                'call_type': 'post',
                                'uri': HA_API_URL + '/services/switch/turn_on',
                                'json': {"entity_id": HA_ENTITY_PLUG1_2},
                                }]
        light_location = Point(3366, 3860)

        event_2 = LightBulbPoltergeistEvent(
            light_location=light_location,
            active=False,
            light_on=False
        )

        event_1 = MozillaSimplePoltergeistEvent(
            active=True,
            trigger_points=plug_trigger_events,
            next_event=event_2
        )
        poltergeist_events = [
            event_1,
            event_2
        ]
        hunter = SymposiumHunter(loop, executor,
                                 hunt_url='ws://demos.kaazing.com/echo',
                                 MAC='78:4f:43:6c:cc:0f',
                                 poltergeist_events=poltergeist_events
                                 )
        hunter.detectable_things = detectable_things
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
