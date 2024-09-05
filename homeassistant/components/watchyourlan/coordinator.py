"""Coordinator for the WatchYourLAN integration."""

import logging
from types import MappingProxyType

from watchyourlanclient import WatchYourLANClient

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)


class WatchYourLANUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the WatchYourLAN API."""

    def __init__(self, hass: HomeAssistant, config: MappingProxyType) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="WatchYourLAN",
        )
        self.api_url = config.get("url")
        self.api_client = WatchYourLANClient(
            base_url=config.get("url"), async_mode=True
        )

    async def _async_update_data(self):
        """Fetch data from the WatchYourLAN API with retries."""
        try:
            return await self.api_client.get_all_hosts()
        except Exception as e:
            _LOGGER.error("Failed to fetch data from WatchYourLAN")
            raise UpdateFailed(f"Error fetching data: {e}") from e

        return None
