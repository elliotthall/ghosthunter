import radar
# Diagnostic/ demo for the pimicro radar
device = None


def demo_init():
    hunt_context = {}
    device = radar.PiMicroRadarCartesian_RSSI(hunt_context)
    device.serial_address = '/dev/cu.usbmodem14522'


def demo_sweep():
    print "Begin sweep"
    device.init_detection()


if __name__ == '__main__':
    demo_init()
    demo_sweep()
