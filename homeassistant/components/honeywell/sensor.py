"""Support for Honeywell (US) Total Connect Comfort sensors."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from somecomfort import Device

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    DEVICE_CLASS_HUMIDITY,
    DEVICE_CLASS_TEMPERATURE,
    PERCENTAGE,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
)
from homeassistant.helpers.typing import StateType

from .const import DOMAIN, HUMIDITY_STATUS_KEY, TEMPERATURE_STATUS_KEY


def _get_temperature_sensor_unit(device: Device) -> str:
    """Get the correct temperature unit for the device."""
    return TEMP_CELSIUS if device.temperature_unit == "C" else TEMP_FAHRENHEIT


@dataclass
class HoneywellSensorEntityDescriptionMixin:
    """Mixin for required keys."""

    value_fn: Callable[[Device], Any]
    unit_fn: Callable[[Device], Any]


@dataclass
class HoneywellSensorEntityDescription(
    SensorEntityDescription, HoneywellSensorEntityDescriptionMixin
):
    """Describes a Honeywell sensor entity."""


SENSOR_TYPES: tuple[HoneywellSensorEntityDescription, ...] = (
    HoneywellSensorEntityDescription(
        key=TEMPERATURE_STATUS_KEY,
        name="Temperature",
        device_class=DEVICE_CLASS_TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda device: device.outdoor_temperature,
        unit_fn=_get_temperature_sensor_unit,
    ),
    HoneywellSensorEntityDescription(
        key=HUMIDITY_STATUS_KEY,
        name="Humidity",
        device_class=DEVICE_CLASS_HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda device: device.outdoor_humidity,
        unit_fn=lambda device: PERCENTAGE,
    ),
)


async def async_setup_entry(hass, config, async_add_entities, discovery_info=None):
    """Set up the Honeywell thermostat."""
    data = hass.data[DOMAIN][config.entry_id]
    sensors = []

    for device in data.devices.values():
        for description in SENSOR_TYPES:
            if getattr(device, description.key) is not None:
                sensors.append(HoneywellSensor(device, description))

    async_add_entities(sensors)


class HoneywellSensor(SensorEntity):
    """Representation of a Honeywell US Outdoor Temperature Sensor."""

    entity_description: HoneywellSensorEntityDescription

    def __init__(self, device, description):
        """Initialize the outdoor temperature sensor."""
        self._device = device
        self.entity_description = description
        self._attr_unique_id = f"{device.deviceid}_outdoor_{description.device_class}"
        self._attr_name = f"{device.name} outdoor {description.device_class}"
        self._attr_native_unit_of_measurement = self.entity_description.unit_fn(device)

    @property
    def native_value(self) -> StateType:
        """Return the state."""
        return self.entity_description.value_fn(self._device)
