"""
Core classes for the micro:bit interfaces for ghost hunting devices
Elliott Hall 29/4/2018
"""
import microbit

# Byte codes for communication between
# pi and micro:bit.
"""
MICROBIT_CODES = {
    'ready': \x01,
    # Same as dwm_cfg_get to identify serial connections
    # returns bytecode of device script on micro:bit
    'id': \x08,
    # Different than dwm error code so pi knows this is a micro:bit
    'id_return': \x09,
    'input': \x10,  # A (0), B(1) or both(2) buttons pressed
    # Accelecrometer data
    'acc': 11,
    'toggle_acc': \x15,
    # Light up a single pixel
    'pixel': \x12,
    # Image
    'image': \x13,
    'reset': \x14',
}

BUTTON_A = 0
BUTTON_B = 1
BUTTON_BOTH = 2
"""

""" Base class for all hunter microbits """
loop_delay = 100
# send accelerometer data, can be toggled
send_acc_data_active = False
# millisecond delay between acc sends
send_acc_data_delay = 5

# The integer id of this device's code version
device_id = 1



def send_to_pi(code, value='0'):
    """Send a message to the pi
    in the format CODE::VALUE
    :param code: MICROBIT_CODE
    :param value: value such as button presse, -1 is default for no value
    """
    microbit.uart.write(code + b'\xFF' + bytes(value,'UTF-8'))


def parse_pi_message():
    """Read input from the pi
    Codes here are hard-coded to save memory.  See module docs above
    """
    line = microbit.uart.readline()
    # split line into code :: value
    # code, sep, value = line.rstrip().partition('::')
    code = line[0:1]
    value = line[2:-1]
    # microbit.display.clear()
    # microbit.display.show(code, delay=500)
    # microbit.uart.write(code)
    if code == b'\x14':
        # reset the micro:bit
        microbit.reset()
    elif code == b'\x08':
        send_to_pi(
            b'\x09',
            str(device_id)
        )
    elif code == code == b'\x12':
        # change led
        value = str(value, 'utf-8')
        x, y, bright = value.split(",")
        microbit.set_pixel(int(x), int(y), int(bright))
        microbit.display.show()
    elif code == b'\x13':
        microbit.display.clear()
        value = str(value, 'utf-8')
        image_delay, image_strings = value.split(';;')
        images = []
        for i in image_strings.split(","):
            images.append(microbit.Image(i))
        microbit.display.clear()
        microbit.display.show(images, delay=int(image_delay))
    elif code == b'\x15':
        if int(value) == 0:
            send_acc_data_active = False
        else:
            send_acc_data = True


def send_acc_data():
    """ Get x,y,z accelerometer data
    send to Pi"""
    acc_values = microbit.accelerometer.get_values()
    send_to_pi(
       b'\x11',
        "{},{},{}".format(
            acc_values[0],
            acc_values[1],
            acc_values[2]
        )
    )


def device_listen(send_acc_data=False):
    """ Listen for inputs from microbit
    and messages from pi"""
    if microbit.uart.any():
        # message from pi
        parse_pi_message()

    # check for buttons pressed, send to pi
    if microbit.button_a.is_pressed() and microbit.button_b.is_pressed():
        send_to_pi(b'\x10',
                   '3')
    elif microbit.button_a.is_pressed():
        microbit.display.clear()
        microbit.display.show('A')
        send_to_pi(b'\x10',
                   '1')
    elif microbit.button_b.is_pressed():
        microbit.display.clear()
        microbit.display.show('B')
        send_to_pi(b'\x10',
                   '2')
    # todo timer so we don't spam pi
    if send_acc_data:
        send_acc_data()


def startup():
    """ Perform startup connections
    signal microbit is ready."""
    # serial communicator
    acc_data_delay = 0
    if microbit.uart is None:
        microbit.uart.init(115200)
    send_to_pi(
        b'\x01'
    )
    microbit.display.show(microbit.Image.GHOST)
    while True:
        send_acc_data = False
        if send_acc_data_active:
            if acc_data_delay < send_acc_data_delay:
                acc_data_delay += 1
            else:
                acc_data_delay = 0
                send_acc_data = True
        device_listen(send_acc_data)
        microbit.sleep(loop_delay)


if __name__ == '__main__':
    startup()
