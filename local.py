import os
"""" 
The local settings for the hunter device
"""
# Url to the hunt websocket
HUNT_URL = ''
HUNT_DETECTION_URI = ''

"""Poltergeist login """
POLTERGEIST_LOGIN = 'elliott.hall@kcl.ac.uk'
POLTERGEIST_PASSWORD = 'Kgb5EbUDge69'

# Toggle for testing websocket components, defaulted to skip
SKIP_WEBSOCKET  = os.getenv('SKIP_WEBSOCKET', True)