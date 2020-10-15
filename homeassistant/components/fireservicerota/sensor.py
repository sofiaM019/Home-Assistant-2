"""Sensor platform for FireServiceRota integration."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ATTRIBUTION
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.typing import HomeAssistantType

from .const import ATTRIBUTION, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistantType, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up FireServiceRota sensor based on a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    entry_id = entry.entry_id
    unique_id = entry.unique_id

    async_add_entities(
        [IncidentsSensor(data, entry_id, unique_id, "Incidents", "mdi:fire-truck")],
        True,
    )


class IncidentsSensor(RestoreEntity, Entity):
    """Representation of FireServiceRota incidents sensor."""

    def __init__(self, data, entry_id, unique_id, name, icon):
        """Initialize."""
        self._data = data
        self._entry_id = entry_id
        self._unique_id = unique_id
        self._name = name
        self._icon = icon

        self._state = None
        self._state_attributes = {}

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self._name

    @property
    def icon(self) -> str:
        """Return the icon to use in the frontend."""
        return self._icon

    @property
    def state(self) -> str:
        """Return the state of the sensor."""
        return self._state

    @property
    def unique_id(self) -> str:
        """Return the unique ID for this sensor."""
        return f"{self._unique_id}_{self._name}"

    @property
    def device_state_attributes(self) -> object:
        """Return available attributes for sensor."""
        attr = {}
        data = self._state_attributes

        if data:
            for value in (
                "trigger",
                "created_at",
                "message_to_speech_url",
                "prio",
                "type",
                "responder_mode",
                "can_respond_until",
            ):
                if data.get(value):
                    attr[value] = data[value]

            try:
                for address_value in (
                    "latitude",
                    "longitude",
                    "address_type",
                    "formatted_address",
                ):
                    attr[address_value] = data.get("address").get(address_value)
            except (KeyError, AttributeError):
                pass

            attr[ATTR_ATTRIBUTION] = ATTRIBUTION
            return attr

    async def async_added_to_hass(self) -> None:
        """Handle entity which will be added."""
        await super().async_added_to_hass()

        state = await self.async_get_last_state()
        if state:
            self._state = state.state
            self._state_attributes = state.attributes

        self.async_on_remove(self._data.stop_listener)

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{DOMAIN}_{self._entry_id}_update",
                self.async_on_demand_update,
            )
        )

    @property
    def should_poll(self) -> bool:
        """No polling needed."""
        return False

    async def async_on_demand_update(self) -> None:
        """Update state on demand."""
        self.async_schedule_update_ha_state(True)

    async def async_update(self) -> None:
        """Update using FireServiceRota data."""
        if not self.enabled:
            return

        try:
            self._state = self._data.incident_data["body"]
            self._state_attributes = self._data.incident_data
        except (KeyError, TypeError):
            pass

        _LOGGER.debug("Entity '%s' state set to: %s", self._name, self._state)
