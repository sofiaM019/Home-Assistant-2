"""
Support for Tuya switch.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/switch.tuya/
"""
from homeassistant.components.switch import SwitchDevice
from homeassistant.components.tuya import (
    DOMAIN as TUYA_DOMAIN, DATA_TUYA, SIGNAL_DELETE_ENTITY,
    SIGNAL_UPDATE_ENTITY, TuyaDevice)
from homeassistant.helpers.dispatcher import async_dispatcher_connect

DEPENDENCIES = ['tuya']

DEVICE_TYPE = 'switch'


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up Tuya Switch device."""
    tuya = hass.data[DATA_TUYA]
    if discovery_info is None:
        return
    dev_ids = discovery_info.get('dev_ids')
    devices = []
    for dev_id in dev_ids:
        device = tuya.get_device_by_id(dev_id)
        if device is None:
            continue
        devices.append(TuyaSwitch(device))
    add_devices(devices)


class TuyaSwitch(TuyaDevice, SwitchDevice):
    """Tuya Switch Device."""

    def __init__(self, tuya):
        """Init Tuya switch device."""
        super().__init__(tuya)
        self.entity_id = DEVICE_TYPE + '.' + tuya.object_id()

    async def async_added_to_hass(self):
        """Call when entity is added to hass."""
        dev_id = self.tuya.object_id()
        self.hass.data[TUYA_DOMAIN]['entities'][dev_id] = self.entity_id
        async_dispatcher_connect(
            self.hass, SIGNAL_DELETE_ENTITY, self._delete_callback)
        async_dispatcher_connect(
            self.hass, SIGNAL_UPDATE_ENTITY, self._update_callback)

    @property
    def is_on(self):
        """Return true if switch is on."""
        return self.tuya.state()

    def turn_on(self, **kwargs):
        """Turn the switch on."""
        self.tuya.turn_on()

    def turn_off(self, **kwargs):
        """Turn the device off."""
        self.tuya.turn_off()
