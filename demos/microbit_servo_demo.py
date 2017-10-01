import microbit
import neopixel
from random import randint
# import servo
# A pure microbit demo to show some of the possible effects we can acheive with it
# A sandbox to mess around with the breakout board


class Servo:

    """
    A simple class for controlling hobby servos.

    Args:
        pin (pin0 .. pin3): The pin where servo is connected.
        freq (int): The frequency of the signal, in hertz.
        min_us (int): The minimum signal length supported by the servo.
        max_us (int): The maximum signal length supported by the servo.
        angle (int): The angle between minimum and maximum positions.

    Usage:
        SG90 @ 3.3v servo connected to pin0
        = Servo(pin0).write_angle(90)
    """

    def __init__(self, pin, freq=50, min_us=600, max_us=2400, angle=180):
        self.min_us = min_us
        self.max_us = max_us
        self.us = 0
        self.freq = freq
        self.angle = angle
        self.analog_period = 0
        self.pin = pin
        analog_period = round((1/self.freq) * 1000)  # hertz to miliseconds
        self.pin.set_analog_period(analog_period)

    def write_us(self, us):
        us = min(self.max_us, max(self.min_us, us))
        duty = round(us * 1024 * self.freq // 1000000)
        self.pin.write_analog(duty)
        self.pin.write_digital(0)  # turn the pin off

    def write_angle(self, degrees=None):
        degrees = degrees % 360
        total_range = self.max_us - self.min_us
        us = self.min_us + total_range * degrees // self.angle
        self.write_us(us)


class MicrobitServoDemo():       

    def reset(self):
        # Reset the antenna and the screen
        microbit.display.clear()
        # microbit.pin1.write_analog(0)        
        # sv1.write_angle(self.angle_1)

    def adjust_antenna_sweep(self, servo, angle):
        servo.write_angle(angle)
        
    # use a neopixel strip for hot/cold pulse
    def led_pulse(self, strength):        
        red = randint(0, 30)
        green = randint(0, 30)
        blue = randint(0, 30)
        # random example of reading
        for pixel_id in range(0, strength):
            np[pixel_id] = (red+strength, green+strength, blue+strength)
            np.show()
            microbit.sleep(100)
     
    # fade down
    def led_fade(self, strength):
        for pixel_id in range(strength, 0, -1):
            np[pixel_id] = (0, 0, 0)
            np.show()
            microbit.sleep(100)

    # Radar 'blip' animation
    def initdetectionanimation(self):
        microbit.display.clear()
        ping = [microbit.Image("00000:00000:00300:00000:00000"),
                microbit.Image("00000:07770:07070:07770:00000"),
                microbit.Image("99999:90009:90009:90009:99999")]
        microbit.display.show(ping, loop=False, delay=200)
        microbit.display.clear()

# set up the servo pins
# microbit.pin1.set_analog_period(20)
# microbit.pin2.set_analog_period(20)
sv1 = Servo(microbit.pin1, min_us=1000, max_us=2000)
sv2 = Servo(microbit.pin2, min_us=1000, max_us=2000)
np = neopixel.NeoPixel(microbit.pin0, 5)
demo = MicrobitServoDemo()
demo.reset()

while True:
    # Check for messages from pi
    if microbit.uart.any():
            pi_message = str(microbit.uart.readall()).replace(
                '\\n', '').replace('\'', '')
            if 'RSSI' in pi_message:
                # get rssi
                rssi = float(pi_message.replace('RSSI=',''))
                # transform rssi into number for antenna spread
                
    if microbit.button_a.is_pressed() and microbit.button_b.is_pressed():
        demo.reset()
    elif microbit.button_a.is_pressed():
        strength = randint(0, len(np)-1)
        demo.initdetectionanimation()
        demo.led_pulse(strength)
        demo.adjust_antenna_sweep(sv1, 0)
        demo.adjust_antenna_sweep(sv2, 180)   
        microbit.sleep(1000)
        demo.led_fade(strength)

    elif microbit.button_b.is_pressed():
        demo.initdetectionanimation()
        demo.adjust_antenna_sweep(sv1, 180)
        demo.adjust_antenna_sweep(sv2, 0)
        microbit.sleep(1000)
