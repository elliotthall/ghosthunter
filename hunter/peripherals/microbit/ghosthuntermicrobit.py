"""
Elliott Hall 29/4/2018
Core classes for the micro:bit interfaces for ghost hunting devices


Common behaviour:

1. Startup
I'd use this to introduce them to some very basic issues around embedded computing, like making sure the hardware is all connected and ready.  Logic mostly, not much exposed code.

2. Begin scan
This would start the main function of the device.  As an example in my simple radar device, it would need to tell the pi that it wants to scan and pass some parameters.  For others it might turn on the accelerometer if that's being used.

3. Parse scan results
The Pi would tell the micro:bit what it's found, and this function should be able to handle the messages we tell them to decide what needs to happen.

4. Display results
Passed from 3 and where I think they can have the most freedom.  We can help them with a few templates, and then encourage them to change the display to customise it on their own.

5. Main function loop
This function is the heart of the device, and should listen for inputs from the mico:bit (buttons, accelerometer) as well as the bytecode messages from the pi over the uart.  I think this would be exposed in a very limited way so they could work with looping and decision trees, something like:
if button_a_pressed:
   scan()
if pi_message:
   result = parse_pi_message(pi_message)
   (result would be human readable so they could use it for display etc.)
   if 'FOUND' in result:
     etc.


Current variants:

Ghost Radar 0.2


Ectoscope Version 0.1

A short range, detection-based device to locate ectoplasmic 'trails' and follow them



"""
import microbit

# Byte codes for communication between
# pi and micro:bit.
# Note: DWM = Decawave UWB radio
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
    'toggle_acc': \x14,
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


class MicrobitHunter():
    """
    Base class for all microbit hunters
    base version is thin interface for pi to do testing/debugging
    but is overwritten for other variants
    """

    loop_delay = 100
    # send accelerometer data, can be toggled
    send_acc_data_active = False
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
        microbit.uart.write(code + b'\xFF' + bytes(value, 'UTF-8')+b'\n')


    def parse_pi_message(self):
        """Read input from the pi
        Codes here are hard-coded to save memory.  See module docs above
        """
        line = microbit.uart.readline()
        # split line into code :: value

        code = line[0:1]
        value = line[2:-1]

        if code == b'\x14':
            # reset the micro:bit
            microbit.reset()
        elif code == b'\x08':
            MicrobitHunter.send_to_pi(
                b'\x09',
                str(self.device_id)
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
            global send_acc_data_active
            if int(value) == 0:
                send_acc_data_active = False
            else:
                send_acc_data_active = True

    @staticmethod
    def send_acc_data():
        """ Get x,y,z accelerometer data
        send to Pi"""
        acc_values = microbit.accelerometer.get_values()
        MicrobitHunter.send_to_pi(
           b'\x11',
           "{},{},{}".format(
                acc_values[0],
                acc_values[1],
                acc_values[2]
            )
        )

    @staticmethod
    def device_listen(send_acc_data_now=False):
        """ Listen for inputs from microbit
        and messages from pi"""
        if microbit.uart.any():
            # message from pi
            MicrobitHunter.parse_pi_message()

        # check for buttons pressed, send to pi
        if microbit.button_a.is_pressed() and microbit.button_b.is_pressed():
            MicrobitHunter.send_to_pi(b'\x10','3')
        elif microbit.button_a.is_pressed():
            microbit.display.clear()
            microbit.display.show('A')
            MicrobitHunter.send_to_pi(b'\x10',
                       '1')
        elif microbit.button_b.is_pressed():
            microbit.display.clear()
            microbit.display.show('B')
            MicrobitHunter.send_to_pi(b'\x10',
                       '2')
        # todo timer so we don't spam pi
        if send_acc_data_now:
            MicrobitHunter.send_acc_data()

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
        while True:
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
