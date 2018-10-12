import hunter.peripherals.uwb.uart as uwb
import time
import serial

uwb_serial_address = '/dev/ttyACM0'
uwb_serial = serial.Serial(uwb_serial_address, 115200, timeout=3)
print(uwb.dwm_serial_get_loc(uwb_serial))
uwb_serial.close()