"""LED BLE integration light platform."""
from __future__ import annotations

from typing import Any

from led_ble import LEDBLE

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_RGB_COLOR,
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN
from .models import LEDBLEData


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the light platform from config_flow."""
    data: LEDBLEData = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([LEDBLEEntity(data.coordinator, data.device, entry.title)])


class LEDBLEEntity(CoordinatorEntity, LightEntity):
    """Representation of LEDBLE device."""

    _attr_supported_color_modes = {ColorMode.RGB}
    _attr_color_mode = ColorMode.RGB
    _attr_has_entity_name = True

    def __init__(
        self, coordinator: DataUpdateCoordinator, device: LEDBLE, name: str
    ) -> None:
        """Initialize an ledble."""
        super().__init__(coordinator)
        self._device = device
        self._attr_unique_id = device._address
        self._attr_device_info = DeviceInfo(
            name=name,
            connections={(dr.CONNECTION_BLUETOOTH, device._address)},
        )
        self._async_update_attrs()

    @callback
    def _async_update_attrs(self) -> None:
        """Handle updating _attr values."""
        device = self._device
        if (brightness := device.brightness) is not None:
            self._attr_brightness = max(0, min(255, brightness))
        self._attr_rgb_color = device.rgb_unscaled
        self._attr_is_on = device.on

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Instruct the light to turn on."""
        brightness = kwargs.get(ATTR_BRIGHTNESS, self.brightness)
        if ATTR_RGB_COLOR in kwargs:
            rgb = kwargs[ATTR_RGB_COLOR]
            await self._device.set_rgb(rgb, brightness)
            return
        if ATTR_BRIGHTNESS in kwargs:
            await self._device.set_brightness(brightness)
            return
        await self._device.turn_on()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Instruct the light to turn off."""
        await self._device.turn_off()

    @callback
    def _handle_coordinator_update(self, *args: Any) -> None:
        """Handle data update."""
        self._async_update_attrs()
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Register callbacks."""
        self.async_on_remove(
            self._device.register_callback(self._handle_coordinator_update)
        )
        return await super().async_added_to_hass()
