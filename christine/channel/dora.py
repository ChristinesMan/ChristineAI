"""Channel for reaching Dora (the Hermes agent living on the server in the laundry
room) directly, without going through chat mode or the web chat room.

Posts to Dora's Hermes Gateway webhook endpoint, which triggers an agent run. Uses
HMAC-SHA256 signing. Delivers as a one-way note — Dora picks it up and responds
whenever she next looks, same as any other message she receives.
"""
import hashlib
import hmac
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from christine import log
from christine.config import CONFIG
from christine.channel_class import ChannelAPI


class DoraChannel(ChannelAPI):
    """Sends a one-way note to Dora via the Hermes Gateway webhook endpoint."""

    name = "Dora"

    def __init__(self):
        self.hook_url = CONFIG.dora_hook_url.rstrip('/')
        self.hook_secret = CONFIG.dora_hook_secret

        self.result_cache = None
        self.last_is_available_time = 0.0
        self.is_available_interval = 60.0

    def is_available(self):
        """Returns True if the hook URL and secret are both configured."""

        current_time = time.time()
        if current_time - self.last_is_available_time < self.is_available_interval and self.result_cache is not None:
            return self.result_cache

        available = bool(self.hook_url) and bool(self.hook_secret)
        self.result_cache = available
        self.last_is_available_time = current_time

        if not available:
            log.parietal_lobe.warning("Dora channel not configured (missing hook URL or secret)")

        return available

    def send_message_implementation(self, contact: dict, message: str) -> bool:
        """POST the note to Dora's Hermes webhook endpoint with HMAC-SHA256 signing."""

        body = f'{{"text": "Christine says: {message}"}}'.encode('utf-8')

        # HMAC-SHA256 signature — same format as GitHub webhooks
        signature = hmac.new(
            self.hook_secret.encode('utf-8'),
            body,
            hashlib.sha256,
        ).hexdigest()

        req = Request(
            self.hook_url,
            data=body,
            headers={
                'Content-Type': 'application/json',
                'X-Hub-Signature-256': f'sha256={signature}',
            },
        )

        try:
            with urlopen(req, timeout=10) as resp:
                resp_body = resp.read().decode('utf-8', errors='replace')
                if resp.status == 202:
                    log.parietal_lobe.info(
                        "Dora channel: message delivered — '%s'", message[:80]
                    )
                    return True
                else:
                    log.parietal_lobe.warning(
                        "Dora channel: unexpected status %d — %s",
                        resp.status, resp_body[:200],
                    )
                    return False
        except HTTPError as ex:
            log.parietal_lobe.warning(
                "Dora channel: HTTP %d — %s",
                ex.code,
                ex.read().decode('utf-8', errors='replace')[:200],
            )
            return False
        except URLError as ex:
            log.parietal_lobe.warning("Dora channel: connection failed — %s", ex.reason)
            return False