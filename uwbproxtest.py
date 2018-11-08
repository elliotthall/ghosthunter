import hunter.peripherals.uwb.uart as uwb
import time
import serial

uwb_serial_address = '/dev/ttyACM0'
#uwb_serial_address = '/dev/tty.usbmodem1451'
uwb_serial = serial.Serial(uwb_serial_address, 115200, timeout=3)
#uwb.dwm_reset(uwb_serial)
x = 0
#time.sleep(5)
while True:
    try:
        pos = uwb.dwm_serial_get_loc(uwb_serial)
        print("\n{}:\nPosition:\n{}\n\nAnchors:\n{}".format(x,pos['position'],pos['anchors']))
        x+=1
        time.sleep(1)
    except KeyboardInterrupt:
        print("Finished")
        break

uwb_serial.close()
