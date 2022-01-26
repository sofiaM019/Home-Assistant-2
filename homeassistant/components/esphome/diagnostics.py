"""Diahgnostics support for ESPHome."""
from __future__ import annotations

from typing import Any, cast

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD
from homeassistant.core import HomeAssistant

from . import CONF_NOISE_PSK, DomainData

CONF_MAC_ADDRESS = "mac_address"

REDACT_CONFIG = {CONF_NOISE_PSK, CONF_PASSWORD}
REDACT_STORAGE_INFO = {CONF_MAC_ADDRESS}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    diag: dict[str, Any] = {}

    diag["config"] = async_redact_data(config_entry.as_dict(), REDACT_CONFIG)

    entry_data = DomainData.get(hass).get_entry_data(config_entry)

    if (storage_data := await entry_data.store.async_load()) is not None:
        storage_data = cast("dict[str, Any]", storage_data)
        diag["storage_data"] = async_redact_data(storage_data, REDACT_STORAGE_INFO)

    return diag
