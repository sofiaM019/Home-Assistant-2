"""Coordinator for Glances integration."""
from datetime import timedelta
import logging
from typing import Any

from glances_api import Glances, exceptions

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class GlancesDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Get the latest data from Glances api."""

    def __init__(
        self, hass: HomeAssistant, config_entry: ConfigEntry, api: Glances
    ) -> None:
        """Initialize the Glances data."""
        self.hass = hass
        self.config_entry: ConfigEntry = config_entry
        self.host: str = self.config_entry.data[CONF_HOST]
        self.api = api
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} - {self.host}",
            update_interval=timedelta(seconds=60),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Get the latest data from the Glances REST API."""

        try:
            await self.api.get_data("all")
        except exceptions.GlancesApiError as err:
            raise UpdateFailed from err
        return self.api.ha_sensor_data()
