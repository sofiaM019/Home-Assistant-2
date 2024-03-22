"""Support for The Things network."""

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_APP_ID,
    CONF_HOSTNAME,
    DOMAIN,
    ENTRY_DATA_COORDINATOR,
    PLATFORMS,
    TTN_API_HOSTNAME,
)
from .coordinator import TTNCoordinator

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {},
            extra=vol.ALLOW_EXTRA,
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Initialize of The Things Network component."""

    if DOMAIN in config:
        ir.async_create_issue(
            hass,
            DOMAIN,
            "manual_migration",
            breaks_in_ha_version="2021.10.0",
            is_fixable=False,
            severity=ir.IssueSeverity.ERROR,
            translation_key="manual_migration",
            translation_placeholders={"domain": DOMAIN},
        )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Establish connection with The Things Network."""

    _LOGGER.debug(
        "Set up %s at %s",
        entry.data[CONF_APP_ID],
        entry.data.get(CONF_HOSTNAME, TTN_API_HOSTNAME),
    )

    # Create coordinator to fetch TTN updates
    coordinator = TTNCoordinator(hass, entry)
    hass.data.setdefault(DOMAIN, {}).setdefault(entry.entry_id, {})[
        ENTRY_DATA_COORDINATOR
    ] = coordinator

    # Trigger the creation of entities for each supported platform
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Fetch all existing values in the TTN storage DB - NOTE: the free TTN only keeps 24 hours
    await coordinator.async_config_entry_first_refresh()

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    _LOGGER.debug(
        "Remove %s at %s",
        entry.data[CONF_APP_ID],
        entry.data.get(CONF_HOSTNAME, TTN_API_HOSTNAME),
    )

    # Unload entities created for each supported platform
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        del hass.data[DOMAIN][entry.entry_id]
    return True
