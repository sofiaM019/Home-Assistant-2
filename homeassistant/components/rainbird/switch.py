"""Support for Rain Bird Irrigation system LNK WiFi Module."""

import logging

import voluptuous as vol

from homeassistant.components.switch import PLATFORM_SCHEMA, SwitchDevice
from homeassistant.const import (
    CONF_FRIENDLY_NAME,
    CONF_SCAN_INTERVAL,
    CONF_SWITCHES,
    CONF_TRIGGER_TIME,
    CONF_ZONE,
)
from homeassistant.helpers import config_validation as cv
from pyrainbird import RainbirdController

from . import DATA_RAINBIRD

DOMAIN = "rainbird"
_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_SWITCHES, default={}): vol.Schema(
            {
                cv.string: {
                    vol.Optional(CONF_FRIENDLY_NAME): cv.string,
                    vol.Required(CONF_ZONE): cv.string,
                    vol.Required(CONF_TRIGGER_TIME): cv.string,
                    vol.Optional(CONF_SCAN_INTERVAL): cv.string,
                }
            }
        )
    }
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up Rain Bird switches over a Rain Bird controller."""
    controller = hass.data[DATA_RAINBIRD]

    devices = []
    for dev_id, switch in config.get(CONF_SWITCHES).items():
        devices.append(RainBirdSwitch(controller, switch, dev_id))
    add_entities(devices, True)


class RainBirdSwitch(SwitchDevice):
    """Representation of a Rain Bird switch."""

    def __init__(self, rb: RainbirdController, dev, dev_id):
        """Initialize a Rain Bird Switch Device."""
        self._rainbird = rb
        self._devid = dev_id
        self._zone = int(dev.get(CONF_ZONE))
        self._name = dev.get(CONF_FRIENDLY_NAME, f"Sprinkler {self._zone}")
        self._state = None
        self._duration = dev.get(CONF_TRIGGER_TIME)
        self._attributes = {"duration": self._duration, "zone": self._zone}

    @property
    def device_state_attributes(self):
        """Return state attributes."""
        return self._attributes

    @property
    def name(self):
        """Get the name of the switch."""
        return self._name

    def turn_on(self, **kwargs):
        """Turn the switch on."""
        response = self._rainbird.irrigate_zone(int(self._zone), int(self._duration))
        if response and response["type"] == "AcknowledgeResponse":
            self._state = True

    def turn_off(self, **kwargs):
        """Turn the switch off."""
        response = self._rainbird.stop_irrigation()
        if response and response["type"] == "AcknowledgeResponse":
            self._state = False

    def update(self):
        """Update switch status."""
        self._state = self._rainbird.zone_state(self._zone)

    @property
    def is_on(self):
        """Return true if switch is on."""
        return self._state
