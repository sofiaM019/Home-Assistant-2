"""
Support for INSTEON dimmers via PowerLinc Modem.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/insteon_plm/
"""
import logging
import asyncio

from homeassistant.core import callback
from homeassistant.components.switch import (SwitchDevice)
from homeassistant.loader import get_component

DEPENDENCIES = ['insteon_plm']

_LOGGER = logging.getLogger(__name__)


@asyncio.coroutine
def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    """Set up the INSTEON PLM device class for the hass platform."""

    device_list = []
    for device in discovery_info:

        _LOGGER.info('Registered %s with switch platform.', device.id)

        device_list.append(
            InsteonPLMSwitchDevice(hass, device)
        )

    async_add_devices(device_list)


class InsteonPLMSwitchDevice(SwitchDevice):
    """A Class for an Insteon device."""

    def __init__(self, hass, device):
        """Initialize the switch."""
        self._hass = hass
        self._device = device

        self._device.lightOnLevel.connect(self.async_switch_update)

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def address(self):
        """Return the address of the node."""
        return self._device.address.human

    @property
    def id(self):
        """Return the name of the node."""
        return self._device.id

    @property
    def name(self):
        """Return the name of the node. (used for Entity_ID)"""
        return self._device.id

    @property
    def is_on(self):
        """Return the boolean response if the node is on."""
        if self._device.cat == 0x07: # I/O Linc
            onlevel = self._device.relay.value
        else:
            onlevel = self._device.lightOnLevel.value
        _LOGGER.debug('on level for %s is %s', self._device.id, onlevel)
        return bool(onlevel)

    @property
    def device_state_attributes(self):
        """Provide attributes for display on device card."""
        insteon_plm = get_component('insteon_plm')
        return insteon_plm.common_attributes(self._device)

    @callback
    def async_switch_update(self, deviceid, statename, val):
        """Receive notification from transport that new data exists."""
        _LOGGER.info('Received update calback from PLM for %s', self._device.id)
        self._hass.async_add_job(self.async_update_ha_state())

    @asyncio.coroutine
    def async_turn_on(self, **kwargs):
        """Turn device on."""
        if self._device.cat == 0x07: # I/O Linc
            self._device.relay_open()
        else:
            self._device.light_on()

    @asyncio.coroutine
    def async_turn_off(self, **kwargs):
        """Turn device off"""
        if self._device.cat == 0x07: # I/O Linc
            self._device.relay_close()
        else:
            self._device.light_off()
