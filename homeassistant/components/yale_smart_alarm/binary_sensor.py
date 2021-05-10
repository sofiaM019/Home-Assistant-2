"""Support for Yale binary sensors."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    DEVICE_CLASS_OPENING,
    BinarySensorEntity,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import YaleDataUpdateCoordinator


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the binary_sensor platform."""

    return True


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the binary sensor entry."""
    coordinator: YaleDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        "coordinator"
    ]
    async_add_entities(
        YaleDoorWindowSensor(coordinator, key)
        for key in coordinator.data["door_window"]
    )

    return True


class YaleDoorWindowSensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a Yale door window sensor."""

    def __init__(self, coordinator: YaleDataUpdateCoordinator, name: str):
        """Initialize Yale door window sensor."""
        self._name = name
        self._state = None
        self.coordinator = coordinator
        super().__init__(coordinator)

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def device_class(self) -> str:
        """Return the class of this entity."""
        return DEVICE_CLASS_OPENING

    @property
    def is_on(self) -> bool:
        """Return the state of the sensor."""
        return self.coordinator.data["door_window"][self._name] == "open"
