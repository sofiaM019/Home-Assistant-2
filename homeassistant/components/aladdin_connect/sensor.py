"""Support for Aladdin Connect Garage Door sensors."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import cast

from AIOAladdinConnect import AladdinConnectClient

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, SIGNAL_STRENGTH_DECIBELS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .model import DoorDevice


@dataclass
class AccSensorEntityDescriptionMixin:
    """Mixin for required keys."""

    value_fn: Callable


@dataclass
class AccSensorEntityDescription(
    SensorEntityDescription, AccSensorEntityDescriptionMixin
):
    """Describes AladdinConnect sensor entity."""


SENSORS: tuple[AccSensorEntityDescription, ...] = (
    AccSensorEntityDescription(
        key="battery_level",
        name="Battery Level",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=AladdinConnectClient.get_battery_status,
    ),
    AccSensorEntityDescription(
        key="rssi",
        name="WIFI RSSI",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        entity_registry_enabled_default=False,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS,
        value_fn=AladdinConnectClient.get_rssi_status,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Aladdin Connect sensor devices."""

    acc: AladdinConnectClient = hass.data[DOMAIN][entry.entry_id]

    entities = []
    doors = await acc.get_doors()

    for door in doors:
        entities.extend(
            [AladdinConnectSensor(acc, door, description) for description in SENSORS]
        )

        async_add_entities(entities)


class AladdinConnectSensor(SensorEntity):
    """A sensor implementation for Aladdin Connect devices."""

    _device: AladdinConnectSensor
    entity_description: AccSensorEntityDescription

    def __init__(
        self,
        acc: AladdinConnectClient,
        device: DoorDevice,
        description: AccSensorEntityDescription,
    ) -> None:
        """Initialize a sensor for an Abode device."""
        self._device_id = device["device_id"]
        self._number = device["door_number"]
        self._name = device["name"]
        self._acc = acc
        self.entity_description = description
        self._attr_name = f"{self._name} {description.name}"
        self._attr_unique_id = f"{self._device_id}-{self._number}-{description.key}"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        # attribute: ignore
        return cast(
            float,
            self.entity_description.value_fn(self._acc, self._device_id, self._number),
        )
