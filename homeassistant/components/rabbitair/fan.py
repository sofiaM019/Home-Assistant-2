"""Support for Rabbit Air fan entity."""
from __future__ import annotations

import logging
from typing import Any

from rabbitair import Client, Mode, Model, Speed, State

from homeassistant.components.fan import (
    SUPPORT_PRESET_MODE,
    SUPPORT_SET_SPEED,
    FanEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util.percentage import (
    ordered_list_item_to_percentage,
    percentage_to_ordered_list_item,
)

from .const import DOMAIN, KEY_COORDINATOR, KEY_DEVICE
from .entity import RabbitAirBaseEntity

_LOGGER = logging.getLogger(__name__)

SPEED_LIST = [
    Speed.Silent,
    Speed.Low,
    Speed.Medium,
    Speed.High,
    Speed.Turbo,
]

PRESET_MODE_AUTO = "Auto"
PRESET_MODE_MANUAL = "Manual"
PRESET_MODE_POLLEN = "Pollen"

PRESET_MODES = {
    PRESET_MODE_AUTO: Mode.Auto,
    PRESET_MODE_MANUAL: Mode.Manual,
    PRESET_MODE_POLLEN: Mode.Pollen,
}


class RabbitAirFanEntity(RabbitAirBaseEntity, FanEntity):
    """Fan control functions of the Rabbit Air air purifier."""

    _attr_supported_features = SUPPORT_PRESET_MODE | SUPPORT_SET_SPEED

    def __init__(
        self,
        coordinator: DataUpdateCoordinator[State],
        client: Client,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator, client, entry)

        if self._is_model(Model.MinusA2):
            self._attr_preset_modes = list(PRESET_MODES)
        elif self._is_model(Model.A3):
            # A3 does not support Pollen mode
            self._attr_preset_modes = [
                k for k in PRESET_MODES if k != PRESET_MODE_POLLEN
            ]

        self._attr_speed_count = len(SPEED_LIST)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        await self._set_state(mode=PRESET_MODES[preset_mode])

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed of the fan, as a percentage."""
        value = percentage_to_ordered_list_item(SPEED_LIST, percentage)
        await self._set_state(speed=value)

    async def async_turn_on(
        self,
        speed: str | None = None,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn on the fan."""
        mode_value: Mode | None = None
        if preset_mode is not None:
            mode_value = PRESET_MODES[preset_mode]
        speed_value: Speed | None = None
        if percentage is not None:
            speed_value = percentage_to_ordered_list_item(SPEED_LIST, percentage)
        await self._set_state(power=True, mode=mode_value, speed=speed_value)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the fan off."""
        await self._set_state(power=False)

    @property
    def is_on(self) -> bool | None:
        """Return true if device is on."""
        return self.coordinator.data.power

    @property
    def percentage(self) -> int | None:
        """Return the current speed as a percentage."""
        speed = self.coordinator.data.speed
        if speed is None:
            return None
        if speed is Speed.SuperSilent:
            return 0
        return ordered_list_item_to_percentage(SPEED_LIST, speed)

    @property
    def preset_mode(self) -> str | None:
        """Return the current preset mode."""
        mode = self.coordinator.data.mode
        if mode is None:
            return None
        # Get key by value in dictionary
        return next(k for k, v in PRESET_MODES.items() if v == mode)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id][KEY_COORDINATOR]
    device = hass.data[DOMAIN][entry.entry_id][KEY_DEVICE]

    async_add_entities([RabbitAirFanEntity(coordinator, device, entry)])
