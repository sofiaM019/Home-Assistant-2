"""
Component to retrieve uptime for Home Assistant.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.uptime/
"""

import logging

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
import homeassistant.util.dt as dt_util
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_NAME
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = 'Uptime'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the Version sensor platform."""
    name = config.get(CONF_NAME)
    add_devices([UptimeSensor(name)])


class UptimeSensor(Entity):
    """Representation of an uptime sensor."""

    def __init__(self, name):
        """Initialize the Version sensor."""
        self._name = name
        self._icon = 'mdi:clock'
        self._units = 'days'
        self.initial = dt_util.now()
        self._state = 0

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def icon(self):
        """Icon to display in the front end."""
        return self._icon

    @property
    def unit_of_measurement(self):
        """Retrun the unit of measurement the value is expressed in."""
        return self._units

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    def update(self):
        """Update the state of the sensor."""
        delta = dt_util.now() - self.initial
        delta_in_days = delta.total_seconds() / (3600 * 24)
        self._state = round(delta_in_days, 2)
        _LOGGER.debug("New value: %s", delta_in_days)
