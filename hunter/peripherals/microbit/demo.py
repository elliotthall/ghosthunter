import ghosthunter
import microbit

ghosthunter.use_acc = True

def startup():
        """ Perform startup connections
        signal microbit is ready."""
        # serial communicator
        if microbit.uart is None:
            microbit.uart.init(115200)
        ghosthunter.send_to_pi(
            b'\x01'
        )        
        microbit.display.show(microbit.Image.GHOST)
        return True
        
def hunt(pi_msg):
        """ The device's main function, such as radar ping, radio etc
        The default function provides test inputs and diagnostics
        """
        # Buttons
        if microbit.button_a.is_pressed() and \
                microbit.button_b.is_pressed():
            microbit.display.clear()
            microbit.display.show('C')
        elif microbit.button_a.is_pressed():
            microbit.display.clear()
            microbit.display.show('A')
        elif microbit.button_b.is_pressed():
            microbit.display.clear()
            microbit.display.show('B')
        if ghosthunter.use_acc:
            gesture_image = None
            if ghosthunter.get_lean() == "W":
                gesture_image = microbit.Image.ARROW_W            
            elif microbit.accelerometer.get_x() >= 200:
                gesture_image = microbit.Image.ARROW_E
            if microbit.accelerometer.get_y() <= -200:
                gesture_image = microbit.Image.ARROW_N
            elif microbit.accelerometer.get_y() >= 200:
                gesture_image = microbit.Image.ARROW_S
            if gesture_image is not None:
                microbit.display.clear()
                microbit.display.show(gesture_image)
        return 0
        
def display_result(result):
    pass

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
            display_result(result)
            microbit.sleep(ghosthunter.loop_delay)
            

if __name__ == '__main__':
    if startup():
        begin_hunting()