""" Specific ghost detectors derived from the core library.
These devices are what the student will select and use."""
import asyncio
import concurrent.futures
import hunter.core as hunter_core
import hunter.peripherals.uwb
import logging
from concurrent.futures import CancelledError

class ProximityDevice(hunter_core.HunterUwbMicrobit):
    """Ping-type radar detection.
    Short range(?), 360 degree FOV
    Detect anomalies and use micro:bit LEDs to display
    their rough proximity in a hotter/colder fashion"""

    async def execute_commands(self):
        """
        """
        try:
            while True:
                try:
                    # Are there waiting commands?
                    if len(self.command_queue) > 0:
                        # Parse commands
                        if self.COMMAND_SHUTDOWN in self.command_queue:
                            break
                        elif self.COMMAND_TRIGGER in self.command_queue:
                            self.command_queue.remove(self.COMMAND_TRIGGER)
                            self.trigger()
                    await asyncio.sleep(0.1)
                except CancelledError:
                    logging.debug("execute_commands cancelled")
                    break
        finally:
            logging.debug("Stopping main loop")
        self.cancel_events()
        return True



