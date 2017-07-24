from devices.radar import PiMicroRadar
import time
# Diagnostic/ demo for the pimicro radar

device = None


def demo_init():
    hunt_context = {}
    print("Pi Microbit Ghost Radar version 0.1")
    device = PiMicroRadar(hunt_context)
    # device.serial_address = '/dev/cu.usbmodem14522'
    # Boot up
    print("Booting up...\n")
    device.bootup()
    return device


# Test Microbit connection
def test_microbit(device):
    print("*** Testing Microbit ***\n")
    init_msg = device.serial.readline()
    print (init_msg)
    data = device.get_microbit_sensor_data()
    if len(data) > 0:
        print("Microbit sensor response\n {}".format(data))
    else:
        print("Have you flashed the data and checked the serial address?")
    print ("Testing Ready...")
    device.serial.write('device_ready=1\n')
    time.sleep(3)
    print ("Testing detection messages")
    device.serial.write('detected=1,clue_heading=3,clue_distance=3\n')
    time.sleep(6)
    device.serial.write('detected=1,clue_heading=90,clue_distance=3\n')
    time.sleep(6)
    device.serial.write('detected=1,clue_heading=180,clue_distance=3\n')
    time.sleep(6)
    device.serial.write('detected=1,clue_heading=270,clue_distance=3\n')
    time.sleep(6)
    device.serial.write('detected=0\n')


# Test BLE/WIFI aerials and parsing
def test_aerials(device):
    print("Testing wifi...\n")
    wifi = device.get_wifi()
    print("Report: {}".format(wifi))
    print("Testing BLE...\n")
    print("Report: {}".format(device.get_ble()))


def test_sweep(device):
    print("Waiting for begin sweep signal")
    # test init
    # pass not detected
    # pass detected
    begin = False
    while not begin:
        response = device.serial.readline()
        if 'begin_detection' in response:
            begin = True
            device.init_detection()

"""
RSSI = TxPower - 10 * n * lg(d)
n = 2 (in free space)
d = 10 ^ ((TxPower - RSSI) / (10 * n))

"""

def ble_demo(device):
    # todo wait for microbit
    # todo if A look for BLE
    ble_report = device.get_ble()
    if ble_report.keys():
        # get first rssi
        rssi = float(ble_report[0]["RSSI"])
        # translate rssi into clue_distance
        if rssi < 0.3:
            clue_distance =1
        elif rssi < 0.6:
            clue_distance = 2
        else:
            clue_distance = 3
        # send to microbit, currently always North
        device.serial.write('detected=1,clue_heading=3,clue_distance={}\n'.format(clue_distance))



    pass

if __name__ == '__main__':
    try:
        device = demo_init()
        # test_microbit(device)
        # test_aerials(device)   
        test_sweep(device)
    finally:
        device.shutdown()
