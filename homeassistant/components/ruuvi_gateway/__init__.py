"""The Ruuvi Gateway integration."""
from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_TOKEN, Platform
from homeassistant.core import HomeAssistant

from .bluetooth import async_connect_scanner
from .const import DOMAIN
from .coordinator import RuuviGatewayUpdateCoordinator
from .models import RuuviGatewayRuntimeData

PLATFORMS: list[Platform] = []

_LOGGER = logging.getLogger(DOMAIN)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Ruuvi Gateway from a config entry."""
    coordinator = RuuviGatewayUpdateCoordinator(
        hass,
        logger=_LOGGER,
        name=entry.title,
        update_interval=timedelta(seconds=10),
        host=entry.data[CONF_HOST],
        token=entry.data[CONF_TOKEN],
    )
    scanner, unload_scanner = async_connect_scanner(hass, entry, coordinator)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = RuuviGatewayRuntimeData(
        update_coordinator=coordinator,
        scanner=scanner,
    )
    entry.async_on_unload(unload_scanner)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
