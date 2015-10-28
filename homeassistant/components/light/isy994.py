"""
homeassistant.components.light.isy994
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Support for ISY994 lights.
"""
import logging

from homeassistant.components.isy994 import (ISYDeviceABC, ISY, SENSOR_STRING,
                                             HIDDEN_STRING)
from homeassistant.helpers import set_log_severity
from homeassistant.components.light import ATTR_BRIGHTNESS
from homeassistant.const import STATE_ON, STATE_OFF

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_devices, discovery_info=None):
    """ Sets up the ISY994 platform. """
    devs = []

    set_log_severity(hass, config, _LOGGER)

    # verify connection
    if ISY is None or not ISY.connected:
        _LOGGER.error('A connection has not been made to the ISY controller.')
        return False

    # import dimmable nodes
    for (path, node) in ISY.nodes:
        if node.dimmable and SENSOR_STRING not in node.name:
            if HIDDEN_STRING in path:
                node.name += HIDDEN_STRING
            devs.append(ISYLightDevice(node))

    add_devices(devs)


class ISYLightDevice(ISYDeviceABC):
    """ Represents as ISY light. """

    _domain = 'light'
    _dtype = 'analog'
    _attrs = {ATTR_BRIGHTNESS: 'value'}
    _onattrs = [ATTR_BRIGHTNESS]
    _states = [STATE_ON, STATE_OFF]

    def _attr_filter(self, attr):
        """ Filter brightness out of entity while off. """
        if ATTR_BRIGHTNESS in attr and not self.is_on:
            del attr[ATTR_BRIGHTNESS]
        return attr
