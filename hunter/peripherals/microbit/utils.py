# Byte codes for communication between
# pi and micro:bit.
MICROBIT_CODES = {
    'ready': 1,
    # Same as dwm_cfg_get to identify serial connections
    # returns bytecode of device script on micro:bit
    'id': 8,
    # Different than dwm error code so pi knows this is a micro:bit
    'id_return': 0x09,
    'input': 10, # A (0), B(1) or both(2) buttons pressed
    # Accelecrometer data
    'acc': 11,
    'toggle_acc': 14,
    # Light up a single pixel
    'pixel': 12,
    # Image
    'image': 13,
    'reset': 14,
}

BUTTON_A = 0
BUTTON_B = 1
BUTTON_BOTH = 2