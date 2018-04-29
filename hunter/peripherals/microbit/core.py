"""
Core classes for the micro:bit interfaces for ghost hunting devices
Elliott Hall 29/4/2018
"""
import microbit

# Byte codes for communication between
# pi and micro:bit.  Written as pairs to be same as uwb
MICROBIT_CODES = {
    'ready': 1,
    # Same as dwm_cfg_get to identify serial connections
    # returns bytecode of device script on micro:bit
    'id': 8,
    # higher than dwm error code so pi knows this is a micro:bit
    'id_return': 4,
    # A (0), B(1) or both(2) buttons pressed
    'input': 10,
    # Accelecrometer data
    'acc': 11,
    # Light up a single pixel
    'pixel': 12,
    # Image
    'image': 13,
}


class MicrobitHunterController(object):
    """ Base class for all hunter microbits """
    loop_delay = 100
    # send accelerometer data, can be toggled
    send_acc_data_active = True
    # millisecond delay between acc sends
    send_acc_data_delay = 500

    def __init__(self):
        # serial communicator
        if microbit.uart is None:
            microbit.uart.init(115200)

    @staticmethod
    def send_to_pi(code, value='-1'):
        """Send a message to the pi
        in the format CODE::VALUE
        :param code: MICROBIT_CODE
        :param value: value such as button presse, -1 is default for no value"""
        microbit.uart.write('{}::{}\n'.format(
            code,
            value
        ))

    @staticmethod
    def parse_pi_message():
        """Read input from the pi"""
        line = microbit.uart.readline()
        

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
            self.send_to_pi(MICROBIT_CODES['input'],
                            '0')
        elif microbit.button_b.is_pressed():
            self.send_to_pi(MICROBIT_CODES['input'],
                            '1')
        # todo timer so we don't spam pi
        if self.send_acc_data_active:
            self.send_acc_data()



    def startup(self):
        """ Perform startup connections
        signal microbit is ready."""
        self.send_to_pi(
            MICROBIT_CODES['ready']
        )
        while True:
            self.device_listen()
            microbit.sleep(self.loop_delay)


if __name__ == '__main__':
    microhunter = MicrobitHunterController()
    microhunter.startup()
