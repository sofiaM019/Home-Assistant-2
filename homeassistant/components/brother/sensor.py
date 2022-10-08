"""Support for the Brother service."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
import logging
from typing import Any

from brother import BrotherSensors

from homeassistant.components.sensor import (
    DOMAIN as PLATFORM,
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, PERCENTAGE
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import BrotherDataUpdateCoordinator
from .const import DATA_CONFIG_ENTRY, DOMAIN

UNIT_PAGES = "p"

_LOGGER = logging.getLogger(__name__)


@dataclass
class BrotherSensorRequiredKeysMixin:
    """Class for Brother entity required keys."""

    value: Callable[[BrotherSensors], StateType | datetime]
    extra_state_attrs: Callable[[BrotherSensors], dict[str, Any]]


@dataclass
class BrotherSensorEntityDescription(
    SensorEntityDescription, BrotherSensorRequiredKeysMixin
):
    """A class that describes sensor entities."""


SENSOR_TYPES: tuple[BrotherSensorEntityDescription, ...] = (
    BrotherSensorEntityDescription(
        key="status",
        icon="mdi:printer",
        name="Status",
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda data: data.status,
        extra_state_attrs=lambda _: {},
    ),
    BrotherSensorEntityDescription(
        key="page_counter",
        icon="mdi:file-document-outline",
        name="Page counter",
        native_unit_of_measurement=UNIT_PAGES,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda data: data.page_counter,
        extra_state_attrs=lambda _: {},
    ),
    BrotherSensorEntityDescription(
        key="bw_counter",
        icon="mdi:file-document-outline",
        name="B/W counter",
        native_unit_of_measurement=UNIT_PAGES,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda data: data.bw_counter,
        extra_state_attrs=lambda _: {},
    ),
    BrotherSensorEntityDescription(
        key="color_counter",
        icon="mdi:file-document-outline",
        name="Color counter",
        native_unit_of_measurement=UNIT_PAGES,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda data: data.color_counter,
        extra_state_attrs=lambda _: {},
    ),
    BrotherSensorEntityDescription(
        key="duplex_unit_pages_counter",
        icon="mdi:file-document-outline",
        name="Duplex unit pages counter",
        native_unit_of_measurement=UNIT_PAGES,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda data: data.duplex_unit_pages_counter,
        extra_state_attrs=lambda _: {},
    ),
    BrotherSensorEntityDescription(
        key="drum_remaining_life",
        icon="mdi:chart-donut",
        name="Drum remaining life",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda data: data.drum_remaining_life,
        extra_state_attrs=lambda data: {
            "remaining_pages": data.drum_remaining_pages,
            "counter": data.drum_counter,
        },
    ),
    BrotherSensorEntityDescription(
        key="black_drum_remaining_life",
        icon="mdi:chart-donut",
        name="Black drum remaining life",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda data: data.black_drum_remaining_life,
        extra_state_attrs=lambda data: {
            "remaining_pages": data.black_drum_remaining_pages,
            "counter": data.black_drum_counter,
        },
    ),
    BrotherSensorEntityDescription(
        key="cyan_drum_remaining_life",
        icon="mdi:chart-donut",
        name="Cyan drum remaining life",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda data: data.cyan_drum_remaining_life,
        extra_state_attrs=lambda data: {
            "remaining_pages": data.cyan_drum_remaining_pages,
            "counter": data.cyan_drum_counter,
        },
    ),
    BrotherSensorEntityDescription(
        key="magenta_drum_remaining_life",
        icon="mdi:chart-donut",
        name="Magenta drum remaining life",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda data: data.magenta_drum_remaining_life,
        extra_state_attrs=lambda data: {
            "remaining_pages": data.magenta_drum_remaining_pages,
            "counter": data.magenta_drum_counter,
        },
    ),
    BrotherSensorEntityDescription(
        key="yellow_drum_remaining_life",
        icon="mdi:chart-donut",
        name="Yellow drum remaining life",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda data: data.yellow_drum_remaining_life,
        extra_state_attrs=lambda data: {
            "remaining_pages": data.yellow_drum_remaining_pages,
            "counter": data.yellow_drum_counter,
        },
    ),
    BrotherSensorEntityDescription(
        key="belt_unit_remaining_life",
        icon="mdi:current-ac",
        name="Belt unit remaining life",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda data: data.belt_unit_remaining_life,
        extra_state_attrs=lambda _: {},
    ),
    BrotherSensorEntityDescription(
        key="fuser_remaining_life",
        icon="mdi:water-outline",
        name="Fuser remaining life",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda data: data.fuser_remaining_life,
        extra_state_attrs=lambda _: {},
    ),
    BrotherSensorEntityDescription(
        key="laser_remaining_life",
        icon="mdi:spotlight-beam",
        name="Laser remaining life",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda data: data.laser_remaining_life,
        extra_state_attrs=lambda _: {},
    ),
    BrotherSensorEntityDescription(
        key="pf_kit_1_remaining_life",
        icon="mdi:printer-3d",
        name="PF Kit 1 remaining life",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda data: data.pf_kit_1_remaining_life,
        extra_state_attrs=lambda _: {},
    ),
    BrotherSensorEntityDescription(
        key="pf_kit_mp_remaining_life",
        icon="mdi:printer-3d",
        name="PF Kit MP remaining life",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda data: data.pf_kit_mp_remaining_life,
        extra_state_attrs=lambda _: {},
    ),
    BrotherSensorEntityDescription(
        key="black_toner_remaining",
        icon="mdi:printer-3d-nozzle",
        name="Black toner remaining",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda data: data.black_toner_remaining,
        extra_state_attrs=lambda _: {},
    ),
    BrotherSensorEntityDescription(
        key="cyan_toner_remaining",
        icon="mdi:printer-3d-nozzle",
        name="Cyan toner remaining",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda data: data.cyan_toner_remaining,
        extra_state_attrs=lambda _: {},
    ),
    BrotherSensorEntityDescription(
        key="magenta_toner_remaining",
        icon="mdi:printer-3d-nozzle",
        name="Magenta toner remaining",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda data: data.magenta_toner_remaining,
        extra_state_attrs=lambda _: {},
    ),
    BrotherSensorEntityDescription(
        key="yellow_toner_remaining",
        icon="mdi:printer-3d-nozzle",
        name="Yellow toner remaining",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda data: data.yellow_toner_remaining,
        extra_state_attrs=lambda _: {},
    ),
    BrotherSensorEntityDescription(
        key="black_ink_remaining",
        icon="mdi:printer-3d-nozzle",
        name="Black ink remaining",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda data: data.black_ink_remaining,
        extra_state_attrs=lambda _: {},
    ),
    BrotherSensorEntityDescription(
        key="cyan_ink_remaining",
        icon="mdi:printer-3d-nozzle",
        name="Cyan ink remaining",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda data: data.cyan_ink_remaining,
        extra_state_attrs=lambda _: {},
    ),
    BrotherSensorEntityDescription(
        key="magenta_ink_remaining",
        icon="mdi:printer-3d-nozzle",
        name="Magenta ink remaining",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda data: data.magenta_ink_remaining,
        extra_state_attrs=lambda _: {},
    ),
    BrotherSensorEntityDescription(
        key="yellow_ink_remaining",
        icon="mdi:printer-3d-nozzle",
        name="Yellow ink remaining",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda data: data.yellow_ink_remaining,
        extra_state_attrs=lambda _: {},
    ),
    BrotherSensorEntityDescription(
        key="uptime",
        name="Uptime",
        entity_registry_enabled_default=False,
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda data: data.uptime,
        extra_state_attrs=lambda _: {},
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Add Brother entities from a config_entry."""
    coordinator = hass.data[DOMAIN][DATA_CONFIG_ENTRY][entry.entry_id]

    # Due to the change of the attribute name of one sensor, it is necessary to migrate
    # the unique_id to the new one.
    entity_registry = er.async_get(hass)
    old_unique_id = f"{coordinator.data.serial.lower()}_b/w_counter"
    if entity_id := entity_registry.async_get_entity_id(
        PLATFORM, DOMAIN, old_unique_id
    ):
        new_unique_id = f"{coordinator.data.serial.lower()}_bw_counter"
        _LOGGER.debug(
            "Migrating entity %s from old unique ID '%s' to new unique ID '%s'",
            entity_id,
            old_unique_id,
            new_unique_id,
        )
        entity_registry.async_update_entity(entity_id, new_unique_id=new_unique_id)

    sensors = []

    device_info = DeviceInfo(
        configuration_url=f"http://{entry.data[CONF_HOST]}/",
        identifiers={(DOMAIN, coordinator.data.serial)},
        manufacturer="Brother",
        model=coordinator.data.model,
        name=coordinator.data.model,
        sw_version=coordinator.data.firmware,
    )

    for description in SENSOR_TYPES:
        if description.value(coordinator.data) is not None:
            sensors.append(BrotherPrinterSensor(coordinator, description, device_info))
    async_add_entities(sensors, False)


class BrotherPrinterSensor(CoordinatorEntity, SensorEntity):
    """Define an Brother Printer sensor."""

    _attr_has_entity_name = True
    entity_description: BrotherSensorEntityDescription

    def __init__(
        self,
        coordinator: BrotherDataUpdateCoordinator,
        description: BrotherSensorEntityDescription,
        device_info: DeviceInfo,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._attr_device_info = device_info
        self._attr_extra_state_attributes = description.extra_state_attrs(
            coordinator.data
        )
        self._attr_native_value = description.value(coordinator.data)
        self._attr_unique_id = f"{coordinator.data.serial.lower()}_{description.key}"
        self.entity_description = description

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_native_value = self.entity_description.value(self.coordinator.data)
        self._attr_extra_state_attributes = self.entity_description.extra_state_attrs(
            self.coordinator.data
        )
        self.async_write_ha_state()
