"""Demo lock platform that has two fake locks."""
import asyncio

from homeassistant.components.lock import SUPPORT_OPEN, LockEntity
from homeassistant.const import (
    STATE_JAMMED,
    STATE_LOCKED,
    STATE_LOCKING,
    STATE_UNLOCKED,
    STATE_UNLOCKING,
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Demo lock platform."""
    async_add_entities(
        [
            DemoLock("Front Door", STATE_LOCKED),
            DemoLock("Kitchen Door", STATE_UNLOCKED),
            DemoLock("Poorly Installed Door", STATE_LOCKED, False, True),
            DemoLock("Openable Lock", STATE_LOCKED, True),
        ]
    )


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Demo config entry."""
    await async_setup_platform(hass, {}, async_add_entities)


class DemoLock(LockEntity):
    """Representation of a Demo lock."""

    def __init__(self, name, state, openable=False, jam_on_operation=False):
        """Initialize the lock."""
        self._name = name
        self._state = state
        self._openable = openable
        self._jam_on_operation = jam_on_operation

    @property
    def should_poll(self):
        """No polling needed for a demo lock."""
        return False

    @property
    def name(self):
        """Return the name of the lock if any."""
        return self._name

    @property
    def is_locking(self):
        """Return true if lock is locking."""
        return self._state == STATE_LOCKING

    @property
    def is_unlocking(self):
        """Return true if lock is unlocking."""
        return self._state == STATE_LOCKING

    @property
    def is_jammed(self):
        """Return true if lock is jammed."""
        return self._state == STATE_JAMMED

    @property
    def is_locked(self):
        """Return true if lock is locked."""
        return self._state == STATE_LOCKED

    async def async_lock(self, **kwargs):
        """Lock the device."""
        self._state = STATE_LOCKING
        self.async_write_ha_state()
        await asyncio.sleep(5)
        if self._jam_on_operation:
            self._state = STATE_JAMMED
            self.async_write_ha_state()
            await asyncio.sleep(5)
        self._state = STATE_UNLOCKED
        self.async_write_ha_state()

    async def async_unlock(self, **kwargs):
        """Unlock the device."""
        self._state = STATE_UNLOCKING
        self.async_write_ha_state()
        await asyncio.sleep(5)
        if self._jam_on_operation:
            self._state = STATE_JAMMED
            self.async_write_ha_state()
            await asyncio.sleep(5)
        self._state = STATE_UNLOCKED
        self.async_write_ha_state()

    async def async_open(self, **kwargs):
        """Open the door latch."""
        self._state = STATE_UNLOCKED
        self.async_write_ha_state()

    @property
    def supported_features(self):
        """Flag supported features."""
        if self._openable:
            return SUPPORT_OPEN
