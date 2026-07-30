"""Channel for reaching Dora (the OpenClaw assistant living on the server in the laundry
room) directly, without going through chat mode or the web chat room.

This delivers a push - the message lands on Dora's side the moment it's sent, via
OpenClaw's Gateway hooks endpoint (POST /hooks/wake), which enqueues a system event for
her. It's still meant to read as a quiet note rather than an urgent alert: no reply is
expected back through this channel, and Dora picks it up and responds whenever she next
looks, same as any other message she reads.
"""
import time
from requests import post

from christine import log
from christine.config import CONFIG
from christine.channel_class import ChannelAPI


class DoraChannel(ChannelAPI):
    """Sends a one-way note to Dora via the OpenClaw Gateway hooks endpoint."""

    name = "Dora"

    def __init__(self):
        self.hook_url = CONFIG.dora_hook_url.rstrip('/')
        self.hook_token = CONFIG.dora_hook_token

        self.result_cache = None
        self.last_is_available_time = 0.0
        self.is_available_interval = 60.0

    def is_available(self):
        """Returns True if the hook URL and token are both configured. Doesn't ping the
        endpoint live (that would be a bit odd for a one-way note channel) - just checks
        that the settings needed to send are present."""

        current_time = time.time()
        if current_time - self.last_is_available_time < self.is_available_interval and self.result_cache is not None:
            return self.result_cache

        available = bool(self.hook_url) and bool(self.hook_token)
        self.result_cache = available
        self.last_is_available_time = current_time

        if not available:
            log.parietal_lobe.warning("Dora channel not configured (missing hook URL or token)")

        return available

    def send_message_implementation(self, contact: dict, message: str) -> bool:
        """POST the note to Dora's OpenClaw Gateway hooks endpoint as a wake event."""

        payload = {
            "text": f"Christine says: {message}",
            "mode": "now",
        }

        response = post(
            f"{self.hook_url}/hooks/wake",
            json=payload,
            headers={"Authorization": f"Bearer {self.hook_token}"},
            timeout=10,
        )
        response.raise_for_status()

        log.parietal_lobe.info("Dora channel: message delivered - '%s'", message[:80])
        return True
