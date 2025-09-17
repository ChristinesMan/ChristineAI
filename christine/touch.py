"""
Handles the 5 touch sensors inside head.
"""
import time
from datetime import datetime
from collections import deque

from christine import log
from christine.status import STATE
from christine.parietal_lobe import parietal_lobe
from christine.sleep import sleep


class Touch:
    """
    When Christine gets touched, stuff should happen. That happens here.
    """

    def __init__(self):

        # I want to limit how often messages get sent to the LLM
        self.time_of_last_kiss = time.time()

        # labels for the 5 touch sensors
        self.channel_labels = [
            "Mouth",
            "Left Cheek",
            "Forehead",
            "Right Cheek",
            "Nose"
        ]

        # Track the current state of each sensor (True = touched, False = not touched)
        self.current_touch_state = [False] * 5

        # Track the previous state to detect changes
        self.previous_touch_state = [False] * 5

        # Keep a narrative log of touch events (limited to last 20 events)
        self.touch_narrative = deque(maxlen=20)

        # Minimum time between touch events to avoid spam (in seconds)
        self.touch_cooldown = 0.5

        # Track last touch time for each sensor
        self.last_touch_time = [0] * 5

    def new_data(self, touch_data):
        """
        Called to deliver new data point
        touch_data should be a list of 5 boolean values (True = touched, False = not touched)
        """

        current_time = time.time()
        
        if len(touch_data) != 5:
            log.touch.warning("Expected 5 touch sensor values, got %d", len(touch_data))
            return

        # Update current state
        self.current_touch_state = list(touch_data)

        # Check for changes in each sensor
        for i in range(5):
            # Detect touch start (was not touched, now touched)
            if not self.previous_touch_state[i] and self.current_touch_state[i]:
                # Check cooldown to avoid spam
                if current_time - self.last_touch_time[i] > self.touch_cooldown:
                    self._handle_touch_start(i, current_time)
                    self.last_touch_time[i] = current_time

            # Detect touch end (was touched, now not touched)
            elif self.previous_touch_state[i] and not self.current_touch_state[i]:
                self._handle_touch_end(i, current_time)

        # Update previous state for next comparison
        self.previous_touch_state = self.current_touch_state.copy()

    def _handle_touch_start(self, sensor_index, timestamp):
        """
        Handle when a sensor starts being touched
        """
        sensor_name = self.channel_labels[sensor_index]
        
        log.touch.info("Touch started: %s", sensor_name)
        
        # Add to narrative
        time_str = datetime.fromtimestamp(timestamp).strftime("%H:%M:%S")
        narrative_entry = f"[{time_str}] {sensor_name} touched"
        self.touch_narrative.append(narrative_entry)

        # Special handling for mouth touches (maintaining compatibility)
        if sensor_name == "Mouth":
            if STATE.is_sleeping is False:
                parietal_lobe.mouth_touched()
            
            # Update kiss timing for LLM rate limiting
            self.time_of_last_kiss = timestamp

        # Wake up Christine if she's sleeping
        sleep.wake_up(0.05)

    def _handle_touch_end(self, sensor_index, timestamp):
        """
        Handle when a sensor stops being touched
        """
        sensor_name = self.channel_labels[sensor_index]
        
        log.touch.debug("Touch ended: %s", sensor_name)
        
        # Add to narrative for longer touches (more than 0.5 seconds)
        if timestamp - self.last_touch_time[sensor_index] > 0.5:
            time_str = datetime.fromtimestamp(timestamp).strftime("%H:%M:%S")
            duration = timestamp - self.last_touch_time[sensor_index]
            narrative_entry = f"[{time_str}] {sensor_name} released after {duration:.1f}s"
            self.touch_narrative.append(narrative_entry)

    def get_current_touches(self):
        """
        Get list of currently active touches
        """
        active_touches = []
        for i, is_touched in enumerate(self.current_touch_state):
            if is_touched:
                active_touches.append(self.channel_labels[i])
        return active_touches

    def get_touch_narrative(self, clear_after_read=True):
        """
        Get the current touch narrative as a string
        If clear_after_read is True, clears the narrative after reading
        """
        if not self.touch_narrative:
            return "No recent touch events."
        
        narrative = "\n".join(self.touch_narrative)
        
        if clear_after_read:
            self.touch_narrative.clear()
        
        return narrative

    def get_touch_summary(self):
        """
        Get a summary of current touch state and recent activity
        """
        current_touches = self.get_current_touches()
        
        if current_touches:
            current_status = f"Currently being touched: {', '.join(current_touches)}"
        else:
            current_status = "No current touches"
        
        # Get recent narrative without clearing it
        recent_narrative = self.get_touch_narrative(clear_after_read=False)
        
        return f"{current_status}\nRecent touch events:\n{recent_narrative}"

    def is_being_touched(self):
        """
        Check if any sensor is currently being touched
        """
        return any(self.current_touch_state)

    def time_since_last_touch(self):
        """
        Get time in seconds since any sensor was last touched
        """
        if not self.last_touch_time:
            return float('inf')
        
        return time.time() - max(self.last_touch_time)


# instantiate
touch = Touch()
