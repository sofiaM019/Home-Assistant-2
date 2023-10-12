"""Coordinator for La Marzocco API."""
from datetime import timedelta
import logging

from lmcloud.exceptions import AuthFail, RequestNotSuccessful

from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .lm_client import LaMarzoccoClient

SCAN_INTERVAL = timedelta(seconds=30)
UPDATE_DELAY = 2

_LOGGER = logging.getLogger(__name__)


class LmApiCoordinator(DataUpdateCoordinator):
    """Class to handle fetching data from the La Marzocco API centrally."""

    @property
    def lm(self):
        """Return the La Marzocco API object."""
        return self._lm

    def __init__(self, hass: HomeAssistant, lm: LaMarzoccoClient) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="La Marzocco API coordinator",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=SCAN_INTERVAL,
        )
        self._lm = lm
        self._initialized = False
        self._websocket_initialized = False
        self._websocket_task = None

    async def _async_update_data(self):
        try:
            _LOGGER.debug("Update coordinator: Updating data")
            if not self._initialized:
                await self._lm.hass_init()

            elif self._initialized and not self._websocket_initialized:
                # only initialize websockets after the first update
                _LOGGER.debug("Initializing WebSockets")
                self._websocket_task = self.hass.async_create_task(
                    self._lm.websocket_connect(
                        callback=self._on_data_received, use_sigterm_handler=False
                    )
                )
                self._websocket_initialized = True

            await self._lm.update_local_machine_status(force_update=True)

        except AuthFail as ex:
            msg = "Authentication failed. \
                            Maybe one of your credential details was invalid or you changed your password."
            _LOGGER.error(msg)
            _LOGGER.debug(msg, exc_info=True)
            raise ConfigEntryAuthFailed(msg) from ex
        except (RequestNotSuccessful, Exception) as ex:
            _LOGGER.error(ex)
            _LOGGER.debug(ex, exc_info=True)
            raise UpdateFailed("Querying API failed. Error: %s" % ex) from ex

        _LOGGER.debug("Current status: %s", str(self._lm.current_status))
        self._initialized = True
        return self._lm

    @callback
    def _on_data_received(self, property_updated, update):
        """Handle data received from websocket."""

        if not property_updated or not self._initialized:
            return

        _LOGGER.debug(
            "Received data from websocket, property updated: %s with value: %s",
            str(property_updated),
            str(update),
        )
        if property_updated:
            self._lm.update_current_status(property_updated, update)

        self.data = self._lm

        self.async_update_listeners()

    def terminate_websocket(self):
        """Terminate the websocket connection."""
        self._lm.websocket_terminating = True
        if self._websocket_task:
            self._websocket_task.cancel()
            self._websocket_task = None
