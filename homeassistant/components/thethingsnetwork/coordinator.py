"""The Things Network's integration DataUpdateCoordinator."""

from collections.abc import Callable
from datetime import timedelta
import logging
import traceback
from typing import TYPE_CHECKING

from ttn_client import TTNAuthError, TTNClient

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_API_KEY,
    CONF_APP_ID,
    CONF_HOSTNAME,
    DEFAULT_API_REFRESH_PERIOD_S,
    DEFAULT_FIRST_FETCH_LAST_H,
    OPTIONS_MENU_EDIT_INTEGRATION,
    OPTIONS_MENU_INTEGRATION_FIRST_FETCH_TIME_H,
    OPTIONS_MENU_INTEGRATION_REFRESH_TIME_S,
)
from .entry_settings import TTN_EntrySettings

if TYPE_CHECKING:
    from .entity import TTN_Entity

_LOGGER = logging.getLogger(__name__)


class TTNCoordinator(DataUpdateCoordinator):
    """TTN coordinator."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name=f"TheThingsNetwork_{entry.data[CONF_APP_ID]}",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(
                seconds=entry.options.get(OPTIONS_MENU_EDIT_INTEGRATION, {}).get(
                    OPTIONS_MENU_INTEGRATION_REFRESH_TIME_S,
                    DEFAULT_API_REFRESH_PERIOD_S,
                )
            ),
        )
        self.__entry: ConfigEntry = entry
        self.__entity_class_register: list[TTNCoordinator.__RegisteredEntityClass] = []

        self.__client = TTNClient(
            entry.data[CONF_HOSTNAME],
            entry.data[CONF_APP_ID],
            entry.data[CONF_API_KEY],
            self.__entry.options.get(OPTIONS_MENU_EDIT_INTEGRATION, {}).get(
                OPTIONS_MENU_INTEGRATION_FIRST_FETCH_TIME_H, DEFAULT_FIRST_FETCH_LAST_H
            ),
            push_callback=self._push_callback,
        )

    async def _async_update_data(self) -> TTNClient.DATA_TYPE:
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            # Note: asyncio.TimeoutError and aiohttp.ClientError are already
            # handled by the data update coordinator.
            measurements = await self.__client.fetch_data()
            _LOGGER.debug("fetched data: %s", measurements)

            # Register newly found entities - nop if no new entities
            self.__async_add_entities(measurements)

            # Return measurements
            return measurements
        except TTNAuthError as err:
            # Raising ConfigEntryAuthFailed will cancel future updates
            # and start a config flow with SOURCE_REAUTH (async_step_reauth)
            _LOGGER.error("TTNAuthError")
            raise ConfigEntryAuthFailed from err
        except Exception as err:
            _LOGGER.error(err)
            _LOGGER.error(traceback.format_exc())
            raise

    async def _push_callback(self, data: TTNClient.DATA_TYPE) -> None:
        _LOGGER.debug("pushed data: %s", data)

        # Register newly found entities - nop if no new entities
        self.__async_add_entities(data)

        # Push data to entities
        self.async_set_updated_data(data)

    def register_platform_entity_class(
        self,
        entity_class: type["TTN_Entity"],
        async_add_entities: Callable[[TTNClient.DATA_TYPE], None],
    ) -> None:
        """Register a TTN_Entity handling for a platform.

        New entries discovered by this coordinator will be checked with each registered platform.
        If their `manages_uplink` method returns True then they will be added to their platform.
        """

        self.__entity_class_register.append(
            TTNCoordinator.__RegisteredEntityClass(
                self.__entry, entity_class, async_add_entities
            )
        )

    def __async_add_entities(self, data: TTNClient.DATA_TYPE) -> None:
        """Create new entities out of received TTN data if they are seen for the first time."""

        for entity_class in self.__entity_class_register:
            entity_class.async_add_entities(data)

    class __RegisteredEntityClass:
        def __init__(
            self,
            entry: ConfigEntry,
            entity_class: type["TTN_Entity"],
            async_add_entities: Callable[[TTNClient.DATA_TYPE], None],
        ) -> None:
            self.__entry = entry
            self.__entity_class = entity_class
            self.__async_add_entities = async_add_entities

        def async_add_entities(self, data: TTNClient.DATA_TYPE) -> None:
            """Add newly discovered entities to platform claiming ownership."""

            entrySettings = TTN_EntrySettings(self.__entry)
            self.__async_add_entities(
                self.__entity_class(
                    self.__entry,
                    entrySettings.get_coordinator(),
                    ttn_value,
                )
                for device_id, device_uplinks in data.items()
                for field_id, ttn_value in device_uplinks.items()
                if not self.__entity_class.exits(self.__entry, device_id, field_id)
                and self.__entity_class.manages_uplink(entrySettings, ttn_value)
            )
