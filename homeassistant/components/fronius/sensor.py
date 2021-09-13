"""Support for Fronius devices."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import CONF_RESOURCE
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType

from . import FroniusSolarNet
from .const import DOMAIN
from .coordinator import (
    FroniusEntity,
    FroniusInverterUpdateCoordinator,
    FroniusMeterUpdateCoordinator,
    FroniusPowerFlowUpdateCoordinator,
    FroniusStorageUpdateCoordinator,
)

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {vol.Required(CONF_RESOURCE): cv.url},
    extra=vol.ALLOW_EXTRA,
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: None = None,
) -> None:
    """Import Fronius configuration from yaml."""
    _LOGGER.warning(
        "Loading Fronius via platform setup is deprecated. Please remove it from your configuration"
    )
    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_IMPORT},
            data=config,
        )
    )


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Fronius sensor entities based on a config entry."""
    solar_net: FroniusSolarNet = hass.data[DOMAIN][config_entry.entry_id]
    for inverter_coordinator in solar_net.inverter_coordinators:
        inverter_coordinator.add_entities_for_seen_keys(
            async_add_entities, InverterSensor
        )
    if solar_net.meter_coordinator is not None:
        solar_net.meter_coordinator.add_entities_for_seen_keys(
            async_add_entities, MeterSensor
        )
    if solar_net.power_flow_coordinator is not None:
        solar_net.power_flow_coordinator.add_entities_for_seen_keys(
            async_add_entities, PowerFlowSensor
        )
    if solar_net.storage_coordinator is not None:
        solar_net.storage_coordinator.add_entities_for_seen_keys(
            async_add_entities, StorageSensor
        )


class InverterSensor(FroniusEntity, SensorEntity):
    """Defines a Fronius inverter device sensor entity."""

    coordinator: FroniusInverterUpdateCoordinator

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Set up an individual Fronius inverter sensor."""
        super().__init__(*args, **kwargs)
        # device_info created in __init__ from a `GetInverterInfo` request
        self._attr_device_info = self.coordinator.inverter_info.device_info
        self._attr_native_value = self._device_data[self.entity_description.key][
            "value"
        ]
        self._attr_unique_id = (
            f"{self.coordinator.inverter_info.unique_id}-{self.entity_description.key}"
        )


class MeterSensor(FroniusEntity, SensorEntity):
    """Defines a Fronius meter device sensor entity."""

    coordinator: FroniusMeterUpdateCoordinator

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Set up an individual Fronius meter sensor."""
        super().__init__(*args, **kwargs)
        meter_data = self._device_data

        self._attr_extra_state_attributes = {
            "meter_loaction": meter_data["meter_location"]["value"],
            "enable": meter_data["enable"]["value"],
            "visible": meter_data["visible"]["value"],
        }
        self._attr_device_info = DeviceInfo(
            name=meter_data["model"]["value"],
            identifiers={(DOMAIN, meter_data["serial"]["value"])},
            manufacturer=meter_data["manufacturer"]["value"],
            model=meter_data["model"]["value"],
            via_device=(DOMAIN, self.coordinator.solar_net_device_id),
        )
        self._attr_native_value = meter_data[self.entity_description.key]["value"]
        self._attr_unique_id = (
            f'{meter_data["serial"]["value"]}-{self.entity_description.key}'
        )


class PowerFlowSensor(FroniusEntity, SensorEntity):
    """Defines a Fronius power flow sensor entity."""

    coordinator: FroniusPowerFlowUpdateCoordinator

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Set up an individual Fronius power flow sensor."""
        super().__init__(*args, **kwargs)
        # device_info created in __init__ from a `GetLoggerInfo` or `GetInverterInfo` request
        self._attr_device_info = self.coordinator.power_flow_info.device_info
        self._attr_native_value = self._device_data[self.entity_description.key][
            "value"
        ]
        self._attr_unique_id = (
            f"{self.coordinator.power_flow_info.unique_id}"
            f"-power_flow-{self.entity_description.key}"
        )


class StorageSensor(FroniusEntity, SensorEntity):
    """Defines a Fronius storage device sensor entity."""

    coordinator: FroniusStorageUpdateCoordinator

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Set up an individual Fronius storage sensor."""
        super().__init__(*args, **kwargs)
        storage_data = self._device_data

        self._attr_device_info = DeviceInfo(
            name=storage_data["model"]["value"],
            identifiers={(DOMAIN, storage_data["serial"]["value"])},
            manufacturer=storage_data["manufacturer"]["value"],
            model=storage_data["model"]["value"],
            via_device=(DOMAIN, self.coordinator.solar_net_device_id),
        )
        self._attr_native_value = storage_data[self.entity_description.key]["value"]
        self._attr_unique_id = (
            f'{storage_data["serial"]["value"]}-{self.entity_description.key}'
        )
