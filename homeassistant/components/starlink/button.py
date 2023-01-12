"""Contains buttons exposed by the Starlink ingegration."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from homeassistant.components.button import (
    ButtonDeviceClass,
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import StarlinkUpdateCoordinator
from .entity import StarlinkEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up all binary sensors for this entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        StarlinkButtonEntity(coordinator, description) for description in BUTTONS
    )


@dataclass
class StarlinkButtonEntityDescriptionMixin:
    """Mixin for required keys."""

    press_fn: Callable[[StarlinkUpdateCoordinator], Awaitable[None]]


@dataclass
class StarlinkButtonEntityDescription(
    ButtonEntityDescription, StarlinkButtonEntityDescriptionMixin
):
    """Describes a Starlink button entity."""


class StarlinkButtonEntity(StarlinkEntity, ButtonEntity):
    """A ButtonEntity for Starlink devices. Handles creating unique IDs."""

    entity_description: StarlinkButtonEntityDescription

    def __init__(
        self,
        coordinator: StarlinkUpdateCoordinator,
        description: StarlinkButtonEntityDescription,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{self.coordinator.data.status['id']}_{description.key}"

    async def async_press(self) -> None:
        """Press the button."""
        return await self.entity_description.press_fn(self.coordinator)


BUTTONS = [
    StarlinkButtonEntityDescription(
        key="reboot",
        name="Reboot",
        device_class=ButtonDeviceClass.RESTART,
        entity_category=EntityCategory.DIAGNOSTIC,
        press_fn=lambda coordinator: coordinator.reboot_starlink(),
    )
]
