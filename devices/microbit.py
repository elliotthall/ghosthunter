import microbit
# Ghost Radar for the Micro:bit verion 0.5
# todo add readthedocs link
# Elliott Hall


class RadarMicrobit():

    # Whether the device is ready to begin detection
    detection_ready = False

    def __init__(self):
        # serial communicator
        if microbit.uart is None:
            microbit.uart.init(115200)

    def initdetectionanimation(self):
        microbit.display.clear()
        ping = [microbit.Image("00000:00000:00300:00000:00000"),
                microbit.Image("00000:07770:07070:07770:00000"),
                microbit.Image("99999:90009:90009:90009:99999")]
        microbit.display.show(ping, loop=False, delay=200)
        microbit.display.clear()

    def showready(self):
        microbit.display.set_pixel(2, 2, 9)

    def showblip(self, images, distance):
        microbit.display.clear()
        for x in range(distance):
            microbit.display.show(microbit.Image(images[x]))
            microbit.sleep(500)
            microbit.display.clear()
        microbit.sleep(2000)

    def compass_display(self, heading, distance):
        if heading < 45 or heading > 315:
            # North
            foundN = ["00000:00500:00300:00000:00000",
                      "00000:07770:00300:00000:00000",
                      "99999:09990:00900:00000:00000"]
            self.showblip(foundN, distance)
        elif heading > 45 and heading < 135:
            # East
            foundE = ["00000:00000:00350:00000:00000",
                      "00000:00070:00770:00070:00000",
                      "00009:00099:00999:00099:00009"]

            self.showblip(foundE, distance)
        elif heading > 135 and heading < 235:
            # South
            foundS = [
                "00000:00000:00300:00500:00000",
                "00000:00000:00300:07770:00000",
                "00000:00000:00900:09990:99999"
            ]
            self.showblip(foundS, distance)
        elif heading > 235 and heading < 315:
            # West
            foundW = [
                "00000:00000:05300:00000:00000",
                "00000:07000:07700:07000:00000",
                "90000:99000:99900:99000:90000"
            ]
            self.showblip(foundW, distance)

    def not_detected(self, pi_message):
        microbit.display.show(microbit.Image.NO)
        microbit.sleep(2000)
        microbit.display.clear()

    def detected(self, pi_message):
        # Clue heading
        clue_heading = 0
        clue_distance = 0
        for response in pi_message.split(','):
            if 'clue_heading' in response:
                print(response)
                clue_heading = int(response.split('=')[1])
            if 'clue_distance' in response:
                clue_distance = int(response.split('=')[1])
        if clue_distance > 0 and clue_heading > 0:
            self.compass_display(clue_heading, clue_distance)
        else:
            microbit.uart.write(
                'ERROR: Bad detection data {}\n'.format(pi_message))
        # if hunt_response.get('ghost_heading'):
        #     microbit.display.show(microbit.Image.GHOST)
        #     microbit.sleep(1000)
        #     self.compass_display(int(hunt_response.get('clue_heading')),
        #                          int(hunt_response.get('clue_distance')))
        # microbit.display.clear()

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
        # Decode to string
        try:
            if 'request_sensor_data' in pi_message:
                self.send_sensor_data()
            elif 'device_ready' in pi_message:
                self.detection_ready = True
                self.showready()
            elif 'detected=0' in pi_message:
                # no detection
                self.not_detected(pi_message)
            elif 'detected=1' in pi_message:
                # Clue found, run detection animation
                self.detected(pi_message)
            elif 'init_detection' in pi_message:
                # Tell the Microbit to begin detection
                self.initdetectionanimation()
        except ValueError as ve:
            microbit.display.scroll(str(ve))

    def send_begin_detection(self):
        microbit.uart.write('begin_detection=1\n')

    def device_listen(self):
        if microbit.uart.any():
            pi_message = str(microbit.uart.readall()).replace(
                '\\n', '').replace('\'', '')
            self.parse_pi_message(pi_message)

        if microbit.button_a.is_pressed():
            if self.detection_ready:
                self.detection_ready = False
                self.initdetectionanimation()
                self.send_begin_detection()
        if microbit.button_b.is_pressed():
            microbit.compass.calibrate()


radar = RadarMicrobit()

microbit.uart.write("READY\n")
while True:
    radar.device_listen()
    microbit.sleep(100)
