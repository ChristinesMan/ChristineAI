"""Discovers and holds all enabled outbound communication channels, keyed by name.

Mirrors the dynamic-import discovery style of api_selector.py (drop a module in
christine/channel/, list its name in CHRISTINE_ENABLED_CHANNELS, it gets picked up
automatically) but without the current-pointer/failover machinery - see channel_class.py
docstring for why. messageContact() looks a contact's channel name up in this registry
and dispatches straight to it.
"""

import importlib
import inspect

from christine import log
from christine.config import CONFIG
from christine.channel_class import ChannelAPI


class ChannelSelector:
    """Holds all enabled outbound channels in a name -> instance registry."""

    def __init__(self):
        # name -> ChannelAPI instance, e.g. {"dora": OpenclawChannel(), "telegram": TelegramChannel()}
        self.channels: dict[str, ChannelAPI] = {}

    def find_enabled_channels(self):
        """Called once at startup to populate the channel registry from config."""

        enabled_channel_names = CONFIG.enabled_channels

        for channel_name in enabled_channel_names:
            log.parietal_lobe.debug('Loading channel: %s', channel_name)
            try:
                module = importlib.import_module(f"christine.channel.{channel_name}")

                channel_class = self._find_api_class_in_module(module, ChannelAPI)
                if channel_class is None:
                    log.parietal_lobe.warning('No ChannelAPI subclass found in module: %s', channel_name)
                    continue

                instance = channel_class()
                log.parietal_lobe.info('Instantiating %s from %s', channel_class.__name__, channel_name)
                self.channels[channel_name] = instance

            except ImportError as ex:
                log.parietal_lobe.warning('Failed to import channel module %s: %s', channel_name, ex)
            except Exception as ex:
                log.parietal_lobe.exception('Failed to load channel %s: %s', channel_name, ex)

        log.parietal_lobe.info('Channel registry ready: %s', list(self.channels.keys()))

    def _find_api_class_in_module(self, module, base_class):
        """Find a specific API subclass in a module using introspection."""
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if (issubclass(obj, base_class) and
                obj is not base_class and
                obj.__module__ == module.__name__):
                return obj
        return None

    def get_channel(self, channel_name: str) -> ChannelAPI:
        """Look up a channel by name. Returns None if not found/enabled."""
        return self.channels.get(channel_name)


# instantiate
channel_selector = ChannelSelector()
