import ghosthunter
import microbit
import math

debug = True


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
        result = ghosthunter.ecto_scan()
    # return result
    return result


def display_result(result):
    """light up leds based on scan, 5 levels"""
    # clunky, written this way to preserve memory
    microbit.display.clear()
    for x in range(1, int(math.ceil(result * 5))):
        if x == 1:
            scan = "00000:00000:00000:00000:00900"
        elif x == 2:
            scan = "00000:00000:00000:00900:00900"
        elif x == 3:
            scan = "00000:00000:09990:00900:00900"
        elif x == 4:
            scan = "00000:99999:09990:00900:00900"
        elif x == 5:
            scan = "99999:99999:09990:00900:00900"
        microbit.display.clear()
        microbit.display.show(microbit.Image(scan))
        microbit.sleep(200)


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
            display_result(int(result))
        microbit.sleep(ghosthunter.loop_delay)


if __name__ == '__main__':
    if startup(microbit.Image.TRIANGLE_LEFT):
        begin_hunting()    
