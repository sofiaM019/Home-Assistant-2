"""The Palazzetti integration."""

from __future__ import annotations

from pypalazzetti.exceptions import CommunicationError, ValidationError

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError

from .const import DOMAIN
from .coordinator import PalazzettiDataUpdateCoordinator

PLATFORMS: list[Platform] = [Platform.CLIMATE]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Palazzetti from a config entry."""

    hass.data.setdefault(DOMAIN, {})
    coordinator = PalazzettiDataUpdateCoordinator(hass, entry)
    try:
        await coordinator.palazzetti.connect()
        await coordinator.palazzetti.update_state()
    except (CommunicationError, ValidationError) as err:
        raise ConfigEntryError(
            err, translation_domain=DOMAIN, translation_key="invalid_host"
        ) from err

    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = {"coordinator": coordinator}
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
