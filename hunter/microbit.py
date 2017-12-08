import logging
import serial
import asyncio
import serial_asyncio

from .ble import HunterBLE


class HunterMicrobit(HunterBLE):
    """
    Bluetooth Hunter using attached Micro:Bit as an interface
    """
    serial_address = '/dev/ttyACM0'