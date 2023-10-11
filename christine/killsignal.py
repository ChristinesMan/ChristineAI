"""
Handles exiting the script gracefully in response to a kill signal

Taken from:
https://stackoverflow.com/questions/18499497/how-to-process-sigterm-signal-gracefully
"""

import signal


class GracefulKiller:
    """
    Kills gracefully. Are you okay, honey?
    """

    kill_now = False

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, *_):
        """
        Set the variable used by the killer
        """
        self.kill_now = True
