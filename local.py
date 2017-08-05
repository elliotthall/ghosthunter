import os
"""" 
The local settings for the hunter device
"""
# Url to the hunt websocket
HUNT_URL = ''
HUNT_DETECTION_URI = ''
# Navigator Path
NAVIGATOR_URL = ''
# Toggle for testing websocket components, defaulted to skip
SKIP_WEBSOCKET  = os.getenv('SKIP_WEBSOCKET', True)