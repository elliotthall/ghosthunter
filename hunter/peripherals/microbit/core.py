"""
Core classes for the micro:bit interfaces for ghost hunting devices
Elliott Hall 29/4/2018
"""
import microbit


# Byte codes for communication between
# pi and micro:bit.
MICROBIT_CODES = {
    'ready': 1,
    # Same as dwm_cfg_get to identify serial connections
    # returns bytecode of device script on micro:bit
    'id': 8,
    # Different than dwm error code so pi knows this is a micro:bit
    'id_return': 0x09,
    'input': 10, # A (0), B(1) or both(2) buttons pressed
    # Accelecrometer data
    'acc': 11,
    'toggle_acc': 14,
    # Light up a single pixel
    'pixel': 12,
    # Image
    'image': 13,
    'reset': 14,
}

BUTTON_A = 0
BUTTON_B = 1
BUTTON_BOTH = 2

class MicrobitHunterController(object):
    """ Base class for all hunter microbits """
    loop_delay = 100
    # send accelerometer data, can be toggled
    send_acc_data_active = False
    # millisecond delay between acc sends
    send_acc_data_delay = 5
    acc_data_delay = 0
    # The integer id of this device's code version
    device_id = 1

    def __init__(self):
        # serial communicator
        if microbit.uart is None:
            microbit.uart.init(115200)

    @staticmethod
    def send_to_pi(code, value='-1'):
        """Send a message to the pi
        in the format CODE::VALUE
        :param code: MICROBIT_CODE
        :param value: value such as button presse, -1 is default for no value
        """
        microbit.uart.write('{}::{}\n'.format(
            code,
            value
        ))

    def parse_pi_message(self):
        """Read input from the pi"""
        line = microbit.uart.readline()
        # split line into code :: value
        code, sep, value = line.rstrip().partition('::')
        if code == MICROBIT_CODES['reset']:
            # reset the micro:bit
            microbit.reset()
        elif code == MICROBIT_CODES['id']:
            self.send_to_pi(
                MICROBIT_CODES['id_return'],
                str(self.device_id)
            )
        elif code == MICROBIT_CODES['pixel']:
            # change led
            x, y, bright = value.split(",")
            microbit.set_pixel(int(x), int(y), int(bright))
            microbit.display.show()
        elif code == MICROBIT_CODES['image']:
            # display image(s)
            # Format is delay;;image1,image 2 etc.
            images = []
            image_delay, image_strings = value.split(';;')
            for i in image_strings.split(","):
                images.append(microbit.Image(i))
            microbit.display.clear()
            microbit.display.show(images, delay=image_delay)
        elif code == MICROBIT_CODES['toggle_acc']:
            if int(value) == 0:
                self.send_acc_data_active = False
            else:
                self.send_acc_data = True

    def send_acc_data(self):
        """ Get x,y,z accelerometer data
        send to Pi"""
        acc_values = microbit.accelerometer.get_values()
        self.send_to_pi(
            MICROBIT_CODES['acc'],
            "{},{},{}".format(
                acc_values[0],
                acc_values[1],
                acc_values[2]
            )
        )

    def device_listen(self):
        """ Listen for inputs from microbit
        and messages from pi"""
        if microbit.uart.any():
            # message from pi
            self.parse_pi_message()

        # check for buttons pressed, send to pi
        if microbit.button_a.is_pressed() and microbit.button_b.is_pressed():
            self.send_to_pi(MICROBIT_CODES['input'],
                            '2')
        elif microbit.button_a.is_pressed():
            microbit.display.clear()
            microbit.display.show('A')
            self.send_to_pi(MICROBIT_CODES['input'],
                            '0')
        elif microbit.button_b.is_pressed():
            microbit.display.clear()
            microbit.display.show('B')
            self.send_to_pi(MICROBIT_CODES['input'],
                            '1')
        # todo timer so we don't spam pi
        if self.send_acc_data_active:
            if self.acc_data_delay < self.send_acc_data_delay:
                self.acc_data_delay += 1
            else:
                self.acc_data_delay = 0
                self.send_acc_data()

    def startup(self):
        """ Perform startup connections
        signal microbit is ready."""
        self.send_to_pi(
            MICROBIT_CODES['ready']
        )
        microbit.display.show(microbit.Image.GHOST)
        while True:
            self.device_listen()
            microbit.sleep(self.loop_delay)


if __name__ == '__main__':
    microhunter = MicrobitHunterController()
    microhunter.startup()
