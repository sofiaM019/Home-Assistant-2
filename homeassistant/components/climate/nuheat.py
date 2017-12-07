"""
Support for NuHeat thermostats.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/climate.nuheat/
"""
import logging
from datetime import timedelta

from homeassistant.components.climate import (
    ClimateDevice,
    SUPPORT_HOLD_MODE,
    SUPPORT_OPERATION_MODE,
    SUPPORT_TARGET_TEMPERATURE,
    STATE_HEAT,
    STATE_IDLE)
from homeassistant.components.nuheat import DATA_NUHEAT
from homeassistant.const import (
    ATTR_TEMPERATURE,
    STATE_HOME,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT)
from homeassistant.util import Throttle

DEPENDENCIES = ["nuheat"]

_LOGGER = logging.getLogger(__name__)

ICON = "mdi:thermometer"

MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=5)

# Hold modes
MODE_AUTO = STATE_HOME  # Run device schedule
MODE_HOLD_TEMPERATURE = "temperature"
MODE_TEMPORARY_HOLD = "temporary_temperature"

OPERATION_LIST = [STATE_HEAT, STATE_IDLE]

SCHEDULE_HOLD = 3
SCHEDULE_RUN = 1
SCHEDULE_TEMPORARY_HOLD = 2

SUPPORT_FLAGS = (SUPPORT_TARGET_TEMPERATURE | SUPPORT_HOLD_MODE |
                 SUPPORT_OPERATION_MODE)


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the NuHeat thermostat(s)."""
    if discovery_info is None:
        return

    temperature_unit = hass.config.units.temperature_unit
    api, serial_numbers = hass.data[DATA_NUHEAT]
    thermostats = [
        NuHeatThermostat(api, serial_number, temperature_unit)
        for serial_number in serial_numbers
    ]
    add_devices(thermostats, True)


class NuHeatThermostat(ClimateDevice):
    """Representation of a NuHeat Thermostat."""

    def __init__(self, api, serial_number, temperature_unit):
        """Initialize the thermostat."""
        self._thermostat = api.get_thermostat(serial_number)
        self._temperature_unit = temperature_unit
        self._force_update = False

    @property
    def name(self):
        """Return the name of the thermostat."""
        return self._thermostat.room

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        return ICON

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_FLAGS

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        if self._temperature_unit == "C":
            return TEMP_CELSIUS

        return TEMP_FAHRENHEIT

    @property
    def current_temperature(self):
        """Return the current temperature."""
        if self._temperature_unit == "C":
            return self._thermostat.celsius

        return self._thermostat.fahrenheit

    @property
    def current_operation(self):
        """Return current operation. ie. heat, idle."""
        if self._thermostat.heating:
            return STATE_HEAT

        return STATE_IDLE

    @property
    def min_temp(self):
        """Return the minimum supported temperature for the thermostat."""
        if self._temperature_unit == "C":
            return self._thermostat.min_celsius

        return self._thermostat.min_fahrenheit

    @property
    def max_temp(self):
        """Return the maximum supported temperature for the thermostat."""
        if self._temperature_unit == "C":
            return self._thermostat.max_celsius

        return self._thermostat.max_fahrenheit

    @property
    def target_temperature(self):
        """Return the currently programmed temperature."""
        if self._temperature_unit == "C":
            return self._thermostat.target_celsius

        return self._thermostat.target_fahrenheit

    @property
    def current_hold_mode(self):
        """Return current hold mode."""
        schedule_mode = self._thermostat.schedule_mode
        if schedule_mode == SCHEDULE_RUN:
            return MODE_AUTO

        if schedule_mode == SCHEDULE_HOLD:
            return MODE_HOLD_TEMPERATURE

        if schedule_mode == SCHEDULE_TEMPORARY_HOLD:
            return MODE_TEMPORARY_HOLD

        return MODE_AUTO

    @property
    def operation_list(self):
        """Return list of possible operation modes."""
        return OPERATION_LIST

    def resume_program(self):
        """Resume the thermostat's programmed schedule."""
        self._thermostat.resume_schedule()
        self._force_update = True

    def set_temperature(self, **kwargs):
        """Set a new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if self._temperature_unit == "C":
            self._thermostat.target_celsius = temperature
        else:
            self._thermostat.target_fahrenheit = temperature

        _LOGGER.debug(
            "Setting NuHeat thermostat temperature to %s %s",
            temperature, self.temperature_unit)

        self._force_update = True

    def update(self):
        """Get the latest state from the thermostat."""
        if self._force_update:
            self._throttled_update(no_throttle=True)
            self._force_update = False
        else:
            self._throttled_update()

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def _throttled_update(self, **kwargs):
        """Get the latest state from the thermostat with a throttle."""
        self._thermostat.get_data()
