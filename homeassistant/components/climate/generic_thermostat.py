"""
Adds support for generic thermostat units.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/climate.generic_thermostat/
"""
import asyncio
import logging

import voluptuous as vol

from homeassistant.core import callback
from homeassistant.components import switch
from homeassistant.components.climate import (
    HOLD_MODE_AWAY, HOLD_MODE_HOME, HOLD_MODE_SLEEP, HOLD_MODE_VACATION,
    ATTR_HOLD_MODE,
    STATE_HEAT, STATE_COOL, STATE_IDLE, ClimateDevice, PLATFORM_SCHEMA)
from homeassistant.const import (
    ATTR_UNIT_OF_MEASUREMENT, STATE_ON, STATE_OFF, ATTR_TEMPERATURE)
from homeassistant.helpers import condition
from homeassistant.helpers.event import async_track_state_change
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ['switch', 'sensor']

DEFAULT_TOLERANCE = 0.3
DEFAULT_NAME = 'Generic Thermostat'

CONF_NAME = 'name'
CONF_HEATER = 'heater'
CONF_SENSOR = 'target_sensor'
CONF_MIN_TEMP = 'min_temp'
CONF_MAX_TEMP = 'max_temp'
CONF_TARGET_TEMP = 'target_temp'
CONF_HOLD_TEMPS = 'hold_temps'
CONF_AC_MODE = 'ac_mode'
CONF_MIN_DUR = 'min_cycle_duration'
CONF_TOLERANCE = 'tolerance'

HOLD_MODE_LIST = (
    HOLD_MODE_AWAY,
    HOLD_MODE_HOME,
    HOLD_MODE_SLEEP,
    HOLD_MODE_VACATION,
)


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HEATER): cv.entity_id,
    vol.Required(CONF_SENSOR): cv.entity_id,
    vol.Optional(CONF_AC_MODE): cv.boolean,
    vol.Optional(CONF_MAX_TEMP): vol.Coerce(float),
    vol.Optional(CONF_MIN_DUR): vol.All(cv.time_period, cv.positive_timedelta),
    vol.Optional(CONF_MIN_TEMP): vol.Coerce(float),
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_TOLERANCE, default=DEFAULT_TOLERANCE): vol.Coerce(float),
    vol.Optional(CONF_TARGET_TEMP): vol.Coerce(float),
    vol.Required(CONF_HOLD_TEMPS, default=dict()): vol.Schema({
        vol.Any(
            # Note that the hold mode "home" is NOT accepted here
            HOLD_MODE_AWAY, HOLD_MODE_SLEEP, HOLD_MODE_VACATION
        ): vol.Coerce(float),
    }),
})


@asyncio.coroutine
def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    """Setup the generic thermostat."""
    name = config.get(CONF_NAME)
    heater_entity_id = config.get(CONF_HEATER)
    sensor_entity_id = config.get(CONF_SENSOR)
    min_temp = config.get(CONF_MIN_TEMP)
    max_temp = config.get(CONF_MAX_TEMP)
    target_temp = config.get(CONF_TARGET_TEMP)
    hold_temps = config.get(CONF_HOLD_TEMPS)
    ac_mode = config.get(CONF_AC_MODE)
    min_cycle_duration = config.get(CONF_MIN_DUR)
    tolerance = config.get(CONF_TOLERANCE)

    yield from async_add_devices([GenericThermostat(
        hass, name, heater_entity_id, sensor_entity_id, min_temp, max_temp,
        target_temp, hold_temps, ac_mode, min_cycle_duration, tolerance)])


