from devices.radar import PiMicroRadarCartesian_RSSI
import time
# Diagnostic/ demo for the pimicro radar
device = None


def demo_init():
    hunt_context = {}
    print("Pi Microbit Ghost Radar version 0.1")
    device = PiMicroRadarCartesian_RSSI(hunt_context)
    # device.serial_address = '/dev/cu.usbmodem14522'
    # Boot up
    print("Booting up...\n")
    device.bootup()
    return device


# Test Microbit connection
def test_microbit(device):
    print("*** Testing Microbit ***\n")
    data = device.get_microbit_sensor_data()
    if len(data) > 0:
        print("Microbit sensor response\n {}".format(data))
    else:
        print("Have you flashed the data and checked the serial address?")


# Test BLE/WIFI aerials and parsing
def test_aerials(device):
    print("Testing wifi...\n")
    wifi = device.get_wifi()
    print("Report: {}".format(wifi))
    print("Testing BLE...\n")
    print("Report: {}".format(device.get_ble()))


def test_detections(device):
    demo_headings = [3, 90, 180, 270]
    demo_distances = [0, 1, 2]
    print("Testing detected response...\n")
    hunt_response = {'clue_heading': demo_headings[0], 
                     'clue_distance': demo_distances[2]}
    device.detected(hunt_response)
    time.sleep(3)
    print("Testing NOT detected response...\n")
    hunt_response = {}
    device.notdetected(hunt_response)


def test_sweep():
    print("Begin sweep")
    # test init
    # pass not detected
    # pass detected
    device.init_detection()


if __name__ == '__main__':
    device = demo_init()
    test_microbit(device)
    # test_aerials(device)
    test_detections(device)
    # test_sweep(device)
    # todo shutdown?
