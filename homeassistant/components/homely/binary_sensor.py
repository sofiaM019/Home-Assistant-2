"""Sensors provided by Homely."""
import logging

from homelypy.devices import Device, MotionSensorMini, SmokeAlarm, State, WindowSensor

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN
from .coordinator import HomelyHomeCoordinator
from .homely_device import HomelyDevice

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up binary sensors based on a config entry."""
    homely_home: HomelyHomeCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[BinarySensorEntity] = []
    for homely_device in homely_home.devices.values():
        if isinstance(homely_device.homely_api_device, WindowSensor):
            entities.append(WindowSensorEntity(homely_home, homely_device))
        elif isinstance(homely_device.homely_api_device, SmokeAlarm):
            entities.append(SmokeAlarmEntity(homely_home, homely_device))
        elif isinstance(homely_device.homely_api_device, MotionSensorMini):
            entities.append(MotionSensorEntity(homely_home, homely_device))
        entities.append(BatteryLowEntity(homely_home, homely_device))
    async_add_entities(entities)


class HomelyBinarySensorEntity(CoordinatorEntity, BinarySensorEntity):
    """Abstract binary sensor class."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        homely_device: HomelyDevice,
    ) -> None:
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator)
        self.homely_device = homely_device
        self._attr_is_on = self.get_is_on_from_device(
            self.homely_device.homely_api_device
        )
        self._attr_device_info = homely_device.device_info
        self._attr_unique_id = f"{homely_device.homely_api_device.id}_{self._attr_name}"

    def get_is_on_from_device(self, device: Device) -> bool:
        """Get the current state of the sensor."""
        raise NotImplementedError

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        device: State = next(
            filter(
                lambda device: (device.id == self.homely_device.homely_api_device.id),
                self.coordinator.location.devices,
            )
        )
        self._attr_is_on = self.get_is_on_from_device(device)
        self.async_write_ha_state()


class WindowSensorEntity(HomelyBinarySensorEntity):
    """Represent a window sensor."""

    _attr_name = "Window"
    _attr_device_class = BinarySensorDeviceClass.WINDOW

    def get_is_on_from_device(self, device: Device) -> bool:
        """Get the current state of the sensor."""
        return device.alarm.alarm


class MotionSensorEntity(HomelyBinarySensorEntity):
    """Represent a motion sensor."""

    _attr_name = "Motion"
    _attr_device_class = BinarySensorDeviceClass.MOTION

    def get_is_on_from_device(self, device: Device) -> bool:
        """Get the current state of the sensor."""
        return device.alarm.alarm


class SmokeAlarmEntity(HomelyBinarySensorEntity):
    """Represent a smoke alarm."""

    _attr_name = "Smoke"
    _attr_device_class = BinarySensorDeviceClass.SMOKE

    def get_is_on_from_device(self, device: Device) -> bool:
        """Get the current state of the sensor."""
        return device.alarm.fire


class BatteryLowEntity(HomelyBinarySensorEntity):
    """Represent battery low state."""

    _attr_name = "Battery low"
    _attr_device_class = BinarySensorDeviceClass.BATTERY

    def get_is_on_from_device(self, device: Device) -> bool:
        """Get the current state of the sensor."""
        return device.battery.low
