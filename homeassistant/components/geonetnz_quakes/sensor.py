"""Feed Entity Manager Sensor support for GeoNet NZ Quakes Feeds."""
import logging
from typing import Optional

from homeassistant.components.geonetnz_quakes import DOMAIN, FEED
from homeassistant.components.geonetnz_quakes.geo_location import SIGNAL_STATUS
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

ATTR_ENTRY_ID = "entry_id"
ATTR_STATUS = "status"
ATTR_LAST_UPDATE = "last_update"
ATTR_LAST_UPDATE_SUCCESSFUL = "last_update_successful"
ATTR_LAST_TIMESTAMP = "last_timestamp"
ATTR_CREATED = "created"
ATTR_UPDATED = "updated"
ATTR_REMOVED = "removed"


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the GeoNet NZ Quakes Feed platform."""
    sensor = GeonetnzQuakesSensor(entry.entry_id, entry.title)
    async_add_entities([sensor])


class GeonetnzQuakesSensor(Entity):
    def __init__(self, config_entry_id, config_title):
        """Initialize entity."""
        self._config_entry_id = config_entry_id
        self._config_title = config_title
        self._status = None
        self._last_update = None
        self._last_update_successful = None
        self._last_timestamp = None
        self._total = None
        self._created = None
        self._updated = None
        self._removed = None
        self._remove_signal_status = None

    async def async_added_to_hass(self):
        """Call when entity is added to hass."""
        self._remove_signal_status = async_dispatcher_connect(
            self.hass,
            SIGNAL_STATUS.format(self._config_entry_id),
            self._update_status_callback,
        )
        _LOGGER.debug("Waiting for updates %s", self._config_entry_id)
        # First update is manual because of how the feed entity manager is updated.
        await self.async_update()

    async def async_will_remove_from_hass(self) -> None:
        """Call when entity will be removed from hass."""
        self._remove_signal_status()

    @callback
    def _update_status_callback(self):
        """Call status update method."""
        _LOGGER.debug("Received status update for %s", self._config_entry_id)
        self.async_schedule_update_ha_state(True)

    @property
    def should_poll(self):
        """No polling needed for GeoNet NZ Quakes status sensor."""
        return False

    async def async_update(self):
        """Update this entity from the data held in the feed manager."""
        _LOGGER.debug("Updating %s", self._config_entry_id)
        manager = self.hass.data[DOMAIN][FEED][self._config_entry_id]
        if manager:
            status_info = manager.status_info()
            if status_info:
                self._update_from_status_info(status_info)

    def _update_from_status_info(self, status_info):
        """Update the internal state from the provided information."""
        self._status = status_info.status
        self._last_update = status_info.last_update
        self._last_update_successful = status_info.last_update_successful
        self._last_timestamp = status_info.last_timestamp
        self._total = status_info.total
        self._created = status_info.created
        self._updated = status_info.updated
        self._removed = status_info.removed

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._total

    @property
    def name(self) -> Optional[str]:
        """Return the name of the entity."""
        return f"GeoNet NZ Quakes Status {self._config_title}"

    @property
    def icon(self):
        """Return the icon to use in the frontend, if any."""
        return "mdi:pulse"

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return "entities"

    @property
    def device_state_attributes(self):
        """Return the device state attributes."""
        attributes = {}
        for key, value in (
            (ATTR_STATUS, self._status),
            (ATTR_LAST_UPDATE, self._last_update),
            (ATTR_LAST_UPDATE_SUCCESSFUL, self._last_update_successful),
            (ATTR_LAST_TIMESTAMP, self._last_timestamp),
            (ATTR_CREATED, self._created),
            (ATTR_UPDATED, self._updated),
            (ATTR_REMOVED, self._removed),
            (ATTR_ENTRY_ID, self._config_entry_id),
        ):
            if value or isinstance(value, bool):
                attributes[key] = value
        return attributes
