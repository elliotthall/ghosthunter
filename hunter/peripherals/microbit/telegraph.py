import ghosthunter
import microbit


def hunt(pi_msg):
    msg = None
    result = None
    # button_a - dot, button_b -dash, button_c start/submit
    if microbit.button_a.is_pressed() and \
                microbit.button_b.is_pressed():
        # Begin transmission
        msg = ""
        microbit.sleep(500)
        microbit.display.clear()
        while True:
            key = None
            if microbit.button_a.is_pressed() and \
                microbit.button_b.is_pressed():
                break            
            elif microbit.button_a.is_pressed():
                key = "0"
            elif microbit.button_b.is_pressed():
                key = "1"
            if key is not None:
                microbit.display.clear()
                msg += key                
                for index,r in enumerate(msg):
                    if r == "0":
                        microbit.display.set_pixel(index, 2, 9)
                    elif r == "1":
                        microbit.display.set_pixel(index, 2, 9)
                        microbit.display.set_pixel(index, 1, 9)
                        microbit.display.set_pixel(index, 3, 9)                    
                microbit.sleep(300)
            microbit.sleep(100)
        if msg is not None:
            for x in range(0,2):
                microbit.display.show([
                    microbit.Image("00900:09990:00900:00900:09990"),
                    microbit.Image("09990:09990:09990:00900:09990")
                ],delay=200)
            result = ghosthunter.telegraph_transmit(msg)
    return result
        
def display_result(result):    
    microbit.display.clear()
    microbit.display.show(result)
    
    
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
                display_result(result)
            microbit.sleep(ghosthunter.loop_delay)
            

if __name__ == '__main__':
    if ghosthunter.startup(microbit.Image("00900:09990:00900:00900:09990")):
        begin_hunting()