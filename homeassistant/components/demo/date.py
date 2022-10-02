"""Demo platform that offers a fake Date entity."""
from __future__ import annotations

from datetime import date, datetime

from homeassistant.components.date import DateEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import DEVICE_DEFAULT_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from . import DOMAIN


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the demo Date entity."""
    async_add_entities(
        [
            DemoDate(
                "date",
                "Date",
                date(2020, 1, 1),
                "mdi:calendar",
                False,
            ),
        ]
    )


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Demo config entry."""
    await async_setup_platform(hass, {}, async_add_entities)


class DemoDate(DateEntity):
    """Representation of a demo Date/time entity."""

    _attr_should_poll = False

    def __init__(
        self,
        unique_id: str,
        name: str,
        state: date | datetime,
        icon: str,
        assumed_state: bool,
    ) -> None:
        """Initialize the Demo Date/Time entity."""
        self._attr_assumed_state = assumed_state
        self._attr_icon = icon
        self._attr_name = name or DEVICE_DEFAULT_NAME
        self._attr_native_value = state
        self._attr_unique_id = unique_id

        self._attr_device_info = DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, unique_id)
            },
            name=self.name,
        )

    async def async_set_value(self, date_value: date | datetime) -> None:
        """Update the date."""
        self._attr_native_value = date_value
        self.async_write_ha_state()
