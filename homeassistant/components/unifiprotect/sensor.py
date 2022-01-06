"""This component provides sensors for UniFi Protect."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from typing import Any

from pyunifiprotect.data import NVR
from pyunifiprotect.data.base import ProtectAdoptableDeviceModel

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    DATA_BYTES,
    DATA_RATE_BYTES_PER_SECOND,
    DATA_RATE_MEGABITS_PER_SECOND,
    DEVICE_CLASS_BATTERY,
    DEVICE_CLASS_HUMIDITY,
    DEVICE_CLASS_ILLUMINANCE,
    DEVICE_CLASS_SIGNAL_STRENGTH,
    DEVICE_CLASS_TEMPERATURE,
    DEVICE_CLASS_TIMESTAMP,
    DEVICE_CLASS_VOLTAGE,
    ELECTRIC_POTENTIAL_VOLT,
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    TEMP_CELSIUS,
    TIME_SECONDS,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import Entity, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .data import ProtectData
from .entity import ProtectDeviceEntity, ProtectNVREntity, async_all_device_entities
from .models import ProtectRequiredKeysMixin
from .utils import get_nested_attr

_LOGGER = logging.getLogger(__name__)


@dataclass
class ProtectSensorEntityDescription(ProtectRequiredKeysMixin, SensorEntityDescription):
    """Describes UniFi Protect Sensor entity."""

    precision: int | None = None


_KEY_MEMORY = "memory_utilization"
_KEY_DISK = "storage_utilization"
_KEY_RECORD_ROTATE = "record_rotating"
_KEY_RECORD_TIMELAPSE = "record_timelapse"
_KEY_RECORD_DETECTIONS = "record_detections"
_KEY_RES_HD = "resolution_HD"
_KEY_RES_4K = "resolution_4K"
_KEY_RES_FREE = "resolution_free"
_KEY_CAPACITY = "record_capacity"

ALL_DEVICES_SENSORS: tuple[ProtectSensorEntityDescription, ...] = (
    ProtectSensorEntityDescription(
        key="uptime",
        name="Uptime",
        icon="mdi:clock",
        device_class=DEVICE_CLASS_TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        ufp_value="up_since",
    ),
    ProtectSensorEntityDescription(
        key="ble_signal",
        name="Bluetooth Signal Strength",
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        device_class=DEVICE_CLASS_SIGNAL_STRENGTH,
        entity_registry_enabled_default=False,
        entity_category=EntityCategory.DIAGNOSTIC,
        ufp_value="bluetooth_connection_state.signal_strength",
        ufp_required_field="bluetooth_connection_state.signal_strength",
    ),
    ProtectSensorEntityDescription(
        key="phy_rate",
        name="Link Speed",
        native_unit_of_measurement=DATA_RATE_MEGABITS_PER_SECOND,
        entity_registry_enabled_default=False,
        entity_category=EntityCategory.DIAGNOSTIC,
        ufp_value="wired_connection_state.phy_rate",
        ufp_required_field="wired_connection_state.phy_rate",
    ),
    ProtectSensorEntityDescription(
        key="wifi_signal",
        name="WiFi Signal Strength",
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        device_class=DEVICE_CLASS_SIGNAL_STRENGTH,
        entity_registry_enabled_default=False,
        entity_category=EntityCategory.DIAGNOSTIC,
        ufp_value="wifi_connection_state.signal_strength",
        ufp_required_field="wifi_connection_state.signal_strength",
    ),
)

CAMERA_SENSORS: tuple[ProtectSensorEntityDescription, ...] = (
    ProtectSensorEntityDescription(
        key="stats_rx",
        name="Received Data",
        native_unit_of_measurement=DATA_BYTES,
        entity_registry_enabled_default=False,
        entity_category=EntityCategory.DIAGNOSTIC,
        ufp_value="stats.rx_bytes",
    ),
    ProtectSensorEntityDescription(
        key="stats_tx",
        name="Transferred Data",
        native_unit_of_measurement=DATA_BYTES,
        entity_registry_enabled_default=False,
        entity_category=EntityCategory.DIAGNOSTIC,
        ufp_value="stats.tx_bytes",
    ),
    ProtectSensorEntityDescription(
        key="oldest_recording",
        name="Oldest Recording",
        entity_registry_enabled_default=False,
        device_class=DEVICE_CLASS_TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        ufp_value="stats.video.recording_start",
    ),
    ProtectSensorEntityDescription(
        key="storage_used",
        name="Storage Used",
        native_unit_of_measurement=DATA_BYTES,
        entity_registry_enabled_default=False,
        entity_category=EntityCategory.DIAGNOSTIC,
        ufp_value="stats.storage.used",
    ),
    ProtectSensorEntityDescription(
        key="write_rate",
        name="Disk Write Rate",
        native_unit_of_measurement=DATA_RATE_BYTES_PER_SECOND,
        entity_registry_enabled_default=False,
        entity_category=EntityCategory.DIAGNOSTIC,
        ufp_value="stats.storage.rate",
        precision=2,
    ),
    ProtectSensorEntityDescription(
        key="voltage",
        name="Voltage",
        device_class=DEVICE_CLASS_VOLTAGE,
        native_unit_of_measurement=ELECTRIC_POTENTIAL_VOLT,
        entity_registry_enabled_default=False,
        entity_category=EntityCategory.DIAGNOSTIC,
        ufp_value="voltage",
        # no feature flag, but voltage will be null if device does not have voltage sensor
        # (i.e. is not G4 Doorbell or not on 1.20.1+)
        ufp_required_field="voltage",
        precision=2,
    ),
)

SENSE_SENSORS: tuple[ProtectSensorEntityDescription, ...] = (
    ProtectSensorEntityDescription(
        key="battery_level",
        name="Battery Level",
        native_unit_of_measurement=PERCENTAGE,
        device_class=DEVICE_CLASS_BATTERY,
        entity_category=EntityCategory.DIAGNOSTIC,
        ufp_value="battery_status.percentage",
    ),
    ProtectSensorEntityDescription(
        key="light_level",
        name="Light Level",
        native_unit_of_measurement="lx",
        device_class=DEVICE_CLASS_ILLUMINANCE,
        ufp_value="stats.light.value",
    ),
    ProtectSensorEntityDescription(
        key="humidity_level",
        name="Humidity Level",
        native_unit_of_measurement="%",
        device_class=DEVICE_CLASS_HUMIDITY,
        ufp_value="stats.humidity.value",
    ),
    ProtectSensorEntityDescription(
        key="temperature_level",
        name="Temperature",
        native_unit_of_measurement=TEMP_CELSIUS,
        device_class=DEVICE_CLASS_TEMPERATURE,
        ufp_value="stats.temperature.value",
    ),
)

NVR_SENSORS: tuple[ProtectSensorEntityDescription, ...] = (
    ProtectSensorEntityDescription(
        key="uptime",
        name="Uptime",
        icon="mdi:clock",
        device_class=DEVICE_CLASS_TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        ufp_value="up_since",
    ),
    ProtectSensorEntityDescription(
        key="cpu_utilization",
        name="CPU Utilization",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:speedometer",
        entity_registry_enabled_default=False,
        entity_category=EntityCategory.DIAGNOSTIC,
        ufp_value="system_info.cpu.average_load",
    ),
    ProtectSensorEntityDescription(
        key="cpu_temperature",
        name="CPU Temperature",
        native_unit_of_measurement=TEMP_CELSIUS,
        device_class=DEVICE_CLASS_TEMPERATURE,
        entity_registry_enabled_default=False,
        entity_category=EntityCategory.DIAGNOSTIC,
        ufp_value="system_info.cpu.temperature",
    ),
    ProtectSensorEntityDescription(
        key=_KEY_MEMORY,
        name="Memory Utilization",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:memory",
        entity_registry_enabled_default=False,
        entity_category=EntityCategory.DIAGNOSTIC,
        precision=2,
    ),
    ProtectSensorEntityDescription(
        key=_KEY_DISK,
        name="Storage Utilization",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:harddisk",
        entity_registry_enabled_default=False,
        entity_category=EntityCategory.DIAGNOSTIC,
        ufp_value="storage_stats.utilization",
        precision=2,
    ),
    ProtectSensorEntityDescription(
        key=_KEY_RECORD_TIMELAPSE,
        name="Type: Timelapse Video",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:server",
        entity_registry_enabled_default=False,
        entity_category=EntityCategory.DIAGNOSTIC,
        ufp_value="storage_stats.storage_distribution.timelapse_recordings.percentage",
        precision=2,
    ),
    ProtectSensorEntityDescription(
        key=_KEY_RECORD_ROTATE,
        name="Type: Continuous Video",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:server",
        entity_registry_enabled_default=False,
        entity_category=EntityCategory.DIAGNOSTIC,
        ufp_value="storage_stats.storage_distribution.continuous_recordings.percentage",
        precision=2,
    ),
    ProtectSensorEntityDescription(
        key=_KEY_RECORD_DETECTIONS,
        name="Type: Detections Video",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:server",
        entity_registry_enabled_default=False,
        entity_category=EntityCategory.DIAGNOSTIC,
        ufp_value="storage_stats.storage_distribution.detections_recordings.percentage",
        precision=2,
    ),
    ProtectSensorEntityDescription(
        key=_KEY_RES_HD,
        name="Resolution: HD Video",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:cctv",
        entity_registry_enabled_default=False,
        entity_category=EntityCategory.DIAGNOSTIC,
        ufp_value="storage_stats.storage_distribution.hd_usage.percentage",
        precision=2,
    ),
    ProtectSensorEntityDescription(
        key=_KEY_RES_4K,
        name="Resolution: 4K Video",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:cctv",
        entity_registry_enabled_default=False,
        entity_category=EntityCategory.DIAGNOSTIC,
        ufp_value="storage_stats.storage_distribution.uhd_usage.percentage",
        precision=2,
    ),
    ProtectSensorEntityDescription(
        key=_KEY_RES_FREE,
        name="Resolution: Free Space",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:cctv",
        entity_registry_enabled_default=False,
        entity_category=EntityCategory.DIAGNOSTIC,
        ufp_value="storage_stats.storage_distribution.free.percentage",
        precision=2,
    ),
    ProtectSensorEntityDescription(
        key=_KEY_CAPACITY,
        name="Recording Capacity",
        native_unit_of_measurement=TIME_SECONDS,
        icon="mdi:record-rec",
        entity_registry_enabled_default=False,
        entity_category=EntityCategory.DIAGNOSTIC,
        ufp_value="storage_stats.capacity",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors for UniFi Protect integration."""
    data: ProtectData = hass.data[DOMAIN][entry.entry_id]
    entities: list[ProtectDeviceEntity] = async_all_device_entities(
        data,
        ProtectDeviceSensor,
        all_descs=ALL_DEVICES_SENSORS,
        camera_descs=CAMERA_SENSORS,
        sense_descs=SENSE_SENSORS,
    )
    entities += _async_nvr_entities(data)

    async_add_entities(entities)


