import microbit
from hunter.pi_microbit import HunterMicrobit

"""
Microbit Diagnostic
Elliott Hall

For testing communication between the pi and microbit
"""


def initdetectionanimation():
    microbit.display.clear()
    ping = [microbit.Image("00000:00000:00300:00000:00000"),
            microbit.Image("00000:07770:07070:07770:00000"),
            microbit.Image("99999:90009:90009:90009:99999")]
    microbit.display.show(ping, loop=False, delay=200)
    microbit.display.clear()


def parse_pi_message(pi_message):
    try:
        if HunterMicrobit.PING in pi_message:
            microbit.uart.write("PONG\n")
        elif HunterMicrobit.ECHO in pi_message:
            microbit.uart.write(pi_message.replace('ECHO', '').lstrip())

    except ValueError as ve:
        microbit.display.scroll(str(ve))


def device_test():
    if microbit.uart.any():
        pi_message = str(microbit.uart.readall()).replace(
            '\\n', '').replace('\'', '')
        parse_pi_message(pi_message)
    if microbit.button_a.is_pressed():
        microbit.uart.write(HunterMicrobit.BUTTON_A_PRESSED)
        initdetectionanimation()
    if microbit.button_b.is_pressed():
        microbit.uart.write(HunterMicrobit.BUTTON_B_PRESSED)
        microbit.display.show(microbit.Image.SMILE)
        microbit.sleep(1000)
        microbit.display.clear()


microbit.uart.init(115200)
microbit.uart.write("READY\n")
microbit.display.show(microbit.Image.HAPPY)
while True:
    device_test()
    microbit.sleep(100)
