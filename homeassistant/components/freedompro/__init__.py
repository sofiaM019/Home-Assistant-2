"""Support for freedompro."""
import asyncio
from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import COORDINATOR, DOMAIN, UNDO_UPDATE_LISTENER
from .utils import get_list, get_states

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    "light",
]


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Freedompro component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Freedompro from a config entry."""
    api_key = entry.data[CONF_API_KEY]

    coordinator = FreedomproDataUpdateCoordinator(hass, api_key)
    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    undo_listener = entry.add_update_listener(update_listener)

    hass.data[DOMAIN][entry.entry_id] = {
        COORDINATOR: coordinator,
        UNDO_UPDATE_LISTENER: undo_listener,
    }

    for platform in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
            ]
        )
    )
    if unload_ok:
        hass.data[DOMAIN][entry.entry_id] = {}

    return unload_ok


async def update_listener(hass, config_entry):
    """Update listener."""
    await hass.config_entries.async_reload(config_entry.entry_id)


class FreedomproDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Freedompro data API."""

    def __init__(self, hass, api_key):
        """Initialize."""
        self._hass = hass
        self._api_key = api_key
        self._devices = None

        update_interval = timedelta(minutes=1)
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=update_interval)

    async def _async_update_data(self):
        if self._devices is None:
            result = await get_list(self._hass, self._api_key)
            if result["state"]:
                self._devices = result["devices"]
            else:
                raise UpdateFailed()

        result = await get_states(self._hass, self._api_key)

        devices = []
        for device in self._devices:
            dev = next(
                (dev for dev in result if dev["uid"] == device["uid"]),
                None,
            )
            if dev is not None:
                if "state" in dev:
                    devices.append(
                        {
                            "uid": device["uid"],
                            "name": device["name"],
                            "type": device["type"],
                            "characteristics": device["characteristics"],
                            "state": dev["state"],
                        }
                    )
                else:
                    devices.append(
                        {
                            "uid": device["uid"],
                            "name": device["name"],
                            "type": device["type"],
                            "characteristics": device["characteristics"],
                        }
                    )
        return devices
