"""
Support for eQ-3 Bluetooth Smart thermostats.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/climate.eq3btsmart/
"""
import logging

import voluptuous as vol

from homeassistant.components.climate import (
    ClimateDevice, PLATFORM_SCHEMA, PRECISION_HALVES,
    STATE_UNKNOWN, STATE_AUTO, STATE_ON, STATE_OFF,
)
from homeassistant.const import (
    CONF_MAC, TEMP_CELSIUS, CONF_DEVICES, ATTR_TEMPERATURE)

import homeassistant.helpers.config_validation as cv

REQUIREMENTS = ['bluepy_devices==0.2.0']

_LOGGER = logging.getLogger(__name__)

STATE_BOOST = "boost"
STATE_AWAY = "away"
STATE_MANUAL = "manual"

DEVICE_SCHEMA = vol.Schema({
    vol.Required(CONF_MAC): cv.string,
})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_DEVICES):
        vol.Schema({cv.string: DEVICE_SCHEMA}),
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the eQ-3 BLE thermostats."""
    devices = []

    for name, device_cfg in config[CONF_DEVICES].items():
        mac = device_cfg[CONF_MAC]
        devices.append(EQ3BTSmartThermostat(mac, name))

    add_devices(devices)


# pylint: disable=import-error
class EQ3BTSmartThermostat(ClimateDevice):
    """Representation of a eQ-3 Bluetooth Smart thermostat."""

    def __init__(self, _mac, _name):
        """Initialize the thermostat."""
        # we want to avoid name clash with this module..
        from bluepy_devices.devices import eq3btsmart as eq3

        self.modes = {eq3.EQ3BTSMART_UNKOWN: STATE_UNKNOWN,
                      eq3.EQ3BTSMART_AUTO: STATE_AUTO,
                      # away mode is handled separately, leaving here just for commentary
                      eq3.EQ3BTSMART_AWAY: STATE_AWAY,
                      eq3.EQ3BTSMART_CLOSED: STATE_OFF,
                      eq3.EQ3BTSMART_OPEN: STATE_ON,
                      eq3.EQ3BTSMART_MANUAL: STATE_MANUAL,
                      eq3.EQ3BTSMART_BOOST: STATE_BOOST}

        self.reverse_modes = {v: k for k, v in self.modes.items()}

        self._name = _name
        self._thermostat = eq3.EQ3BTSmartThermostat(_mac)

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def temperature_unit(self):
        """Return the unit of measurement that is used."""
        return TEMP_CELSIUS

    @property
    def precision(self):
        """Return eq3bt's precision 0.5"""
        return PRECISION_HALVES

    @property
    def current_temperature(self):
        """Can not report temperature, so return target_temperature."""
        return self.target_temperature

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._thermostat.target_temperature

    def set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        self._thermostat.target_temperature = temperature

    @property
    def current_operation(self):
        """Current mode."""
        return self.modes[self._thermostat.mode]

    @property
    def operation_list(self):
        """List of available operation modes."""
        return [x for x in self.modes.values()]

    def set_operation_mode(self, operation_mode):
        """Set operation mode."""
        self._thermostat.mode = self.reverse_modes[operation_mode]

    def turn_away_mode_off(self):
        """Away mode off turns to AUTO mode."""
        self.set_operation_mode(STATE_AUTO)

    def turn_away_mode_on(self):
        """Sets away mode on."""
        self.set_operation_mode(STATE_AWAY)

    @property
    def is_away_mode_on(self):
        """Returns whether we are away."""
        return self.current_operation == STATE_AWAY

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        return self._thermostat.min_temp

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        return self._thermostat.max_temp

    def update(self):
        """Update the data from the thermostat."""
        self._thermostat.update()
