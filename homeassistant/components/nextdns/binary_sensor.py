"""Support for the NextDNS service."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic

from nextdns import ConnectionStatus

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTR_CONNECTION, DOMAIN
from .coordinator import CoordinatorDataT, NextDnsConnectionUpdateCoordinator

PARALLEL_UPDATES = 1


@dataclass(frozen=True, kw_only=True)
class NextDnsBinarySensorEntityDescription(
    BinarySensorEntityDescription, Generic[CoordinatorDataT]
):
    """NextDNS binary sensor entity description."""

    state: Callable[[CoordinatorDataT, str], bool]


SENSORS = (
    NextDnsBinarySensorEntityDescription[ConnectionStatus](
        key="this_device_nextdns_connection_status",
        entity_category=EntityCategory.DIAGNOSTIC,
        translation_key="device_connection_status",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        state=lambda data, _: data.connected,
    ),
    NextDnsBinarySensorEntityDescription[ConnectionStatus](
        key="this_device_profile_connection_status",
        entity_category=EntityCategory.DIAGNOSTIC,
        translation_key="device_profile_connection_status",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        state=lambda data, profile_id: profile_id == data.profile_id,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add NextDNS entities from a config_entry."""
    coordinator: NextDnsConnectionUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        ATTR_CONNECTION
    ]

    async_add_entities(
        NextDnsBinarySensor(coordinator, description) for description in SENSORS
    )


class NextDnsBinarySensor(
    CoordinatorEntity[NextDnsConnectionUpdateCoordinator], BinarySensorEntity
):
    """Define an NextDNS binary sensor."""

    _attr_has_entity_name = True
    entity_description: NextDnsBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: NextDnsConnectionUpdateCoordinator,
        description: NextDnsBinarySensorEntityDescription,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._attr_device_info = coordinator.device_info
        self._attr_unique_id = f"{coordinator.profile_id}_{description.key}"
        self._attr_is_on = description.state(coordinator.data, coordinator.profile_id)
        self.entity_description = description

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_is_on = self.entity_description.state(
            self.coordinator.data, self.coordinator.profile_id
        )
        self.async_write_ha_state()
