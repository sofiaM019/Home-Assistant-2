"""Support for August lock."""
import logging

from august.activity import ActivityType
from august.lock import LockStatus
from august.util import update_lock_detail_from_activity

from homeassistant.components.lock import LockDevice
from homeassistant.const import ATTR_BATTERY_LEVEL
from homeassistant.core import callback

from .const import DATA_AUGUST, DOMAIN
from .entity import AugustEntityMixin

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up August locks."""
    data = hass.data[DOMAIN][config_entry.entry_id][DATA_AUGUST]
    devices = []

    for lock in data.locks:
        _LOGGER.debug("Adding lock for %s", lock.device_name)
        devices.append(AugustLock(data, lock))

    async_add_entities(devices, True)


class AugustLock(AugustEntityMixin, LockDevice):
    """Representation of an August lock."""

    def __init__(self, data, device):
        """Initialize the lock."""
        super().__init__(data, device)
        self._data = data
        self._device = device
        self._lock_status = None
        self._changed_by = None
        self._available = False

    async def async_lock(self, **kwargs):
        """Lock the device."""
        await self._call_lock_operation(self._data.lock)

    async def async_unlock(self, **kwargs):
        """Unlock the device."""
        await self._call_lock_operation(self._data.unlock)

    async def _call_lock_operation(self, lock_operation):
        activities = await self.hass.async_add_executor_job(
            lock_operation, self._device_id
        )
        detail = self._detail
        for lock_activity in activities:
            update_lock_detail_from_activity(detail, lock_activity)

        if self._update_lock_status_from_detail():
            _LOGGER.debug(
                "async_signal_device_id_update (from lock operation): %s",
                self._device_id,
            )
            await self._data.async_signal_device_id_update(self._device_id)

    def _update_lock_status_from_detail(self):
        detail = self._detail
        lock_status = detail.lock_status
        self._available = detail.bridge_is_online

        if self._lock_status != lock_status:
            self._lock_status = lock_status
            return True
        return False

    @callback
    def _update_from_data(self):
        """Get the latest state of the sensor and update activity."""
        lock_detail = self._detail
        lock_activity = self._data.activity_stream.get_latest_device_activity(
            self._device_id, [ActivityType.LOCK_OPERATION]
        )

        if lock_activity is not None:
            self._changed_by = lock_activity.operated_by
            update_lock_detail_from_activity(lock_detail, lock_activity)

        self._update_lock_status_from_detail()
        self.async_write_ha_state()

    @property
    def name(self):
        """Return the name of this device."""
        return self._device.device_name

    @property
    def available(self):
        """Return the availability of this sensor."""
        return self._available

    @property
    def is_locked(self):
        """Return true if device is on."""
        if self._lock_status is None or self._lock_status is LockStatus.UNKNOWN:
            return None
        return self._lock_status is LockStatus.LOCKED

    @property
    def changed_by(self):
        """Last change triggered by."""
        return self._changed_by

    @property
    def device_state_attributes(self):
        """Return the device specific state attributes."""
        attributes = {ATTR_BATTERY_LEVEL: self._detail.battery_level}

        if self._detail.keypad is not None:
            attributes["keypad_battery_level"] = self._detail.keypad.battery_level

        return attributes

    @property
    def unique_id(self) -> str:
        """Get the unique id of the lock."""
        return f"{self._device_id:s}_lock"
