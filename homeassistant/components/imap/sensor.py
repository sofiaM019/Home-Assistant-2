"""IMAP sensor support."""
from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import ImapPollingDataUpdateCoordinator, ImapPushDataUpdateCoordinator
from .const import DOMAIN

IMAP_MAIL_COUNT = "imap_mail_count"


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Imap sensor."""

    coordinator: ImapPushDataUpdateCoordinator | ImapPollingDataUpdateCoordinator = (
        hass.data[DOMAIN][entry.entry_id]
    )
    description = SensorEntityDescription(
        key=IMAP_MAIL_COUNT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    )
    async_add_entities([ImapSensor(coordinator, description)])


class ImapSensor(
    CoordinatorEntity[ImapPushDataUpdateCoordinator | ImapPollingDataUpdateCoordinator],
    SensorEntity,
):
    """Representation of an IMAP sensor."""

    _attr_icon = "mdi:email-outline"
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ImapPushDataUpdateCoordinator | ImapPollingDataUpdateCoordinator,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
            name=f"IMAP ({coordinator.config_entry.data[CONF_USERNAME]})",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def native_value(self) -> int | None:
        """Return the number of emails found."""
        return self.coordinator.data
