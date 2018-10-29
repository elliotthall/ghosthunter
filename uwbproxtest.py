import hunter.peripherals.uwb.uart as uwb
import time
import serial

uwb_serial_address = '/dev/ttyACM0'
#uwb_serial_address = '/dev/tty.usbmodem1451'
uwb_serial = serial.Serial(uwb_serial_address, 115200, timeout=3)
#uwb.dwm_reset(uwb_serial)

while True:
    time.sleep(2)
    pos = uwb.dwm_serial_get_loc(uwb_serial)
    print("{}\n".format(pos['anchors']))
#print("Position:\n{}\n\nAnchors:\n{}".format(pos['position'],pos['anchors']))
uwb_serial.close()
