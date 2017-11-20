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

    def __init__(self, sv1, sv2, np):
        self.sv1= sv1
        self.sv2 = sv2
        self.np = np
        
    def ready(self):
        microbit.display.show('?', wait=False)

    def reset(self):
        # Reset the antenna and the screen
        microbit.display.clear()
        self.antenna_min()
        self.ready()
        
    # Min (farthest away) antenna settings
    def antenna_min(self):
        self.adjust_antenna_sweep(100,80,1)
        
    def antenna_max(self):
        self.adjust_antenna_sweep(0,180,4)
        
    def diagnostic(self):
        self.antenna_min()
        microbit.sleep(500)
        for strength in range(100, 0, -20):
            self.adjust_antenna_sweep(strength)
            microbit.sleep(500)

    # Strength in 0-100
    def adjust_antenna_sweep(self, angle_1,angle_2, neo_strength):        
        demo.initdetectionanimation()        
        demo.led_pulse(neo_strength)
        self.sv1.write_angle(angle_1)
        self.sv2.write_angle(angle_2)        
        microbit.sleep(1000)
        demo.led_fade(neo_strength)
        self.ready()

        
    # use a neopixel strip for hot/cold pulse
    def led_pulse(self, strength):        
        red = randint(0, 30)
        green = randint(0, 30)
        blue = randint(0, 30)
        # random example of reading
        for pixel_id in range(0, strength +1 ):
            self.np[pixel_id] = (red+strength, green+strength, blue+strength)
            self.np.show()
            microbit.sleep(100)
        self.np.show()
     
    # fade down
    def led_fade(self, strength):
        for pixel_id in range(strength, 0, -1):
            self.np[pixel_id] = (0, 0, 0)
            self.np.show()
            microbit.sleep(100)
        self.np.clear()

    # Radar 'blip' animation
    def initdetectionanimation(self):
        microbit.display.clear()
        ping = [microbit.Image("00000:00000:00300:00000:00000"),
                microbit.Image("00000:07770:07070:07770:00000"),
                microbit.Image("99999:90009:90009:90009:99999")]
        microbit.display.show(ping, loop=False, delay=200)
        microbit.display.clear()

# set up the servo pins
sv1 = Servo(microbit.pin1, min_us=1000, max_us=2000)
sv2 = Servo(microbit.pin2, min_us=1000, max_us=2000)
np = neopixel.NeoPixel(microbit.pin0, 5)
demo = MicrobitServoDemo(sv1, sv2, np)
demo.reset()
demo.np.show()

while True:
    # Check for messages from pi
    """if microbit.uart.any():
            pi_message = str(microbit.uart.readall()).replace(
                '\\n', '').replace('\'', '')
            if 'RSSI' in pi_message:
                # get rssi
         
       rssi = float(pi_message.replace('RSSI=',''))
                # transform rssi into number for antenna spread
     """           
    
    if microbit.button_a.is_pressed():
        
        demo.antenna_max()
    elif microbit.button_b.is_pressed():
        demo.antenna_min()
    