import microbit
import random

loop_delay = 100
use_acc = False
device_id = 1
lt = 200
debug = False


def send_to_pi(code, value='0'):
    """Send a message to the pi
    in the format CODE::VALUE
    :param code: MICROBIT_CODE
    :param value: value such as button presse, -1 is default for no value
    """
    microbit.uart.write(code + b'\xFF' + bytes(value, 'UTF-8') + b'\n')
    microbit.sleep(100)
    return get_pi_messages()


def display_image(value):
    """Parse a pi string, turn it into a pi LED image
    and display"""
    microbit.display.clear()
    value = str(value, 'utf-8')
    image_delay, image_strings = value.split(';;')
    images = []
    for i in image_strings.split(","):
        images.append(microbit.Image(i))
    microbit.display.clear()
    microbit.display.show(images, delay=int(image_delay))
    return True


def get_lean():
    lean = ""
    if microbit.accelerometer.get_y() <= lt * -1:
        lean = "N"
    elif microbit.accelerometer.get_y() >= lt:
        lean = "S"
    if microbit.accelerometer.get_x() <= lt * -1:
        lean += "W"
    elif microbit.accelerometer.get_x() >= lt:
        lean += "E"
    return lean


def send_device_id():
    send_to_pi(
        b'\x09',
        str(device_id)
    )


def do_pi_command(line):
    """Perform actions based on input from the pi
    Codes here are hard-coded to save memory.  See module docs above
    """
    # split line into code :: value
    code = line[0:1]
    value = line[2:-1]
    if code == b'\x14':
        # reset the micro:bit
        microbit.reset()
    elif code == b'\x08':
        send_device_id()
    elif code == code == b'\x12':
        # change led
        change_led(value)
    elif code == b'\x13':
        display_image(value)


def get_pi_messages():
    if microbit.uart.any():
        # Read uart message
        line = microbit.uart.readline()
        if line[0:1] == '\x18':
            # data
            return line[2:-1]
        else:
            # if it's a command
            do_pi_command(line)
        # else if it's data (scanning etc.) return it
        # so device can parse it
    return None


def startup(startup_image):
    """ Perform startup connections
    signal microbit is ready."""
    # serial communicator
    if microbit.uart is None:
        microbit.uart.init(115200)
    send_to_pi(
        b'\x01'
    )
    microbit.display.show(startup_image)
    return True


#  ************  Main device functions (mirrored in MainDevice) *************

def ghost_scan():
    """ Submit scan to Pi, receive proximity as percentage """
    microbit.display.show(microbit.Image.ALL_CLOCKS, delay=300)
    microbit.display.show(microbit.Image.CLOCK12, delay=300)
    if debug:
        random.random()


def ecto_scan():
    """ Submit scan to Pi, receive proximity as percentage """
    if debug:
        return random.random()


def telegraph_transmit(msg):
    """ Transmit morse to Pi, receive translated letter (or effect result) """
    if debug:
        return do_pi_command(b'\x18\xFFS')
    else:
        response = send_to_pi(b'\xa2', msg)
        if response is not None:
            return str(response, 'utf-8')
        return None


def decode_spiritsign(sign):
    """ receive microbit.Image of sigil, submit string to pi, get decoded
    string """
    if debug:
        return "BOO!"
    else:
        return send_to_pi(b'\x33', sign)


def tune_radio():
    """ ?"""
    if debug:
        return "00000:09000:90909:00090:00000"