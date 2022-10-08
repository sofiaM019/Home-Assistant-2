"""Camera for the Trafikverket Camera integration."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from homeassistant.components.camera import Camera
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_LOCATION, DOMAIN
from .coordinator import TVDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up a Trafikverket Camera."""

    coordinator: TVDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            TVCamera(
                coordinator,
                entry.title,
                entry.data[CONF_LOCATION],
                entry.entry_id,
            )
        ],
    )


class TVCamera(CoordinatorEntity[TVDataUpdateCoordinator], Camera):
    """Implement Trafikverket camera."""

    _attr_has_entity_name = True
    coordinator: TVDataUpdateCoordinator

    def __init__(
        self,
        coordinator: TVDataUpdateCoordinator,
        name: str,
        location: str,
        entry_id: str,
    ) -> None:
        """Initialize the camera."""
        super().__init__(coordinator)
        Camera.__init__(self)
        self._attr_unique_id = entry_id
        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, entry_id)},
            manufacturer="Trafikverket",
            model="v1.0",
            name=name,
            configuration_url="https://api.trafikinfo.trafikverket.se/",
        )

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return camera picture."""

        if image := self.coordinator.data.image:
            return image
        return None

    @property
    def is_on(self) -> bool:
        """Return camera on."""
        if self.coordinator.data.data:
            return bool(self.coordinator.data.data.active is True)
        return False

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return additional attributes."""
        if self.coordinator.data.data:
            return {
                "deleted": self.coordinator.data.data.deleted,
                "description": self.coordinator.data.data.description,
                "direction": self.coordinator.data.data.direction,
                "full_size_photo": self.coordinator.data.data.fullsizephoto,
                "last_modified": self.coordinator.data.data.modified,
                "photo time": self.coordinator.data.data.phototime,
                "photo url": self.coordinator.data.data.photourl,
                "status": self.coordinator.data.data.status,
                "type": self.coordinator.data.data.camera_type,
            }
        return None
