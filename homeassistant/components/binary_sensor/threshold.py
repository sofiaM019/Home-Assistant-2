"""
Support for monitoring if a sensor value is below/above a threshold.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.threshold/
"""
import asyncio
import logging

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.binary_sensor import (
    BinarySensorDevice, PLATFORM_SCHEMA, DEVICE_CLASSES_SCHEMA)
from homeassistant.const import (
    CONF_NAME, CONF_ENTITY_ID, STATE_UNKNOWN, ATTR_ENTITY_ID,
    CONF_DEVICE_CLASS)
from homeassistant.core import callback
from homeassistant.helpers.event import async_track_state_change

_LOGGER = logging.getLogger(__name__)

ATTR_HYSTERESIS = 'hysteresis'
ATTR_POSITION = "position"
ATTR_SENSOR_VALUE = 'sensor_value'
ATTR_LOWER = 'lower'
ATTR_UPPER = 'upper'
ATTR_TYPE = 'type'

CONF_HYSTERESIS = 'hysteresis'
CONF_LOWER = 'lower'
CONF_UPPER = 'upper'

DEFAULT_NAME = 'Threshold'
DEFAULT_HYSTERESIS = 0.0

POSITION_SENSOR_UNKNOWN = "sensor value unknown"
POSITION_BELOW = "below"
POSITION_IN_RANGE = "in range"
POSITION_ABOVE = "above"

TYPE_UPPER = 'upper'
TYPE_RANGE = 'range'
TYPE_LOWER = 'lower'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_ENTITY_ID): cv.entity_id,
    vol.Optional(CONF_LOWER): vol.Coerce(float),
    vol.Optional(CONF_UPPER): vol.Coerce(float),
    vol.Optional(
        CONF_HYSTERESIS, default=DEFAULT_HYSTERESIS): vol.Coerce(float),
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_DEVICE_CLASS): DEVICE_CLASSES_SCHEMA,
})


@asyncio.coroutine
def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    """Set up the Threshold sensor."""
    entity_id = config.get(CONF_ENTITY_ID)
    name = config.get(CONF_NAME)
    lower = config.get(CONF_LOWER)
    upper = config.get(CONF_UPPER)
    hysteresis = config.get(CONF_HYSTERESIS)
    device_class = config.get(CONF_DEVICE_CLASS)

    async_add_devices([ThresholdSensor(
        hass, entity_id, name, lower, upper, hysteresis, device_class)], True)

    return True


class ThresholdSensor(BinarySensorDevice):
    """Representation of a Threshold sensor."""

    def __init__(self, hass, entity_id, name, lower, upper, hysteresis,
                 device_class):
        """Initialize the Threshold sensor."""
        self._hass = hass
        self._entity_id = entity_id
        self._name = name
        self._threshold_lower = lower
        self._threshold_upper = upper
        self._hysteresis = hysteresis
        self._device_class = device_class

        self._state_position = None
        self._state = False
        self.sensor_value = None

        @callback
        # pylint: disable=invalid-name
        def async_threshold_sensor_state_listener(
                entity, old_state, new_state):
            """Handle sensor state changes."""
            try:
                self.sensor_value = None if new_state.state == STATE_UNKNOWN \
                    else float(new_state.state)
            except (ValueError, TypeError):
                self.sensor_value = None
                _LOGGER.warning("State is not numerical")

            hass.async_add_job(self.async_update_ha_state, True)

        async_track_state_change(
            hass, entity_id, async_threshold_sensor_state_listener)

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def is_on(self):
        """Return true if sensor is on."""
        return self._state

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def device_class(self):
        """Return the sensor class of the sensor."""
        return self._device_class

    @property
    def threshold_type(self):
        """Return the type of threshold this sensor represents."""
        if self._threshold_lower and self._threshold_upper:
            return TYPE_RANGE
        elif self._threshold_lower:
            return TYPE_LOWER
        elif self._threshold_upper:
            return TYPE_UPPER

    @property
    def device_state_attributes(self):
        """Return the state attributes of the sensor."""
        return {
            ATTR_ENTITY_ID: self._entity_id,
            ATTR_SENSOR_VALUE: self.sensor_value,
            ATTR_POSITION: self._state_position,
            ATTR_LOWER: self._threshold_lower,
            ATTR_UPPER: self._threshold_upper,
            ATTR_HYSTERESIS: self._hysteresis,
            ATTR_TYPE: self.threshold_type
        }

    @asyncio.coroutine
    def async_update(self):
        """Get the latest data and updates the states."""
        def below(threshold):
            """Determine if the sensor value is below a threshold."""
            return self.sensor_value < (threshold - self._hysteresis)

        def above(threshold):
            """Determine if the sensor value is above a threshold."""
            return self.sensor_value > (threshold + self._hysteresis)

        if self.sensor_value is None:
            self._state_position = POSITION_SENSOR_UNKNOWN
            self._state = False

        elif self.threshold_type == TYPE_LOWER:
            if below(self._threshold_lower):
                self._state_position = POSITION_BELOW
                self._state = True
            elif above(self._threshold_lower):
                self._state_position = POSITION_ABOVE
                self._state = False

        elif self.threshold_type == TYPE_UPPER:
            if above(self._threshold_upper):
                self._state_position = POSITION_ABOVE
                self._state = True
            elif below(self._threshold_upper):
                self._state_position = POSITION_BELOW
                self._state = False

        elif self.threshold_type == TYPE_RANGE:
            if below(self._threshold_lower):
                self._state_position = POSITION_BELOW
                self._state = False
            if above(self._threshold_upper):
                self._state_position = POSITION_ABOVE
                self._state = False
            elif above(self._threshold_lower) and below(self._threshold_upper):
                self._state_position = POSITION_IN_RANGE
                self._state = True
