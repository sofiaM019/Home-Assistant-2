"""
Support for Tellstick covers using Tellstick Net.

This platform uses the Telldus Live online service.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/cover.tellduslive/
"""
import logging

from homeassistant.components import cover, tellduslive
from homeassistant.components.cover import CoverDevice
from homeassistant.components.tellduslive.entry import TelldusLiveEntity
from homeassistant.helpers.dispatcher import async_dispatcher_connect

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Telldus Live covers."""
    if discovery_info is None:
        return

    client = hass.data[tellduslive.DOMAIN]
    add_entities(TelldusLiveCover(client, cover) for cover in discovery_info)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up tellduslive sensors dynamically."""
    async def async_discover_cover(device_id):
        """Discover and add a discovered sensor."""
        client = hass.data[tellduslive.DOMAIN]
        async_add_entities([TelldusLiveCover(client, device_id)])

    async_dispatcher_connect(
        hass,
        tellduslive.TELLDUS_DISCOVERY_NEW.format(cover.DOMAIN,
                                                 tellduslive.DOMAIN),
        async_discover_cover,
    )


class TelldusLiveCover(TelldusLiveEntity, CoverDevice):
    """Representation of a cover."""

    @property
    def is_closed(self):
        """Return the current position of the cover."""
        return self.device.is_down

    def close_cover(self, **kwargs):
        """Close the cover."""
        self.device.down()

    def open_cover(self, **kwargs):
        """Open the cover."""
        self.device.up()

    def stop_cover(self, **kwargs):
        """Stop the cover."""
        self.device.stop()
