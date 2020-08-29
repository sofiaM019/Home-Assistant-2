"""Provides the NZBGet DataUpdateCoordinator."""
from datetime import timedelta
import logging

from async_timeout import timeout

from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_SSL,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from . import NZBGetAPI, NZBGetAPIException
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class NZBGetDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching NZBGet data."""

    def __init__(
        self,
        hass: HomeAssistantType,
        *,
        config: dict,
        options: dict
    ):
        """Initialize global NZBGet data updater."""
        self.nzbget = NZBGetAPI(
            config[CONF_HOST],
            config[CONF_USERNAME] if config[CONF_USERNAME] != "" else None,
            config[CONF_PASSWORD] if config[CONF_PASSWORD] != "" else None,
            config[CONF_SSL],
            config[CONF_VERIFY_SSL],
            config[CONF_PORT],
        )

        self._completed_downloads_init = False
        self._completed_downloads = {}

        update_interval = timedelta(seconds=options[CONF_SCAN_INTERVAL])

        super().__init__(
            hass, _LOGGER, name=DOMAIN, update_interval=update_interval,
        )

    def _check_completed_downloads(self, history):
        """Check history for newly completed downloads."""
        actual_completed_downloads = {
            (x["Name"], x["Category"], x["Status"]) for x in history
        }

        if self._completed_downloads_init:
            tmp_completed_downloads = list(
                actual_completed_downloads.difference(self._completed_downloads)
            )

            for download in tmp_completed_downloads:
                self.hass.bus.fire(
                    "nzbget_download_complete",
                    {
                        "name": download[0],
                        "category": download[1],
                        "status": download[2],
                    },
                )

        self._completed_downloads = actual_completed_downloads
        self._completed_downloads_init = True

    async def _async_update_data(self) -> dict:
        """Fetch data from NZBGet."""

        def _update_data() -> dict:
            """Fetch data from NZBGet via sync functions."""
            status = self.nzbget.status()
            history = self.nzbget.history()

            self._check_completed_downloads(history)

            return {
                "status": status,
                "downloads": history,
            }

        try:
            async with timeout(4):
                return await self.hass.async_add_executor_job(_update_data)
        except NZBGetAPIException as error:
            raise UpdateFailed(f"Invalid response from API: {error}")
