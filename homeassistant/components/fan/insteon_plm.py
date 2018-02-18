"""
Support for INSTEON fans via PowerLinc Modem.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/insteon_plm/
"""
import logging
import asyncio

from homeassistant.core import callback
from homeassistant.components.fan import (SPEED_OFF,
                                          SPEED_LOW,
                                          SPEED_MEDIUM,
                                          SPEED_HIGH,
                                          FanEntity,
                                          SUPPORT_SET_SPEED)
from homeassistant.const import STATE_OFF
from homeassistant.loader import get_component

DEPENDENCIES = ['insteon_plm']

SPEED_TO_HEX = {SPEED_OFF: 0x00,
                SPEED_LOW: 0x3f,
                SPEED_MEDIUM: 0xbe,
                SPEED_HIGH: 0xff}

_LOGGER = logging.getLogger(__name__)


@asyncio.coroutine
def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    """Set up the INSTEON PLM device class for the hass platform."""

    state_list = []
    plm = hass.data['insteon_plm']

    for deviceInfo in discovery_info:
        address = deviceInfo['address']
        device = plm.devices[address]
        stateKey = deviceInfo['stateKey']

        state_list.append(InsteonPLMFan(hass,
                                        device,
                                        stateKey,
                                        SUPPORT_SET_SPEED))

    async_add_devices(state_list)


class InsteonPLMFan(FanEntity):
    """An INSTEON fan component."""

    def __init__(self, hass, device, stateKey,
                 supported_features: int, ) -> None:
        """Initialize the entity."""
        self._hass = hass
        self._state = device.states[stateKey]
        self._device = device
        self._supported_features = supported_features

        self._state.register_updates(self.async_fan_update)

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def address(self):
        """Return the address of the node."""
        return self._device.address.human

    @property
    def name(self):
        """Return the name of the node. (used for Entity_ID)"""
        name = ''
        if self._state.group == 0x01:
            name = self._device.id
        else:
            name = '{:s}_{:d}'.format(self._device.id, self._state.group)
        return name

    @property
    def device_state_attributes(self):
        """Provide attributes for display on device card."""
        insteon_plm = get_component('insteon_plm')
        return insteon_plm.common_attributes(self._device, self._state)

    @property
    def speed(self) -> str:
        """Return the current speed."""
        return self._hex_to_speed(self._state.value)

    @property
    def speed_list(self) -> list:
        """Get the list of available speeds."""
        return [STATE_OFF, SPEED_LOW, SPEED_MEDIUM, SPEED_HIGH]

    def async_turn_on(self, speed: str = None, **kwargs) -> None:
        """Turn on the entity."""
        if speed is None:
            speed = SPEED_MEDIUM
        self.async_set_speed(speed)

    def async_turn_off(self, **kwargs) -> None:
        """Turn off the entity."""
        self.async_set_speed(SPEED_OFF)

    def async_set_speed(self, speed: str) -> None:
        """Set the speed of the fan."""
        fanSpeed = SPEED_TO_HEX[speed]
        if fanSpeed == 0x00:
            self._state.off()
        else:
            self._state.set_level(fanSpeed)

    @callback
    def async_fan_update(self, deviceid, statename, val):
        """Receive notification from transport that new data exists."""
        self.hass.async_add_job(self.async_update_ha_state())

    @property
    def supported_features(self) -> int:
        """Flag supported features."""
        return self._supported_features

    @staticmethod
    def _hex_to_speed(speed: int):
        hex_speed = SPEED_OFF
        if speed > 0xfe:
            hex_speed = SPEED_HIGH
        elif speed > 0x7f:
            hex_speed = SPEED_MEDIUM
        elif speed > 0:
            hex_speed = SPEED_LOW
        return hex_speed
