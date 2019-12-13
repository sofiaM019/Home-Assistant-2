"""Support for Vera binary sensors."""
import logging
from typing import Callable, List

from homeassistant.components.binary_sensor import (
    DOMAIN as PLATFORM_DOMAIN,
    ENTITY_ID_FORMAT,
    BinarySensorDevice,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity

from . import VeraDevice
from .common import setup_device_entities

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: Callable[[List[Entity], bool], None],
) -> None:
    """Set up the sensor config entry."""
    setup_device_entities(
        hass=hass,
        entry=entry,
        async_add_entities=async_add_entities,
        platform=PLATFORM_DOMAIN,
        generator=VeraBinarySensor,
    )


class VeraBinarySensor(VeraDevice, BinarySensorDevice):
    """Representation of a Vera Binary Sensor."""

    def __init__(self, vera_device, controller):
        """Initialize the binary_sensor."""
        self._state = False
        VeraDevice.__init__(self, vera_device, controller)
        self.entity_id = ENTITY_ID_FORMAT.format(self.vera_id)

    @property
    def is_on(self):
        """Return true if sensor is on."""
        return self._state

    def update(self):
        """Get the latest data and update the state."""
        self._state = self.vera_device.is_tripped
