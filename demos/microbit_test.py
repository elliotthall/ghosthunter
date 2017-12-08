import microbit
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
        # Decode to string
        try:
            if 'PING' in pi_message:
                microbit.uart.write("PONG\n")
            elif 'init_detection' in pi_message:
                # Tell the Microbit to begin detection
                # self.initdetectionanimation()
                pass
        except ValueError as ve:
            microbit.display.scroll(str(ve))


def device_test():
        if microbit.uart.any():
            pi_message = str(microbit.uart.readall()).replace(
                '\\n', '').replace('\'', '')
            parse_pi_message(pi_message)
        if microbit.button_a.is_pressed():
            microbit.uart.write("Button A Pressed\n")
            initdetectionanimation()
        if microbit.button_b.is_pressed():
            microbit.uart.write("Button B Pressed\n")


microbit.uart.init(115200)
microbit.uart.write("READY\n")
while True:
    device_test()
    microbit.sleep(100)
