import radar
# Diagnostic/ demo for the pimicro radar
device = None


def demo_init():
    hunt_context = {}
    print("Pi Microbit Ghost Radar version 0.1")
    device = radar.PiMicroRadarCartesian_RSSI(hunt_context)
    device.serial_address = '/dev/cu.usbmodem14522'
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

    # Test Detection sweep


def test_sweep():
    print "Begin sweep"
    # test init
    # pass not detected
    # pass detected
    device.init_detection()


if __name__ == '__main__':
    device = demo_init()
    test_microbit(device)
    test_aerials(device)
    test_sweep(device)
    # todo shutdown?
