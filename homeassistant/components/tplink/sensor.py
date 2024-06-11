"""Support for TPLink HS100/HS110/HS200 smart switch energy sensors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from kasa import Device, DeviceType

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_VOLTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ATTR_CURRENT_A,
    ATTR_CURRENT_POWER_W,
    ATTR_TODAY_ENERGY_KWH,
    ATTR_TOTAL_ENERGY_KWH,
    DOMAIN,
)
from .coordinator import TPLinkDataUpdateCoordinator
from .entity import CoordinatedTPLinkEntity
from .models import TPLinkData


@dataclass(frozen=True)
class TPLinkSensorEntityDescription(SensorEntityDescription):
    """Describes TPLink sensor entity."""

    emeter_attr: str | None = None
    precision: int | None = None


ENERGY_SENSORS: tuple[TPLinkSensorEntityDescription, ...] = (
    TPLinkSensorEntityDescription(
        key=ATTR_CURRENT_POWER_W,
        translation_key="current_consumption",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        emeter_attr="power",
        precision=1,
    ),
    TPLinkSensorEntityDescription(
        key=ATTR_TOTAL_ENERGY_KWH,
        translation_key="total_consumption",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        emeter_attr="total",
        precision=3,
    ),
    TPLinkSensorEntityDescription(
        key=ATTR_TODAY_ENERGY_KWH,
        translation_key="today_consumption",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        precision=3,
    ),
    TPLinkSensorEntityDescription(
        key=ATTR_VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        emeter_attr="voltage",
        precision=1,
    ),
    TPLinkSensorEntityDescription(
        key=ATTR_CURRENT_A,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        emeter_attr="current",
        precision=2,
    ),
)


def async_emeter_from_device(
    device: Device, description: TPLinkSensorEntityDescription
) -> float | None:
    """Map a sensor key to the device attribute."""
    if attr := description.emeter_attr:
        if (val := getattr(device.emeter_realtime, attr)) is None:
            return None
        return round(cast(float, val), description.precision)

    # ATTR_TODAY_ENERGY_KWH
    if (emeter_today := device.emeter_today) is not None:
        return round(cast(float, emeter_today), description.precision)
    # today's consumption not available, when device was off all the day
    # bulb's do not report this information, so filter it out
    return None if device.device_type == DeviceType.Bulb else 0.0


def _async_sensors_for_device(
    device: Device,
    coordinator: TPLinkDataUpdateCoordinator,
    parent: Device | None = None,
) -> list[SmartPlugSensor]:
    """Generate the sensors for the device."""
    return [
        SmartPlugSensor(device, coordinator, description, parent)
        for description in ENERGY_SENSORS
        if async_emeter_from_device(device, description) is not None
    ]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors."""
    data: TPLinkData = hass.data[DOMAIN][config_entry.entry_id]
    parent_coordinator = data.parent_coordinator
    children_coordinators = data.children_coordinators
    entities: list[SmartPlugSensor] = []
    parent = parent_coordinator.device
    if not parent.has_emeter:
        return

    if parent.children:
        # Historically we only add the children if the device is a strip
        for idx, child in enumerate(parent.children):
            # Only iot strips have child coordinators
            if children_coordinators:
                coordinator = children_coordinators[idx]
            else:
                coordinator = parent_coordinator
            entities.extend(_async_sensors_for_device(child, coordinator, parent))
    else:
        entities.extend(_async_sensors_for_device(parent, parent_coordinator))

    async_add_entities(entities)


class SmartPlugSensor(CoordinatedTPLinkEntity, SensorEntity):
    """Representation of a TPLink Smart Plug energy sensor."""

    entity_description: TPLinkSensorEntityDescription

    def __init__(
        self,
        device: Device,
        coordinator: TPLinkDataUpdateCoordinator,
        description: TPLinkSensorEntityDescription,
        parent: Device | None = None,
    ) -> None:
        """Initialize the switch."""
        self.entity_description = description
        super().__init__(device, coordinator, parent=parent)
        if parent is not None:
            assert device.alias
            self._attr_translation_placeholders = {"device_name": device.alias}
            if description.translation_key:
                self._attr_translation_key = f"{description.translation_key}_child"
            else:
                assert description.device_class
                self._attr_translation_key = f"{description.device_class.value}_child"
        self._async_call_update_attrs()

    @callback
    def _async_update_attrs(self) -> None:
        """Update the entity's attributes."""
        self._attr_native_value = async_emeter_from_device(
            self._device, self.entity_description
        )
