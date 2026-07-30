"""Base class for outbound communication channels (contacting people outside the household).

Channels are NOT interchangeable like LLM/STT/TTS backends - a message meant for Openclaw
can't "fail over" to Telegram, it has to reach Openclaw specifically. So unlike api_selector's
current-pointer + failover pattern, channels are looked up by name from a flat registry
(see channel_selector.py) and dispatched directly based on which channel a contact uses.
"""

class ChannelAPI:
    """Base class for an outbound communication channel."""

    name = "ChannelAPI"

    def is_available(self):
        """Returns True if this channel is configured and reachable, False otherwise."""
        raise NotImplementedError("Subclass must implement is_available method")

    def send_message_implementation(self, contact: dict, message: str) -> bool:
        """Send message to the given contact over this channel. contact is one entry from
        contacts.json (name, channel, address, etc). Returns True on success.
        Subclasses implement the actual delivery mechanics here."""
        raise NotImplementedError("Subclass must implement send_message_implementation method")

    def send_message(self, contact: dict, message: str) -> bool:
        """Send a message to a contact over this channel, with logging and error handling.
        No failover here on purpose - see module docstring."""
        from christine import log

        try:
            return self.send_message_implementation(contact, message)
        except Exception as ex:
            log.parietal_lobe.exception("Channel %s failed to send message to %s: %s",
                                       self.name, contact.get('name', '?'), ex)
            return False
