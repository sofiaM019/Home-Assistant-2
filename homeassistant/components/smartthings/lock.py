"""
Support for locks through the SmartThings cloud API.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/smartthings.lock/
"""
from homeassistant.components.lock import LockDevice

from . import SmartThingsEntity
from .const import DATA_BROKERS, DOMAIN

DEPENDENCIES = ['smartthings']

ST_STATE_LOCKED = 'locked'
ST_LOCK_ATTR_MAP = {
    'method': 'method',
    'codeId': 'code_id',
    'timeout': 'timeout'
}


async def async_setup_platform(hass, config, async_add_entities,
                               discovery_info=None):
    """Platform uses config entry setup."""
    pass


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add locks for a config entry."""
    broker = hass.data[DOMAIN][DATA_BROKERS][config_entry.entry_id]
    async_add_entities(
        [SmartThingsLock(device) for device in broker.devices.values()
         if is_lock(device)])


def is_lock(device):
    """Determine if the device supports the lock capability."""
    from pysmartthings import Capability
    return Capability.lock in device.capabilities


class SmartThingsLock(SmartThingsEntity, LockDevice):
    """Define a SmartThings lock."""

    async def async_lock(self, **kwargs):
        """Lock the device."""
        await self._device.lock(set_status=True)
        self.async_schedule_update_ha_state()

    async def async_unlock(self, **kwargs):
        """Unlock the device."""
        await self._device.unlock(set_status=True)
        self.async_schedule_update_ha_state()

    @property
    def is_locked(self):
        """Return true if lock is locked."""
        return self._device.status.lock == ST_STATE_LOCKED

    @property
    def device_state_attributes(self):
        """Return device specific state attributes."""
        from pysmartthings import Attribute
        state_attrs = {}
        status = self._device.status.attributes[Attribute.lock]
        if status.value:
            state_attrs['lock_state'] = status.value
        if type(status.data) is dict:
            for st_attr, ha_attr in ST_LOCK_ATTR_MAP.items():
                data_val = status.data.get(st_attr)
                if data_val:
                    state_attrs[ha_attr] = data_val
        return state_attrs