class GenericThermostat(ClimateDevice):
    """Representation of a GenericThermostat device."""

    def __init__(self, hass, name, heater_entity_id, sensor_entity_id,
                 min_temp, max_temp, target_temp, hold_temps, ac_mode,
                 min_cycle_duration, tolerance):
        """Initialize the thermostat."""
        self.hass = hass
        self._name = name
        self.heater_entity_id = heater_entity_id
        self.ac_mode = ac_mode

        if ac_mode:
            self._operation_list = [STATE_COOL, STATE_IDLE]
        else:
            self._operation_list = [STATE_HEAT, STATE_IDLE]

        self.min_cycle_duration = min_cycle_duration
        self._tolerance = tolerance

        self._active = False
        self._cur_temp = None
        self._min_temp = min_temp
        self._max_temp = max_temp
        self._current_hold_mode = 'home'
        self._target_temp = target_temp
        self._hold_temps = hold_temps
        self._hold_temps["home"] = target_temp
        self._unit = hass.config.units.temperature_unit

        async_track_state_change(
            hass, sensor_entity_id, self._async_sensor_changed)
        async_track_state_change(
            hass, heater_entity_id, self._async_switch_changed)

        sensor_state = hass.states.get(sensor_entity_id)
        if sensor_state:
            self._async_update_temp(sensor_state)

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def name(self):
        """Return the name of the thermostat."""
        return self._name

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return self._unit

    @property
    def current_temperature(self):
        """Return the sensor temperature."""
        return self._cur_temp

    @property
    def current_operation(self):
        """Return current operation ie. heat, cool, idle."""
        if self.ac_mode:
            cooling = self._active and self._is_device_active
            return STATE_COOL if cooling else STATE_IDLE
        else:
            heating = self._active and self._is_device_active
            return STATE_HEAT if heating else STATE_IDLE

    @property
    def operation_list(self):
        """List of available operation modes."""
        return self._operation_list

    @property
    def current_hold_mode(self):
        """Return the current hold mode."""
        return self._current_hold_mode

    @property
    def hold_list(self):
        """List of available hold modes."""
        # Support all hold modes, as they all are software defined.
        return HOLD_MODE_LIST

    @asyncio.coroutine
    def async_set_hold_mode(self, hold_mode):
        """Set hold mode (currently understood modes: away and home)."""
        if hold_mode == self.current_hold_mode:
            # no change, so no action required
            return

        if hold_mode not in HOLD_MODE_LIST:
            _LOGGER.warning('Hold mode `%s` is not supported, ignoring it.',
                            hold_mode)
            return

        if not self._hold_temps.get(hold_mode):
            _LOGGER.warning('Hold mode `%s` has no temperature set, ignoring',
                            hold_mode)
            return

        # store the (known) mode
        self._current_hold_mode = hold_mode
        _LOGGER.info('The hold mode has been set to `%s`.', hold_mode)
        # and force a refresh
        self._async_control_heating()
        yield from self.async_update_ha_state()

    @property
    def target_temperature(self):
        """Return the temperature we try to reach (in default "home" mode)."""
        return self._target_temp

    @asyncio.coroutine
    def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        hold_mode = kwargs.get(ATTR_HOLD_MODE, HOLD_MODE_HOME)

        if hold_mode not in HOLD_MODE_LIST:
            _LOGGER.warning('Hold mode `%s` is not supported, ignoring.',
                            hold_mode)
            return

        if temperature is None:
            _LOGGER.warning('Attribute `%s` is not an optional attribute, '
                            'ignoring service call.', ATTR_TEMPERATURE)
            return

        if hold_mode == HOLD_MODE_HOME:
            self._target_temp = temperature

        # Store the temperature in the hold_temps dictionary
        self._hold_temps[hold_mode] = temperature
        # Update
        self._async_control_heating()
        yield from self.async_update_ha_state()

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        # pylint: disable=no-member
        if self._min_temp:
            return self._min_temp
        else:
            # get default temp from super class
            return ClimateDevice.min_temp.fget(self)

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        # pylint: disable=no-member
        if self._max_temp:
            return self._max_temp
        else:
            # Get default temp from super class
            return ClimateDevice.max_temp.fget(self)

    @asyncio.coroutine
    def _async_sensor_changed(self, entity_id, old_state, new_state):
        """Called when temperature changes."""
        if new_state is None:
            return

        self._async_update_temp(new_state)
        self._async_control_heating()
        yield from self.async_update_ha_state()

    @callback
    def _async_switch_changed(self, entity_id, old_state, new_state):
        """Called when heater switch changes state."""
        if new_state is None:
            return
        self.hass.async_add_job(self.async_update_ha_state())

    @callback
    def _async_update_temp(self, state):
        """Update thermostat with latest state from sensor."""
        unit = state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)

        try:
            self._cur_temp = self.hass.config.units.temperature(
                float(state.state), unit)
        except ValueError as ex:
            _LOGGER.error('Unable to update from sensor: %s', ex)

    @callback
    def _async_control_heating(self):
        """Check if we need to turn heating on or off."""
        if not self._active and None not in (self._cur_temp,
                                             self._target_temp):
            self._active = True
            _LOGGER.info('Obtained current and target temperature. '
                         'Generic thermostat active.')

        if not self._active:
            return

        if self.min_cycle_duration:
            if self._is_device_active:
                current_state = STATE_ON
            else:
                current_state = STATE_OFF
            long_enough = condition.state(
                self.hass, self.heater_entity_id, current_state,
                self.min_cycle_duration)
            if not long_enough:
                return

        goal_temp = self._hold_temps[self._current_hold_mode]

        if self.ac_mode:
            is_cooling = self._is_device_active
            if is_cooling:
                too_cold = goal_temp - self._cur_temp > self._tolerance
                if too_cold:
                    _LOGGER.info('Turning off AC %s', self.heater_entity_id)
                    switch.async_turn_off(self.hass, self.heater_entity_id)
            else:
                too_hot = self._cur_temp - goal_temp > self._tolerance
                if too_hot:
                    _LOGGER.info('Turning on AC %s', self.heater_entity_id)
                    switch.async_turn_on(self.hass, self.heater_entity_id)
        else:
            is_heating = self._is_device_active
            if is_heating:
                too_hot = self._cur_temp - goal_temp > self._tolerance
                if too_hot:
                    _LOGGER.info('Turning off heater %s',
                                 self.heater_entity_id)
                    switch.async_turn_off(self.hass, self.heater_entity_id)
            else:
                too_cold = goal_temp - self._cur_temp > self._tolerance
                if too_cold:
                    _LOGGER.info('Turning on heater %s', self.heater_entity_id)
                    switch.async_turn_on(self.hass, self.heater_entity_id)

    @property
    def _is_device_active(self):
        """If the toggleable device is currently active."""
        return switch.is_on(self.hass, self.heater_entity_id)
