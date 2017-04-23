import microbit

ping1 = microbit.Image("00000:"
                       "00000:"
                       "00300:"
                       "00000:"
                       "00000")

ping2 = microbit.Image("00000:"
                       "07770:"
                       "07070:"
                       "07770:"
                       "00000")

ping3 = microbit.Image("99999:"
                       "90009:"
                       "90009:"
                       "90009:"
                       "99999")

foundN1 = microbit.Image("00000:"
                         "00500:"
                         "00300:"
                         "00000:"
                         "00000")

foundN2 = microbit.Image("00000:"
                         "07770:"
                         "00300:"
                         "00000:"
                         "00000")

foundN3 = microbit.Image("99999:"
                         "09990:"
                         "00900:"
                         "00000:"
                         "00000")

foundE1 = microbit.Image("00000:"
                         "00000:"
                         "00350:"
                         "00000:"
                         "00000")

foundE2 = microbit.Image("00000:"
                         "00070:"
                         "00770:"
                         "00070:"
                         "00000")

foundE3 = microbit.Image("00009:"
                         "00099:"
                         "00999:"
                         "00099:"
                         "00009")

foundS1 = microbit.Image("00000:"
                         "00000:"
                         "00300:"
                         "00500:"
                         "00000")

foundS2 = microbit.Image("00000:"
                         "00000:"
                         "00300:"
                         "07770:"
                         "00000")

foundS3 = microbit.Image("00000:"
                         "00000:"
                         "00900:"
                         "09990:"
                         "99999")

foundW1 = microbit.Image("00000:"
                         "00000:"
                         "05300:"
                         "00000:"
                         "00000")

foundW2 = microbit.Image("00000:"
                         "07000:"
                         "07700:"
                         "07000:"
                         "00000")

foundW3 = microbit.Image("90000:"
                         "99000:"
                         "99900:"
                         "99000:"
                         "90000")

foundN = [foundN1, foundN2, foundN3]
foundE = [foundE1, foundE2, foundE3]
foundS = [foundS1, foundS2, foundS3]
foundW = [foundW1, foundW2, foundW3]

pingimage = [ping1, ping2, ping3]


class RadarMicrobit():

    # Whether the device is ready to begin detection
    detection_ready = False

    def __init__(self):
        # serial communicator
        if microbit.uart is None:
            microbit.uart.init(115200)

    def initdetectionanimation(self):
        microbit.display.show(pingimage, loop=False, delay=200)
        microbit.display.clear()

    def compass_display(self, heading, distance):
        if heading < 45 or heading > 315:
            # North
            microbit.display.show(foundN[distance])
        elif heading > 45 and heading < 135:
            # East
            microbit.display.show(foundE[distance])
        elif heading > 135 and heading < 235:
            # South
            microbit.display.show(foundS[distance])
        elif heading > 235 and heading < 315:
            # West
            microbit.display.show(foundW[distance])

    def not_detected(self, hunt_response):
        no_hits = microbit.Image(width=5, height=5)
        no_hits.set_pixel(5, 5, 1)

    def detected(self, hunt_response):
        # print("Detected!")
        # Clue heading
        if hunt_response.get('clue_heading'):
            clue_heading = hunt_response.get('clue_heading')
            self.compass_display(int(clue_heading),
                                 int(hunt_response.get('clue_distance')))
            microbit.sleep(1000)
        if hunt_response.get('ghost_heading'):
            microbit.display.show(microbit.Image.GHOST)
            microbit.sleep(1000)
            self.compass_display(int(hunt_response.get('clue_heading')),
                                 int(hunt_response.get('clue_distance')))
        microbit.display.clear()

    # Pass all sensor data over the serial connection

    def send_sensor_data(self):
        a, b = microbit.button_a.was_pressed(), microbit.button_b.was_pressed()
        if microbit.compass.is_calibrated():
            heading = microbit.compass.heading()
        else:
            heading = -1
        # microbit.accelerometer.get_values()
        sensor_string = ("b_a={0},b_b={1},heading={2}"
                         .format(a, b, heading))
        # accelerometer for possible future use

        sensor_string += (",acc_x={}"
                          ",acc_y={}"
                          ",acc_z={}"
                          .format(
                              microbit.accelerometer.get_x(),
                              microbit.accelerometer.get_y(),
                              microbit.accelerometer.get_z()
                          ))
        if (len(microbit.accelerometer.current_gesture()) > 0):
            sensor_string += (",acc_g={}".format(
                microbit.accelerometer.current_gesture()))
        sensor_string += "\n"
        microbit.uart.write(sensor_string)

    def parse_pi_message(self, pi_message):
        if 'request_sensor_data' in pi_message:
            self.send_sensor_data()
        if 'device_ready' in pi_message:
            self.detection_ready = True
        if 'detected=0' in pi_message:
            # no detection
            self.not_detected(pi_message)
        elif 'detected=1' in pi_message:
            # Clue found, run detection animation
            self.detected(pi_message)
        if 'init_detection' in pi_message:
            # Tell the Microbit to begin detection
            self.initdetectionanimation()       
        microbit.display.clear()

    def send_begin_detection(self):
        microbit.uart.write('begin_detection=1')

    def device_listen(self):
        if microbit.uart.any():
            pi_message = microbit.uart.readline()
            self.parse_pi_message(pi_message)
        if microbit.button_a.is_pressed():
            if self.detection_ready:
                self.detection_ready = False
                self.initdetectionanimation()
                self.send_begin_detection()
        if microbit.button_b.is_pressed():
            microbit.compass.calibrate()


radar = RadarMicrobit()
radar.detection_ready = True
demo_headings = [3, 90, 180, 270]
demo_distances = [0, 1, 2]


def display_test():
    for heading in demo_headings:
        for distance in demo_distances:
            radar.detected(
                {'clue_heading': heading, 'clue_distance': distance})
            microbit.sleep(500)


while True:
    radar.device_listen()
    microbit.sleep(100)
