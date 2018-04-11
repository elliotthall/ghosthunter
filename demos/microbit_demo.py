import microbit
import neopixel
from random import randint
# A pure microbit demo to show some of the possible effects we can acheive with it
# A sandbox to mess around with the breakout board


class MicrobitDemo():

    # Radar sweep
    def initdetectionanimation(self):
        microbit.display.clear()
        ping = [microbit.Image("00000:00000:00300:00000:00000"),
                microbit.Image("00000:07770:07070:07770:00000"),
                microbit.Image("99999:90009:90009:90009:99999")]
        microbit.display.show(ping, loop=False, delay=200)
        microbit.display.clear()

    # Spin the fan motor very slowly to simulate a sweeping antenna
    def antenna_sweep(self, speed):
        microbit.pin0.write_analog(speed)
        microbit.sleep(1000)
        microbit.pin0.write_analog(0)

    # use a neopixel strip for hot/cold pulse
    def led_pulse(self, np):
        strength = randint(0, len(np)-1)
        red = randint(0, 30)
        green = randint(0, 30)
        blue = randint(0, 30)
        # random example of reading
        for pixel_id in range(0, strength):
            np[pixel_id] = (red+strength, green+strength, blue+strength)
            np.show()
            microbit.sleep(100)
        # fade down
        microbit.sleep(1000)
        for pixel_id in range(strength, 0, -1):
            np[pixel_id] = (0, 0, 0)
            np.show()
            microbit.sleep(100)
            
def radio_pulse(strength):
    level = 4 - strength
    microbit.display.set_pixel(2,level,9)
    level += 1
    if level > 4:
        level = 4
    microbit.display.set_pixel(1,level,9)
    microbit.display.set_pixel(3,level,9)
    level += 1
    if level > 4:
        level = 4
    microbit.display.set_pixel(0,level,9)
    microbit.display.set_pixel(4,level,9)

demo = MicrobitDemo()
#np = neopixel.NeoPixel(microbit.pin1, 10)
#np.clear()
#microbit.pin0.write_analog(0)

while True:
    if microbit.button_a.is_pressed():
        demo.initdetectionanimation()
        found = [microbit.Image("00000:00000:00700:00000:00000"),
            microbit.Image("00000:07770:07770:07770:00000")]
        microbit.display.show(found, loop=False, delay=200)
        microbit.sleep(500)
        microbit.display.clear()
        #demo.antenna_sweep(randint(50, 300))
        
    if microbit.button_b.is_pressed():
        for max in range(0, 4):
            for x in range(0,5):
                vary = randint(0,1)
                lessmore = randint(0,1)
                if lessmore == 0:
                    max += vary
                else:
                    max -= vary
                if max < 0:
                    max=0
                if max > 4:
                    max = 4
                radio_pulse(max)
                microbit.sleep(100)
                microbit.display.clear()
