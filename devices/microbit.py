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

pingimage = [ping1, ping2, ping3]


def initdetectionanimation():
    microbit.display.show(pingimage, loop=False, delay=200)
    microbit.display.clear()

def compass_display(heading)
  if heading <= 23 and heading >= 292:
    # North
    microbit.display.show(microbit.Image.ARROW_N)
  elif heading >= 23 and heading <= 77:
    # North East
    microbit.display.show(microbit.Image.ARROW_NE)



def detected(hunt_response):
    # print("Detected!")
    # Clue heading
    if hunt_response.get('clue_heading'):
        clue_heading = hunt_response.get('clue_heading')
        compass_display(int(clue_heading))
    if hunt_response.get('ghost_heading'):
        microbit.display.show(microbit.Image.GHOST)
        microbit.sleep(1000)
        compass_display(int(hunt_response.get('clue_heading')))    
    microbit.display.clear()    

# Pass all sensor data over the serial connection


def send_sensor_data():
    a, b = microbit.button_a.was_pressed(), microbit.button_b.was_pressed()
    if microbit.compass.is_calibrated():
        heading = microbit.compass.heading()
    else:
        heading = -1
    # todo may add accelerometer
    # microbit.accelerometer.get_values()
    print("button_a={0},button_b={1},heading={2},\
      accelerometer=[{3},{4},{5},{6}]\n".format(
        a, b, heading,
        microbit.accelerometer.get_x(), microbit.accelerometer.get_y(),
        microbit.accelerometer.get_z(),
        microbit.accelerometer.current_gesture()
    ))


def parse_pi_message(pi_message):
    if 'detected' in pi_message:
        # Clue found, run detection animation
        hunt_response = {}
        detected(hunt_response)
        microbit.sleep(1000)
        microbit.display.clear()
    if 'init_detection' in pi_message:
        initdetectionanimation()


microbit.uart.init(115200)
while True:
    if microbit.uart.any():
        pi_message = microbit.uart.readline()
        parse_pi_message(pi_message)
        
    # if microbit.button_a.is_pressed():
    #     initdetectionanimation()
    #     hunt_response = {}
    #     detected(hunt_response)
    #     microbit.sleep(1000)
    #     microbit.display.clear()
    if microbit.button_b.is_pressed():
        microbit.compass.calibrate()
    send_sensor_data()
    microbit.sleep(100)
