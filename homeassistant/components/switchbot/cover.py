"""Support for SwitchBot curtains."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.cover import (
    ATTR_CURRENT_POSITION,
    ATTR_POSITION,
    DEVICE_CLASS_CURTAIN,
    SUPPORT_CLOSE,
    SUPPORT_OPEN,
    SUPPORT_SET_POSITION,
    SUPPORT_STOP,
    CoverEntity,
)
from homeassistant.components.switchbot.entity import SwitchbotEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_MAC, CONF_NAME, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_RETRY_COUNT, DATA_COORDINATOR, DOMAIN, MANUFACTURER
from .coordinator import SwitchbotDataUpdateCoordinator

# Initialize the logger
_LOGGER = logging.getLogger(__name__)
PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Switchbot curtain based on a config entry."""
    coordinator: SwitchbotDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]

    async_add_entities(
        [
            SwitchBotCurtain(
                coordinator,
                entry.unique_id,
                entry.data[CONF_MAC],
                entry.data[CONF_NAME],
                entry.data.get(CONF_PASSWORD, None),
                entry.options[CONF_RETRY_COUNT],
            )
        ]
    )


class SwitchBotCurtain(CoordinatorEntity, SwitchbotEntity, CoverEntity, RestoreEntity):
    """Representation of a Switchbot."""

    coordinator: SwitchbotDataUpdateCoordinator
    _attr_device_class = DEVICE_CLASS_CURTAIN
    _attr_supported_features = (
        SUPPORT_OPEN | SUPPORT_CLOSE | SUPPORT_STOP | SUPPORT_SET_POSITION
    )
    _attr_assumed_state = True

    def __init__(
        self,
        coordinator: SwitchbotDataUpdateCoordinator,
        idx: str | None,
        mac: str,
        name: str,
        password: str,
        retry_count: int,
    ) -> None:
        """Initialize the Switchbot."""
        super().__init__(coordinator)
        self._last_run_success: bool | None = None
        self._idx = idx
        self._attr_unique_id = idx
        self._attr_name = name
        self._mac = mac
        self._attr_device_info: DeviceInfo = {
            "connections": {(dr.CONNECTION_NETWORK_MAC, self._mac)},
            "name": self._attr_name,
            "model": self.coordinator.data[self._idx]["modelName"],
            "manufacturer": MANUFACTURER,
        }
        self._device = self.coordinator.switchbot_api.SwitchbotCurtain(
            mac=mac, password=password, retry_count=retry_count
        )

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added."""
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if not last_state or ATTR_CURRENT_POSITION not in last_state.attributes:
            return

        self._attr_current_cover_position = last_state.attributes[ATTR_CURRENT_POSITION]
        self._last_run_success = last_state.attributes["last_run_success"]

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes."""
        return {**super().extra_state_attributes}

    @property
    def is_closed(self) -> bool | None:
        """Return if the cover is closed."""
        return self.coordinator.data[self._idx]["data"]["position"] <= 20

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the curtain."""

        _LOGGER.info("Switchbot to open curtain %s", self._mac)

        async with self.coordinator.api_lock:
            self._last_run_success = bool(
                await self.hass.async_add_executor_job(self._device.open)
            )

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the curtain."""

        _LOGGER.info("Switchbot to close the curtain %s", self._mac)

        async with self.coordinator.api_lock:
            self._last_run_success = bool(
                await self.hass.async_add_executor_job(self._device.close)
            )

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop the moving of this device."""

        _LOGGER.info("Switchbot to stop %s", self._mac)

        async with self.coordinator.api_lock:
            self._last_run_success = bool(
                await self.hass.async_add_executor_job(self._device.stop)
            )

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Move the cover shutter to a specific position."""
        position = kwargs.get(ATTR_POSITION)

        _LOGGER.info("Switchbot to move at %d %s", position, self._mac)

        async with self.coordinator.api_lock:
            self._last_run_success = bool(
                await self.hass.async_add_executor_job(
                    self._device.set_position, position
                )
            )

    @property
    def current_cover_position(self) -> int:
        """Return the current position of cover shutter."""
        return self.coordinator.data[self._idx]["data"]["position"]
