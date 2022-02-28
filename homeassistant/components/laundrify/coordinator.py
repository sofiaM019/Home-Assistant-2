"""Custom DataUpdateCoordinator for the laundrify integration."""
from datetime import timedelta
import logging

import async_timeout
from laundrify_aio.errors import ApiConnectionError, ApiUnauthorized

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, REQUEST_TIMEOUT

_LOGGER = logging.getLogger(__name__)


class LaundrifyUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching laundrify API data."""

    def __init__(self, hass, laundrify_api, poll_interval):
        """Initialize laundrify coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=poll_interval),
        )
        self.laundrify_api = laundrify_api

    async def _async_update_data(self):
        """Fetch data from laundrify API."""
        try:
            # Note: asyncio.TimeoutError and aiohttp.ClientError are already
            # handled by the data update coordinator.
            async with async_timeout.timeout(REQUEST_TIMEOUT):
                return await self.laundrify_api.get_machines()
        except ApiUnauthorized as err:
            # Raising ConfigEntryAuthFailed will cancel future updates
            # and start a config flow with SOURCE_REAUTH (async_step_reauth)
            raise ConfigEntryAuthFailed from err
        except ApiConnectionError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