@callback
def _async_nvr_entities(
    data: ProtectData,
) -> list[ProtectDeviceEntity]:
    entities: list[ProtectDeviceEntity] = []
    device = data.api.bootstrap.nvr
    for description in NVR_SENSORS:
        entities.append(ProtectNVRSensor(data, device, description))
        _LOGGER.debug("Adding NVR sensor entity %s", description.name)

    return entities


class SensorValueMixin(Entity):
    """A mixin to provide sensor values."""

    @callback
    def _clean_sensor_value(self, value: Any) -> Any:
        if isinstance(value, timedelta):
            value = int(value.total_seconds())
        elif isinstance(value, datetime):
            # UniFi Protect value can vary slightly over time
            # truncate to ensure no extra state_change events fire
            value = value.replace(second=0, microsecond=0)

        assert isinstance(self.entity_description, ProtectSensorEntityDescription)
        if isinstance(value, float) and self.entity_description.precision:
            value = round(value, self.entity_description.precision)

        return value


class ProtectDeviceSensor(SensorValueMixin, ProtectDeviceEntity, SensorEntity):
    """A Ubiquiti UniFi Protect Sensor."""

    def __init__(
        self,
        data: ProtectData,
        device: ProtectAdoptableDeviceModel,
        description: ProtectSensorEntityDescription,
    ) -> None:
        """Initialize an UniFi Protect sensor."""
        self.entity_description: ProtectSensorEntityDescription = description
        super().__init__(data, device)

    @callback
    def _async_update_device_from_protect(self) -> None:
        super()._async_update_device_from_protect()

        assert self.entity_description.ufp_value is not None

        value = get_nested_attr(self.device, self.entity_description.ufp_value)
        self._attr_native_value = self._clean_sensor_value(value)


class ProtectNVRSensor(SensorValueMixin, ProtectNVREntity, SensorEntity):
    """A Ubiquiti UniFi Protect Sensor."""

	entity_description: ProtectSensorEntityDescription

    def __init__(
        self,
        data: ProtectData,
        device: NVR,
        description: ProtectSensorEntityDescription,
    ) -> None:
        """Initialize an UniFi Protect sensor."""
        self.entity_description = description
        super().__init__(data, device)

    @callback
    def _async_update_device_from_protect(self) -> None:
        super()._async_update_device_from_protect()

        # _KEY_MEMORY
        if self.entity_description.ufp_value is None:
            memory = self.device.system_info.memory
            value = (1 - memory.available / memory.total) * 100
        else:
            value = get_nested_attr(self.device, self.entity_description.ufp_value)

        self._attr_native_value = self._clean_sensor_value(value)
