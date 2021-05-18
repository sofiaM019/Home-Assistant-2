"""The SolarEdge integration."""
from __future__ import annotations

from requests.exceptions import ConnectTimeout, HTTPError
from solaredge import Solaredge

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
import homeassistant.helpers.config_validation as cv

from .const import CONF_SITE_ID, DATA_API_CLIENT, DOMAIN, LOGGER

CONFIG_SCHEMA = cv.deprecated(DOMAIN)

PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up SolarEdge from a config entry."""
    api = Solaredge(entry.data[CONF_API_KEY])

    try:
        response = await hass.async_add_executor_job(
            api.get_details, entry.data[CONF_SITE_ID]
        )
        if response["details"]["status"].lower() != "active":
            LOGGER.error("SolarEdge site is not active")
            return False
        LOGGER.debug("Credentials correct and site is active")
    except KeyError as ex:
        LOGGER.error("Missing details data in SolarEdge response")
        raise ConfigEntryNotReady from ex
    except (ConnectTimeout, HTTPError) as ex:
        LOGGER.error("Could not retrieve details from SolarEdge API")
        raise ConfigEntryNotReady from ex

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {DATA_API_CLIENT: api}
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload SolarEdge config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        del hass.data[DOMAIN][entry.entry_id]
    return unload_ok
