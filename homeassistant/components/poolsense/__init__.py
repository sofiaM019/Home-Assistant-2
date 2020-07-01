"""The PoolSense integration."""
import asyncio
from datetime import timedelta
import logging

import async_timeout
from poolsense import PoolSense
from poolsense.exceptions import PoolSenseError

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client, update_coordinator
from homeassistant.helpers.update_coordinator import UpdateFailed

from .const import DOMAIN

PLATFORMS = ["sensor"]

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the PoolSense component."""
    # Make sure coordinator is initialized.
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up PoolSense from a config entry."""
    await get_coordinator(hass, entry)

    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )

    return unload_ok


async def get_coordinator(hass, entry):
    """Get the data update coordinator."""
    if DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN]:
        return hass.data[DOMAIN][entry.entry_id]

    async def async_get_data():
        _LOGGER.info("Run query to server")
        poolsense = PoolSense()
        return_data = {}
        with async_timeout.timeout(10):
            try:
                return_data = await poolsense.get_poolsense_data(
                    aiohttp_client.async_get_clientsession(hass),
                    entry.data[CONF_EMAIL],
                    entry.data[CONF_PASSWORD],
                )
            except (PoolSenseError) as error:
                raise UpdateFailed(error)

        return return_data

    hass.data[DOMAIN][entry.entry_id] = update_coordinator.DataUpdateCoordinator(
        hass,
        logging.getLogger(__name__),
        name=DOMAIN,
        update_method=async_get_data,
        update_interval=timedelta(hours=1),
    )
    await hass.data[DOMAIN][entry.entry_id].async_refresh()
    return hass.data[DOMAIN][entry.entry_id]
