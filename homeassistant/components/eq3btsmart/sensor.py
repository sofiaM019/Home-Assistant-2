"""Platform for eq3 sensor entities."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from eq3btsmart.models import Status

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.components.sensor.const import SensorStateClass
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import ENTITY_KEY_AWAY_UNTIL, ENTITY_KEY_VALVE
from .coordinator import Eq3ConfigEntry
from .entity import Eq3Entity


@dataclass(frozen=True, kw_only=True)
class Eq3SensorEntityDescription(SensorEntityDescription):
    """Entity description for eq3 sensor entities."""

    value_func: Callable[[Status], int | datetime | None]


SENSOR_ENTITY_DESCRIPTIONS = [
    Eq3SensorEntityDescription(
        key=ENTITY_KEY_VALVE,
        translation_key=ENTITY_KEY_VALVE,
        value_func=lambda status: status.valve,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    Eq3SensorEntityDescription(
        key=ENTITY_KEY_AWAY_UNTIL,
        translation_key=ENTITY_KEY_AWAY_UNTIL,
        value_func=lambda status: (
            status.away_until.value if status.away_until else None
        ),
        device_class=SensorDeviceClass.DATE,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: Eq3ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the entry."""

    async_add_entities(
        Eq3SensorEntity(entry, entity_description)
        for entity_description in SENSOR_ENTITY_DESCRIPTIONS
    )


class Eq3SensorEntity(Eq3Entity, SensorEntity):
    """Base class for eq3 sensor entities."""

    entity_description: Eq3SensorEntityDescription

    def __init__(
        self, entry: Eq3ConfigEntry, entity_description: Eq3SensorEntityDescription
    ) -> None:
        """Initialize the entity."""

        super().__init__(entry, entity_description.key)
        self.entity_description = entity_description

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""

        self._attr_native_value = self.entity_description.value_func(self._status)
        super()._handle_coordinator_update()
