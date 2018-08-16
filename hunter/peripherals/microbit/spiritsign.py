import ghosthunter
import microbit

def hunt(pi_msg):
        """ The device's main function, such as radar ping, radio etc
        The default function provides test inputs and diagnostics
        """
        x = 0
        y = 0
        # pixels = []
        result = None
        if microbit.button_a.is_pressed() and \
                microbit.button_b.is_pressed():
            microbit.sleep(500)
            microbit.display.clear()
            while True:            
                dx = 0
                dy = 0
                if microbit.button_a.is_pressed() and \
                microbit.button_b.is_pressed():
                    break  
                if microbit.button_a.is_pressed():
                    microbit.display.set_pixel(x, y, 9)
                else:
                    if "N" in ghosthunter.get_lean():
                        dy = -1
                    if "S" in ghosthunter.get_lean():
                        dy = 1
                    if "E" in ghosthunter.get_lean():
                        dx = 1
                    if "W" in ghosthunter.get_lean():
                        dx = -1
                    if dx !=0 or dy !=0:
                        if microbit.display.get_pixel(x, y) != 9:
                            microbit.display.set_pixel(x, y, 0)
                        if x+dx <= 4 and x+dx >=0:
                            x += dx
                        if y+dy <= 4 and y+dy >=0:
                            y += dy  
                        if microbit.display.get_pixel(x, y) != 9:
                            microbit.display.set_pixel(x, y, 5)
                microbit.sleep(100)
            sign = ""
            if microbit.display.get_pixel(x, y) != 9:
                microbit.display.set_pixel(x, y, 0)
            for ly in range(0,5):
                for lx in range(0,5):
                    sign += str(microbit.display.get_pixel(lx, ly))
                if ly != 4:
                    sign += ":"
            print(sign)
            result = ghosthunter.decode_spiritsign(sign)
        return result
        
        
        
def display_result(result):
    microbit.display.clear()
    microbit.display.scroll(result,delay=200)

def begin_hunting():        
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
    if ghosthunter.startup(microbit.Image.CONFUSED):
        begin_hunting()