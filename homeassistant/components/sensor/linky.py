"""
Support for Linky.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/sensor.linky/
"""
import logging
import json
from datetime import timedelta

import voluptuous as vol

from homeassistant.const import CONF_USERNAME, CONF_PASSWORD, CONF_TIMEOUT
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle
import homeassistant.helpers.config_validation as cv

REQUIREMENTS = ['pylinky==0.1.6']
_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=10)
DEFAULT_TIMEOUT = 10

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): cv.positive_int,
})


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Configure the platform and add the Linky sensor."""
    username = config[CONF_USERNAME]
    password = config[CONF_PASSWORD]
    timeout = config[CONF_TIMEOUT]

    devices = [LinkySensor('Linky', username, password)]
    add_entities(devices, True)


class LinkySensor(Entity):
    """Representation of a sensor entity for Linky."""

    def __init__(self, name, username, password):
        """Initialize the sensor."""
        self._name = name
        self._username = username
        self._password = password
        self._state = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return 'kWh'

    @Throttle(SCAN_INTERVAL)
    def update(self):
        """Fetch new state data for the sensor."""
        from pylinky.client import LinkyClient, PyLinkyError

        client = LinkyClient(self._username, self._password)
        try:
            client.fetch_data()
        except PyLinkyError as exp:
            _LOGGER.error(exp)
            return

        _LOGGER.debug(json.dumps(client.get_data(), indent=2))

        if client.get_data():
            # get the last past day data
            self._state = client.get_data()['daily'][-2]['conso']
        else:
            self._state = None
