"""Lock for Yale Alarm."""
from __future__ import annotations

from yalesmartalarmclient.exceptions import AuthenticationError, UnknownError

from homeassistant.components.lock import LockEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_CODE, CONF_CODE, CONF_USERNAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_LOCK_CODE_DIGITS,
    COORDINATOR,
    DEFAULT_LOCK_CODE_DIGITS,
    DOMAIN,
    LOGGER,
    MANUFACTURER,
    MODEL,
)
from .coordinator import YaleDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Yale lock entry."""

    coordinator: YaleDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        COORDINATOR
    ]
    code_format = entry.options.get(CONF_LOCK_CODE_DIGITS, DEFAULT_LOCK_CODE_DIGITS)

    async_add_entities(
        YaleDoorlock(coordinator, data, code_format)
        for data in coordinator.data["locks"]
    )


class YaleDoorlock(CoordinatorEntity, LockEntity):
    """Representation of a Yale doorlock."""

    def __init__(
        self, coordinator: YaleDataUpdateCoordinator, data: dict, code_format: int
    ) -> None:
        """Initialize the Yale Lock Device."""
        super().__init__(coordinator)
        self._coordinator = coordinator
        self._attr_name = data["name"]
        self._attr_unique_id = data["address"]
        self._attr_device_info = DeviceInfo(
            name=self._attr_name,
            manufacturer=MANUFACTURER,
            model=MODEL,
            identifiers={(DOMAIN, data["address"])},
            via_device=(DOMAIN, self._coordinator.entry.data[CONF_USERNAME]),
        )
        self._attr_code_format = f"^\\d{code_format}$"

    async def async_unlock(self, **kwargs) -> None:
        """Send unlock command."""
        code = kwargs.get(ATTR_CODE, self._coordinator.entry.options.get(CONF_CODE))

        if not code or not self._coordinator.yale:
            return

        try:
            get_lock = await self.hass.async_add_executor_job(
                self._coordinator.yale.lock_api.get, self._attr_name
            )
            lock_state = await self.hass.async_add_executor_job(
                self._coordinator.yale.lock_api.open_lock,
                get_lock,
                code,
            )
        except (
            AuthenticationError,
            ConnectionError,
            TimeoutError,
            UnknownError,
        ) as error:
            LOGGER.warning("Could not verify door unlocked: %s", error)

        if lock_state:
            self._attr_is_locked = False
            self.async_write_ha_state()
        LOGGER.debug("Door unlock: %s", lock_state)

    async def async_lock(self, **kwargs) -> None:
        """Send lock command."""

        if not self._coordinator.yale:
            return

        try:
            get_lock = await self.hass.async_add_executor_job(
                self._coordinator.yale.lock_api.get, self._attr_name
            )
            lock_state = await self.hass.async_add_executor_job(
                self._coordinator.yale.lock_api.close_lock,
                get_lock,
            )
        except (
            AuthenticationError,
            ConnectionError,
            TimeoutError,
            UnknownError,
        ) as error:
            LOGGER.warning("Could not verify door locked: %s", error)

        if lock_state:
            self._attr_is_locked = True
            self.async_write_ha_state()
        LOGGER.debug("Door unlock: %s", lock_state)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        for lock in self.coordinator.data["locks"]:
            if lock["address"] == self._attr_unique_id:
                self._attr_is_locked = lock["_state"] == "locked"
                LOGGER.debug("Full data %s", lock)

        super()._handle_coordinator_update()
