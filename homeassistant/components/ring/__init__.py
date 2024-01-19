"""Support for Ring Doorbell/Chimes."""
from __future__ import annotations

from functools import partial
import logging

import ring_doorbell

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import APPLICATION_NAME, CONF_TOKEN, __version__
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .const import (
    DOMAIN,
    PLATFORMS,
    RING_API,
    RING_DEVICES,
    RING_DEVICES_COORDINATOR,
    RING_NOTIFICATIONS_COORDINATOR,
)
from .coordinator import RingDataCoordinator, RingNotificationsCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a config entry."""

    def token_updater(token):
        """Handle from sync context when token is updated."""
        hass.loop.call_soon_threadsafe(
            partial(
                hass.config_entries.async_update_entry,
                entry,
                data={**entry.data, CONF_TOKEN: token},
            )
        )

    auth = ring_doorbell.Auth(
        f"{APPLICATION_NAME}/{__version__}", entry.data[CONF_TOKEN], token_updater
    )
    ring = ring_doorbell.Ring(auth)

    coordinator = RingDataCoordinator(hass, ring)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        RING_API: ring,
        RING_DEVICES: ring.devices(),
        RING_DEVICES_COORDINATOR: coordinator,
        RING_NOTIFICATIONS_COORDINATOR: RingNotificationsCoordinator(hass, ring),
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Ring entry."""
    if not await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        return False

    hass.data[DOMAIN].pop(entry.entry_id)

    if len(hass.data[DOMAIN]) != 0:
        return True

    # Last entry unloaded, clean up service
    hass.services.async_remove(DOMAIN, "update")

    return True


async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: ConfigEntry, device_entry: dr.DeviceEntry
) -> bool:
    """Remove a config entry from a device."""
    return True
