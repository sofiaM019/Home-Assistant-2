"""Support for the QNAP QSW service."""
from __future__ import annotations

from qnap_qsw.const import (
    DATA_CONFIG_URL,
    DATA_FIRMWARE_CURRENT_VERSION,
    DATA_SYSTEM_PRODUCT,
    DATA_SYSTEM_SERIAL,
    DATA_TEMPERATURE_CURRENT,
    DATA_TEMPERATURE_MAXIMUM,
    DATA_UPTIME_DATETIME_ISOFORMAT,
    DATA_UPTIME_SECONDS,
)

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import QnapQswDataUpdateCoordinator
from .const import DOMAIN, MANUFACTURER, SENSOR_TYPES


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Add QNAP QSW entities from a config_entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    sensors = []

    device_info: DeviceInfo = {
        "configuration_url": coordinator.data[DATA_CONFIG_URL],
        "identifiers": {(DOMAIN, coordinator.data[DATA_SYSTEM_SERIAL])},
        "manufacturer": MANUFACTURER,
        "model": coordinator.data[DATA_SYSTEM_PRODUCT],
        "name": coordinator.data[DATA_SYSTEM_PRODUCT],
        "sw_version": coordinator.data[DATA_FIRMWARE_CURRENT_VERSION],
    }

    for description in SENSOR_TYPES:
        if description.key in coordinator.data:
            sensors.append(QnapQswSensor(coordinator, description, device_info))

    async_add_entities(sensors, False)


class QnapQswSensor(CoordinatorEntity, SensorEntity):
    """Define a QNAP QSW sensor."""

    def __init__(
        self,
        coordinator: QnapQswDataUpdateCoordinator,
        description: SensorEntityDescription,
        device_info: DeviceInfo,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._attr_device_info = device_info
        self._attr_name = f"{coordinator.data[DATA_SYSTEM_PRODUCT]} {description.name}"
        self._attr_unique_id = (
            f"{coordinator.data[DATA_SYSTEM_SERIAL].lower()}_{description.key}"
        )
        self.entity_description = description

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        _state_attr = None
        if self.entity_description.key == DATA_UPTIME_DATETIME_ISOFORMAT:
            _state_attr = {
                "seconds": self.coordinator.data[DATA_UPTIME_SECONDS],
            }
        elif self.entity_description.key == DATA_TEMPERATURE_CURRENT:
            _state_attr = {
                "maximum": self.coordinator.data[DATA_TEMPERATURE_MAXIMUM],
            }
        return _state_attr

    @property
    def native_value(self):
        """Return the state."""
        return self.coordinator.data[self.entity_description.key]
