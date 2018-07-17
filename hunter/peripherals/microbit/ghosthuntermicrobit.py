"""
Elliott Hall 29/4/2018
Core classes for the micro:bit interfaces for ghost hunting devices


Common behaviour:

1. Startup
I'd use this to introduce them to some very basic issues around embedded
computing, like making sure the hardware is all connected and ready.  Logic
mostly, not much exposed code.

2. Begin scan
This would start the main function of the device.  As an example in my
simple radar device, it would need to tell the pi that it wants to scan and
pass some parameters.  For others it might turn on the accelerometer if
that's being used.

3. Parse scan results
The Pi would tell the micro:bit what it's found, and this function should be
able to handle the messages we tell them to decide what needs to happen.

4. Display results
Passed from 3 and where I think they can have the most freedom.  We can help
them with a few templates, and then encourage them to change the display to
customise it on their own.

5. Main function loop
This function is the heart of the device, and should listen for inputs from
the mico:bit (buttons, accelerometer) as well as the bytecode messages from
the pi over the uart.  I think this would be exposed in a very limited way
so they could work with looping and decision trees, something like:
if button_a_pressed:
   scan()
if pi_message:
   result = parse_pi_message(pi_message)
   (result would be human readable so they could use it for display etc.)
   if 'FOUND' in result:
     etc.


Current variants:

Ghost Radar 0.2
Long range, low precision detection using hot/cold interface


Ectoscope Version 0.1

A short range, detection-based device to locate ectoplasmic 'trails'
and follow them



"""
import microbit

# Byte codes for communication between
# pi and micro:bit.
# Note: DWM = Decawave UWB radio
"""

"""


class MicrobitHunter():
    """
    Base class for all microbit hunters
    base version is thin interface for pi to do testing/debugging
    but is overwritten for other variants

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
    'toggle_gesture': \x16,
    'gesture': \x17,
    'data':\x18
}

BUTTON_A = 0
BUTTON_B = 1
BUTTON_BOTH = 2
    """

    loop_delay = 100
    # send accelerometer data, can be toggled
    send_acc_data_active = False
    send_gesture_data_active = False
    # millisecond delay between acc sends
    send_acc_data_delay = 5

    # The integer id of this device's code version
    # used for verifying device builds
    device_id = 1

    @staticmethod
    def send_to_pi(code, value='0'):
        """Send a message to the pi
        in the format CODE::VALUE
        :param code: MICROBIT_CODE
        :param value: value such as button presse, -1 is default for no value
        """
        microbit.uart.write(code + b'\xFF' + bytes(value, 'UTF-8') + b'\n')

    def send_device_id(self):
        MicrobitHunter.send_to_pi(
            b'\x09',
            str(self.device_id)
        )

    @staticmethod
    def change_led(value):
        """Change a microbit led based on pi instruction"""
        value = str(value, 'utf-8')
        x, y, bright = value.split(",")
        microbit.set_pixel(int(x), int(y), int(bright))
        microbit.display.show()
        return True

    @staticmethod
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

    def do_pi_command(self, line):
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
            self.send_device_id()
        elif code == code == b'\x12':
            # change led
            MicrobitHunter.change_led(value)
        elif code == b'\x13':
            MicrobitHunter.display_image(value)
        elif code == b'\x15':
            # Toggle sending acc data
            if int(value) == 0:
                self.send_acc_data_active = False
            else:
                self.send_acc_data_active = True
        elif code == b'\x16':
            # Toggle sending gesture data
            if int(value) == 0:
                self.send_gesture_data_active = False
            else:
                self.send_gesture_data_active = True

    @staticmethod
    def send_acc_data():
        """ Get x,y,z accelerometer data
        send to Pi"""
        # acc_values = microbit.accelerometer.get_values()
        MicrobitHunter.send_to_pi(
            b'\x11',
            MicrobitHunter.get_acc_data()
        )

    @staticmethod
    def get_acc_data():
        """Get data from accelerometer and return it
        :return: String with acc data in format x, y, z
        """
        acc_values = microbit.accelerometer.get_values()
        return "{},{},{}".format(
            acc_values[0],
            acc_values[1],
            acc_values[2]
        )

    @staticmethod
    def device_listen(send_acc_data_now=False):
        """ Listen for inputs from microbit
        and messages from pi"""
        if microbit.uart.any():
            # message from pi
            MicrobitHunter.do_pi_command()

    def startup(self):
        """ Perform startup connections
        signal microbit is ready."""
        # serial communicator
        acc_data_delay = 0
        if microbit.uart is None:
            microbit.uart.init(115200)
        MicrobitHunter.send_to_pi(
            b'\x01'
        )
        microbit.display.show(microbit.Image.GHOST)


    def get_pi_messages(self):
        if microbit.uart.any():
            # Read uart message
            line = microbit.uart.readline()
            if  line[0:1] == '\x18':
                # data
                return line[2:-1]
            else:
                # if it's a command
                self.do_pi_command(line)
            # else if it's data (scanning etc.) return it
            # so device can parse it
        return None

    @staticmethod
    def get_microbit_input(acc_input_active, acc_gesture_active):
        """
        Get buttons, gesture and acc data from the microbit and return
        it.
        Currently static but could be modified to be expose to students
        :param acc_input_active is accelerometer input toggled?
        :type bool
        :param acc_gesture_active return microbit gestures
        :type bool

        :return: dict containing inputs, None if none
        """
        inputs = {}
        # check for buttons pressed, send to pi
        if microbit.button_a.is_pressed() and microbit.button_b.is_pressed():
            inputs[b'\x10'] = 3
        elif microbit.button_a.is_pressed():
            # microbit.display.clear()
            # microbit.display.show('A')
            inputs[b'\x10'] = 1
        elif microbit.button_b.is_pressed():
            # microbit.display.clear()
            # microbit.display.show('B')
            inputs[b'\x10'] = 2
        # # todo timer so we don't spam pi
        # if send_acc_data_now:
        #     MicrobitHunter.send_acc_data()
        if acc_input_active:
            # get the accelerometer data
            inputs[b'\x11'] = MicrobitHunter.get_acc_data()
        if acc_gesture_active:
            inputs[b'\x17'] = microbit.accelerometer.current_gesture()
        if len(inputs) > 0:
            return inputs
        else:
            return None


    def hunt(self):
        """ The device's main function, such as radar ping, radio etc"""
        pass

    def main_device_loop(self):
        """
        The heartbeat of the ghost detector, this function
        brings together all others in a single event loop.

        """
        while True:
            # 1. Listen for message from Pi
            pi_msg = self.get_pi_messages()
            # 2. Get inputs from Micro:bit
            input = self.get_microbit_input(
                self.send_acc_data_active,
                self.send_gesture_data_active
            )

            # 3. Perform actions based on 1 and 2

            # 4. Display results

            send_acc_data = False
            if self.send_acc_data_active:
                if acc_data_delay < self.send_acc_data_delay:
                    acc_data_delay += 1
                else:
                    acc_data_delay = 0
                    send_acc_data = True
            MicrobitHunter.device_listen(send_acc_data)
            microbit.sleep(self.loop_delay)


if __name__ == '__main__':
    hunter = MicrobitHunter()
    hunter.startup()
