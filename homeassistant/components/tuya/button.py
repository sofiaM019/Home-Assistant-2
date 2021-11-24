"""Support for Tuya buttons."""
from __future__ import annotations

from typing import Any

from tuya_iot import TuyaDevice, TuyaDeviceManager

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ENTITY_CATEGORY_CONFIG
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import HomeAssistantTuyaData
from .base import TuyaEntity
from .const import DOMAIN, TUYA_DISCOVERY_NEW, DPCode

# All descriptions can be found here.
# https://developer.tuya.com/en/docs/iot/standarddescription?id=K9i5ql6waswzq
BUTTONS: dict[str, tuple[ButtonEntityDescription, ...]] = {
    # Robot Vacuum
    # https://developer.tuya.com/en/docs/iot/fsd?id=K9gf487ck1tlo
    "sd": (
        ButtonEntityDescription(
            key=DPCode.RESET_DUSTER_CLOTH,
            name="Reset Duster Cloth",
            icon="mdi:restart",
            entity_category=ENTITY_CATEGORY_CONFIG,
        ),
        ButtonEntityDescription(
            key=DPCode.RESET_EDGE_BRUSH,
            name="Reset Edge Brush",
            icon="mdi:restart",
            entity_category=ENTITY_CATEGORY_CONFIG,
        ),
        ButtonEntityDescription(
            key=DPCode.RESET_FILTER,
            name="Reset Filter",
            icon="mdi:air-filter",
            entity_category=ENTITY_CATEGORY_CONFIG,
        ),
        ButtonEntityDescription(
            key=DPCode.RESET_MAP,
            name="Reset Map",
            icon="mdi:map-marker-remove",
            entity_category=ENTITY_CATEGORY_CONFIG,
        ),
        ButtonEntityDescription(
            key=DPCode.RESET_ROLL_BRUSH,
            name="Reset Roll Brush",
            icon="mdi:restart",
            entity_category=ENTITY_CATEGORY_CONFIG,
        ),
    ),
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Tuya buttons dynamically through Tuya discovery."""
    hass_data: HomeAssistantTuyaData = hass.data[DOMAIN][entry.entry_id]

    @callback
    def async_discover_device(device_ids: list[str]) -> None:
        """Discover and add a discovered Tuya buttons."""
        entities: list[TuyaButtonEntity] = []
        for device_id in device_ids:
            device = hass_data.device_manager.device_map[device_id]
            if descriptions := BUTTONS.get(device.category):
                for description in descriptions:
                    if description.key in device.function:
                        entities.append(
                            TuyaButtonEntity(
                                device, hass_data.device_manager, description
                            )
                        )

        async_add_entities(entities)

    async_discover_device([*hass_data.device_manager.device_map])

    entry.async_on_unload(
        async_dispatcher_connect(hass, TUYA_DISCOVERY_NEW, async_discover_device)
    )


class TuyaButtonEntity(TuyaEntity, ButtonEntity):
    """Tuya Button Device."""

    def __init__(
        self,
        device: TuyaDevice,
        device_manager: TuyaDeviceManager,
        description: ButtonEntityDescription,
    ) -> None:
        """Init Tuya button."""
        super().__init__(device, device_manager)
        self.entity_description = description
        self._attr_unique_id = f"{super().unique_id}{description.key}"

    def press(self, **kwargs: Any) -> None:
        """Press the button."""
        self._send_command([{"code": self.entity_description.key, "value": True}])
