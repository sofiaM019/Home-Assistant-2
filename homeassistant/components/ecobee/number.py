"""Support for using number with ecobee thermostats."""
from __future__ import annotations

import logging

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, ECOBEE_MODEL_TO_NAME, MANUFACTURER

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the ecobee thermostat number entity."""
    data = hass.data[DOMAIN]
    min_time_home_entities = []
    _LOGGER.debug("Adding min time home ventilators numbers (if present)")
    for index in range(len(data.ecobee.thermostats)):
        thermostat = data.ecobee.get_thermostat(index)
        if thermostat["settings"]["ventilatorType"] != "none":
            _LOGGER.debug("Adding 1 ventilator's min time home number")
            min_time_home_entities.append(EcobeeVentilatorMinTimeHome(data, index))

    async_add_entities(min_time_home_entities, True)

    min_time_away_entities = []
    _LOGGER.debug("Adding min time away ventilators numbers (if present)")
    for index in range(len(data.ecobee.thermostats)):
        thermostat = data.ecobee.get_thermostat(index)
        if thermostat["settings"]["ventilatorType"] != "none":
            _LOGGER.debug("Adding 1 ventilator's min time away number")
            min_time_away_entities.append(EcobeeVentilatorMinTimeAway(data, index))

    async_add_entities(min_time_away_entities, True)


class EcobeeVentilatorMinTimeHome(NumberEntity):
    """A number class, representing min time on Home for an ecobee thermostat with ventilator attached."""

    def __init__(self, data, thermostat_index):
        """Initialize ecobee ventilator platform."""
        self.data = data
        self.thermostat_index = thermostat_index
        self.thermostat = self.data.ecobee.get_thermostat(self.thermostat_index)
        self._attr_has_entity_name = True
        self._attr_name = "Ventilator min time home"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.thermostat["identifier"])},
            manufacturer=MANUFACTURER,
            model=ECOBEE_MODEL_TO_NAME.get(self.thermostat["modelNumber"]),
            name=self.thermostat["name"],
        )
        self._attr_unique_id = f'{self.thermostat["identifier"]}_home'
        self._attr_native_min_value = 0
        self._attr_native_max_value = 60
        self._attr_native_step = 5
        self._attr_native_value = self.thermostat["settings"]["ventilatorMinOnTimeHome"]
        self._attr_native_unit_of_measurement = UnitOfTime.MINUTES

    async def async_update(self):
        """Get the latest state from the thermostat."""
        await self.data.update()
        self.thermostat = self.data.ecobee.get_thermostat(self.thermostat_index)
        self._attr_native_value = self.thermostat["settings"]["ventilatorMinOnTimeHome"]

    @property
    def available(self):
        """Return if device is available."""
        return self.thermostat["runtime"]["connected"]

    def set_native_value(self, value: float) -> None:
        """Set new ventilator Min On Time value."""
        self._attr_native_value = int(value)
        self.data.ecobee.set_ventilator_min_on_time_home(
            self.thermostat_index, int(value)
        )


class EcobeeVentilatorMinTimeAway(NumberEntity):
    """A number class, representing min time on Away for an ecobee thermostat with ventilator attached."""

    def __init__(self, data, thermostat_index):
        """Initialize ecobee ventilator platform."""
        self.data = data
        self.thermostat_index = thermostat_index
        self.thermostat = self.data.ecobee.get_thermostat(self.thermostat_index)
        self._attr_has_entity_name = True
        self._attr_name = "Ventilator min time away"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.thermostat["identifier"])},
            manufacturer=MANUFACTURER,
            model=ECOBEE_MODEL_TO_NAME.get(self.thermostat["modelNumber"]),
            name=self.thermostat["name"],
        )
        self._attr_unique_id = f'{self.thermostat["identifier"]}_away'
        self._attr_native_min_value = 0
        self._attr_native_max_value = 60
        self._attr_native_step = 5
        self._attr_native_value = self.thermostat["settings"]["ventilatorMinOnTimeAway"]
        self._attr_native_unit_of_measurement = UnitOfTime.MINUTES

    async def async_update(self):
        """Get the latest state from the thermostat."""
        await self.data.update()
        self.thermostat = self.data.ecobee.get_thermostat(self.thermostat_index)
        self._attr_native_value = self.thermostat["settings"]["ventilatorMinOnTimeAway"]

    @property
    def available(self):
        """Return if device is available."""
        return self.thermostat["runtime"]["connected"]

    def set_native_value(self, value: float) -> None:
        """Set new ventilator Min On Time value."""
        self._attr_native_value = int(value)
        self.data.ecobee.set_ventilator_min_on_time_away(
            self.thermostat_index, int(value)
        )
