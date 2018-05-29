import asyncio
import concurrent.futures
import logging
import pdb
import aiohttp
import requests
import json
from shapely.geometry import Point

from hunter.devices import ProximityDevice
from local import (POLTERGEIST_LOGIN, POLTERGEIST_PASSWORD)

logging.basicConfig(
    level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')
logging.getLogger(__name__).addHandler(logging.NullHandler())
"""
/things output

{'name': 'room1-plug2', 'type': 'smartPlug', 'description': '', 'href': 
'/things/zwave-c83406e1-3', 'properties': {'on': {'type': 'boolean', 'href': 
'/things/zwave-c83406e1-3/properties/on'}, 'instantaneousPower': {'type': 
'number', 'unit': 'watt', 'href': 
'/things/zwave-c83406e1-3/properties/instantaneousPower'}, 'voltage': {
'type': 'number', 'unit': 'volt', 'href': 
'/things/zwave-c83406e1-3/properties/voltage'}, 'current': {'type': 
'number', 'unit': 'ampere', 'href': 
'/things/zwave-c83406e1-3/properties/current'}}, 'actions': {}, 'events': {
}, 'links': [{'rel': 'properties', 'href': 
'/things/zwave-c83406e1-3/properties'}, {'rel': 'actions', 'href': 
'/things/zwave-c83406e1-3/actions'}, {'rel': 'events', 'href': 
'/things/zwave-c83406e1-3/events'}, {'rel': 'alternate', 'mediaType': 
'text/html', 'href': '/things/zwave-c83406e1-3'}, {'rel': 'alternate', 
'href': 'wss://ghost-hunt.mozilla-iot.org/things/zwave-c83406e1-3'}]}, 
{'name': 'room1-plug1', 'type': 'smartPlug', 'description': '', 'href': 
'/things/zwave-c83406e1-4', 'properties': {'on': {'type': 'boolean', 'href': 
'/things/zwave-c83406e1-4/properties/on'}, 'instantaneousPower': {'type': 
'number', 'unit': 'watt', 'href': 
'/things/zwave-c83406e1-4/properties/instantaneousPower'}, 'voltage': {
'type': 'number', 'unit': 'volt', 'href': 
'/things/zwave-c83406e1-4/properties/voltage'}, 'current': {'type': 
'number', 'unit': 'ampere', 'href': 
'/things/zwave-c83406e1-4/properties/current'}}, 'actions': {}, 'events': {
}, 'links': [{'rel': 'properties', 'href': 
'/things/zwave-c83406e1-4/properties'}, {'rel': 'actions', 'href': 
'/things/zwave-c83406e1-4/actions'}, {'rel': 'events', 'href': 
'/things/zwave-c83406e1-4/events'}, {'rel': 'alternate', 'mediaType': 
'text/html', 'href': '/things/zwave-c83406e1-4'}, {'rel': 'alternate', 
'href': 'wss://ghost-hunt.mozilla-iot.org/things/zwave-c83406e1-4'}]}, 
{'name': 'room1-lamp', 'type': 'dimmableColorLight', 'description': '', 
'href': '/things/virtual-things-2', 'properties': {'color': {'type': 
'string', 'href': '/things/virtual-things-2/properties/color'}, 'level': {
'type': 'number', 'unit': 'percent', 'href': 
'/things/virtual-things-2/properties/level'}, 'on': {'type': 'boolean', 
'href': '/things/virtual-things-2/properties/on'}}, 'actions': {}, 'events': 
{}, 'links': [{'rel': 'properties', 'href': 
'/things/virtual-things-2/properties'}, {'rel': 'actions', 'href': 
'/things/virtual-things-2/actions'}, {'rel': 'events', 'href': 
'/things/virtual-things-2/events'}, {'rel': 'alternate', 'mediaType': 
'text/html', 'href': '/things/virtual-things-2'}, {'rel': 'alternate', 
'href': 'wss://ghost-hunt.mozilla-iot.org/things/virtual-things-2'}]}]
"""


class SymposiumHunter(ProximityDevice):
    """ Demo device for sharing.  Will integrate some of the REST stuff  later
    if needed in main classes.
    """
    # hed = {'Authorization': 'Bearer ' + auth_token}
    bearer_token = ''

    poltergeist_url = 'https://ghost-hunt.mozilla-iot.org'

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
                pdb.set_trace()
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
        for thing in self.poltergeist_things:
            if hunter_position.intersects(thing['geometry']):
                # We're in an event position, send api call.                
                await self.poltergeist_call(thing['call_type'],
                                            thing['uri'],
                                            data=thing['json']
                                            )
        return True

    # h = header
    # h
    # r = requests.get(url, headers=h)

    # put to poltergeist thing


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
