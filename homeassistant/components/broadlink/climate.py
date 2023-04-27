"""Support for Broadlink climate devices."""
from typing import Any

from homeassistant.components.climate import (
    ATTR_CURRENT_TEMPERATURE,
    ATTR_HVAC_ACTION,
    ATTR_TEMPERATURE,
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PRECISION_HALVES, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN
from .device import BroadlinkDevice
from .entity import BroadlinkEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Broadlink climate entities."""
    device = hass.data[DOMAIN].devices[config_entry.entry_id]

    if device.api.type in {"HYS"}:
        async_add_entities([BroadlinkThermostat(device)])


class BroadlinkThermostat(ClimateEntity, BroadlinkEntity, RestoreEntity):
    """Representation of a Broadlink Hysen climate entity."""

    _attr_has_entity_name = True
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF, HVACMode.AUTO]
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_target_temperature_step = PRECISION_HALVES
    _attr_temperature_unit = UnitOfTemperature.CELSIUS

    def __init__(self, device: BroadlinkDevice) -> None:
        """Initialize the climate entity."""
        super().__init__(device)
        self._attr_hvac_action = None
        self._attr_hvac_mode = None
        self._attr_current_temperature = None
        self._attr_target_temperature = None
        self._attr_unique_id = device.unique_id

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temperature = kwargs[ATTR_TEMPERATURE]
        await self._device.async_request(self._device.api.set_temp, temperature)
        self._attr_target_temperature = temperature
        self.async_write_ha_state()

    @callback
    def _update_state(self, data: Any) -> None:
        """Update data."""
        if data["power"]:
            if data["auto_mode"]:
                self._attr_hvac_mode = HVACMode.AUTO
            else:
                self._attr_hvac_mode = HVACMode.HEAT

            if data["active"]:
                self._attr_hvac_action = HVACAction.HEATING
            else:
                self._attr_hvac_action = HVACAction.IDLE
        else:
            self._attr_hvac_mode = HVACMode.OFF
            self._attr_hvac_action = HVACAction.OFF

        self._attr_current_temperature = data["room_temp"]
        self._attr_target_temperature = data["thermostat_temp"]

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        if hvac_mode == HVACMode.OFF:
            await self._device.async_request(self._device.api.set_power, 0)

        elif hvac_mode == HVACMode.AUTO:
            await self._device.async_request(self._device.api.set_power, 1)
            await self._device.async_request(self._device.api.set_mode, 1, 0)

        elif hvac_mode == HVACMode.HEAT:
            await self._device.async_request(self._device.api.set_power, 1)
            await self._device.async_request(self._device.api.set_mode, 0, 0)

        self._attr_hvac_mode = hvac_mode
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added."""
        await super().async_added_to_hass()
        await self._async_restore_state()

    async def _async_restore_state(self) -> None:
        """Restore latest state."""
        if (old_state := await self.async_get_last_state()) is not None:
            if old_state.state is not None:
                self._attr_hvac_mode = old_state.state
            if old_state.attributes is not None:
                if old_state.attributes.get(ATTR_HVAC_ACTION) is not None:
                    self._attr_hvac_action = old_state.attributes[ATTR_HVAC_ACTION]
                if old_state.attributes.get(ATTR_TEMPERATURE) is not None:
                    self._attr_target_temperature = float(
                        old_state.attributes[ATTR_TEMPERATURE]
                    )
                if old_state.attributes.get(ATTR_CURRENT_TEMPERATURE) is not None:
                    self._attr_current_temperature = float(
                        old_state.attributes[ATTR_CURRENT_TEMPERATURE]
                    )
