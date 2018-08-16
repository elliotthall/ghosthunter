"""
Scripts to be flashed to ghost hunter microbits
Split into separate files due to Micro:bit low memory

Elliott Hall 29/4/2018
Core classes for the micro:bit interfaces for ghost hunting devices


Common behaviour:

1. Startup
I'd use this to introduce them to some very basic issues around embedded
computing, like making sure the hardware is all connected and ready.  Logic
mostly, not much exposed code.

2. Begin scan
This would start the main function of the device.  As an example in my
simple radar device, it would need to tell the pi that it wants to scan and
pass some parameters.  For others it might turn on the accelerometer if
that's being used.

3. Parse scan results
The Pi would tell the micro:bit what it's found, and this function should be
able to handle the messages we tell them to decide what needs to happen.

4. Display results
Passed from 3 and where I think they can have the most freedom.  We can help
them with a few templates, and then encourage them to change the display to
customise it on their own.

5. Main function loop
This function is the heart of the device, and should listen for inputs from
the mico:bit (buttons, accelerometer) as well as the bytecode messages from
the pi over the uart.  I think this would be exposed in a very limited way
so they could work with looping and decision trees, something like:
if button_a_pressed:
   scan()
if pi_message:
   result = parse_pi_message(pi_message)
   (result would be human readable so they could use it for display etc.)
   if 'FOUND' in result:
     etc.


 MICROBIT_CODES = {
    'ready': \x01,
    # Same as dwm_cfg_get to identify serial connections
    # returns bytecode of device script on micro:bit
    'id': \x08,
    # Different than dwm error code so pi knows this is a micro:bit
    'id_return': \x09,
    'input': \x10,  # A (0), B(1) or both(2) buttons pressed
    # Accelecrometer data
    'acc': 11,
    'toggle_acc': \x15,
    # Light up a single pixel
    'pixel': \x12,
    # Image
    'image': \x13,
    'reset': \x14',
    'toggle_gesture': \x16,
    'gesture': \x17,
    'data':\x18
}

BUTTON_A = 0
BUTTON_B = 1
BUTTON_BOTH = 2


Current variants:

Ghost Radar 0.2
Long range, low precision detection using hot/cold interface


Ectoscope Version 0.1

A short range, detection-based device to locate ectoplasmic 'trails'
and follow them


Spirit Telegraph
CODE = {'A': '.-',     'B': '-...',   'C': '-.-.',
        'D': '-..',    'E': '.',      'F': '..-.',
        'G': '--.',    'H': '....',   'I': '..',
        'J': '.---',   'K': '-.-',    'L': '.-..',
        'M': '--',     'N': '-.',     'O': '---',
        'P': '.--.',   'Q': '--.-',   'R': '.-.',
     	'S': '...',    'T': '-',      'U': '..-',
        'V': '...-',   'W': '.--',    'X': '-..-',
        'Y': '-.--',   'Z': '--..',

        '0': '-----',  '1': '.----',  '2': '..---',
        '3': '...--',  '4': '....-',  '5': '.....',
        '6': '-....',  '7': '--...',  '8': '---..',
        '9': '----.'
        }

"""
