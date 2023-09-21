"""Support for Comelit."""
import asyncio
from datetime import timedelta
from typing import Any

from aiocomelit import ComeliteSerialBridgeApi
import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import _LOGGER, DOMAIN


class ComelitSerialBridge(DataUpdateCoordinator):
    """Queries Comelit Serial Bridge."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, host: str, pin: int) -> None:
        """Initialize the scanner."""

        self._host = host
        self._pin = pin

        self.api = ComeliteSerialBridgeApi(host, pin)

        super().__init__(
            hass=hass,
            logger=_LOGGER,
            name=f"{DOMAIN}-{host}-coordinator",
            update_interval=timedelta(seconds=5),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Update router data."""
        _LOGGER.debug("Polling Comelit Serial Bridge host: %s", self._host)
        try:
            logged = await self.api.login()
        except (asyncio.exceptions.TimeoutError, aiohttp.ClientConnectorError) as err:
            _LOGGER.warning("Connection error for %s", self._host)
            raise UpdateFailed(f"Error fetching data: {repr(err)}") from err

        if not logged:
            raise ConfigEntryAuthFailed

        devices_data = await self.api.get_all_devices()
        await self.api.logout()

        return devices_data

    def register_device(self) -> None:
        """Create device with all available info."""

        device_registry = dr.async_get(self.hass)
        device_registry.async_get_or_create(
            config_entry_id=self.config_entry.entry_id,
            identifiers={
                (DOMAIN, self.config_entry.entry_id),
            },
            manufacturer="Comelit",
            model="Serial Bridge",
            hw_version="20003101",
            name=f"Serial Bridge ({self.api.host})",
        )
