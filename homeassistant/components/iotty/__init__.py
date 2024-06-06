"""The iotty integration."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from iottycloud.device import Device

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.config_entry_oauth2_flow import (
    OAuth2Session,
    async_get_config_entry_implementation,
)
from homeassistant.helpers.device_registry import DeviceEntry

from . import coordinator
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SWITCH]

type IottyConfigEntry = ConfigEntry[KnownDevicesData]


@dataclass
class KnownDevicesData:
    """Contains information useful for handling run-time changes in case of added or removed devices."""

    known_devices: set[Device]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up iotty from a config entry."""
    _LOGGER.debug("async_setup_entry entry_id=%s", entry.entry_id)

    implementation = await async_get_config_entry_implementation(hass, entry)
    session = OAuth2Session(hass, entry, implementation)

    data_update_coordinator = coordinator.IottyDataUpdateCoordinator(
        hass, entry, session
    )

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = data_update_coordinator
    entry.runtime_data = KnownDevicesData(set())

    await data_update_coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: ConfigEntry, device_entry: DeviceEntry
) -> bool:
    """Remove a config entry from a device."""
    return True
