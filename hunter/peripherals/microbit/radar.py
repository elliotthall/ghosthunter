import ghosthunter
import microbit
import math


def startup(startup_image):
    """ Perform startup connections
    signal microbit is ready."""
    # serial communicator
    if microbit.uart is None:
        microbit.uart.init(115200)
    ghosthunter.send_to_pi(
        b'\x01'
    )
    microbit.display.show(startup_image)
    return True


def hunt(pi_msg):
    result = None
    # if button_a pressed
    if microbit.button_a.is_pressed():
        # send to pi for scan begin
        result = ghosthunter.ghost_scan()
    # return result
    return result


def display_result(result):
    """light up leds based on ping/total range"""
    microbit.display.clear()
    if result == 0:
        microbit.display.show(microbit.Image.SAD)
    else:
        leds = int(
            math.ceil(
                result * 25
            )
        )
        if leds == 0:
            # minimum reading of one
            leds = 1
        canvas = [['0'] * 5 for x in range(0, 5)]
        for x in range(0, leds):
            row = int(math.floor(x / 5))
            canvas[row][x - row * 5] = '9'
            # no delay
        image = ""
        for y in range(0, 5):
            image += "".join(canvas[y])
            if y != 4:
                image += ":"
        microbit.display.show(microbit.Image(image))


def begin_hunting():
    """
    The heartbeat of the ghost detector, this function
    brings together all others in a single event loop.
    """
    while True:
        # 1. Listen for push message from Pi
        pi_msg = ghosthunter.get_pi_messages()
        # 3. Perform main action
        result = hunt(pi_msg)
        # 4. Display results
        if result is not None:
            display_result(float(result))
        microbit.sleep(ghosthunter.loop_delay)


if __name__ == '__main__':
    if startup(microbit.Image.DIAMOND):
        begin_hunting()