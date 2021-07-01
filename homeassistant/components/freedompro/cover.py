"""Support for Freedompro cover."""
import json

from pyfreedompro import put_state

from homeassistant.components.cover import (
    ATTR_POSITION,
    DEVICE_CLASS_BLIND,
    DEVICE_CLASS_DOOR,
    DEVICE_CLASS_GARAGE,
    DEVICE_CLASS_GATE,
    DEVICE_CLASS_WINDOW,
    SUPPORT_SET_POSITION,
    CoverEntity,
)
from homeassistant.const import CONF_API_KEY
from homeassistant.core import callback
from homeassistant.helpers import aiohttp_client
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Freedompro cover."""
    api_key = entry.data[CONF_API_KEY]
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        Device(hass, api_key, device, coordinator)
        for device in coordinator.data
        if device["type"] == "windowCovering"
        or device["type"] == "gate"
        or device["type"] == "garageDoor"
        or device["type"] == "door"
        or device["type"] == "window"
    )


class Device(CoordinatorEntity, CoverEntity):
    """Representation of an Freedompro cover."""

    def __init__(self, hass, api_key, device, coordinator):
        """Initialize the Freedompro cover."""
        super().__init__(coordinator)
        self._hass = hass
        self._session = aiohttp_client.async_get_clientsession(self._hass)
        self._api_key = api_key
        self._attr_name = device["name"]
        self._attr_unique_id = device["uid"]
        self._type = device["type"]
        self._characteristics = device["characteristics"]
        self._attr_current_cover_position = 0
        self._attr_is_closed = True
        self._attr_supported_features = SUPPORT_SET_POSITION
        self._attr_device_class = (
            DEVICE_CLASS_GATE
            if self._type == "gate"
            else DEVICE_CLASS_GARAGE
            if self._type == "garageDoor"
            else DEVICE_CLASS_DOOR
            if self._type == "door"
            else DEVICE_CLASS_WINDOW
            if self._type == "window"
            else DEVICE_CLASS_BLIND
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        device = next(
            (
                device
                for device in self.coordinator.data
                if device["uid"] == self._attr_unique_id
            ),
            None,
        )
        if device is not None and "state" in device:
            state = device["state"]
            if "position" in state:
                self._attr_current_cover_position = state["position"]
                self._attr_is_closed = (
                    True if self._attr_current_cover_position == 0 else False
                )
        super()._handle_coordinator_update()

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        self._handle_coordinator_update()

    async def async_set_cover_position(self, **kwargs):
        """Async function to set position to cover."""
        payload = {}
        if ATTR_POSITION in kwargs:
            payload["position"] = kwargs[ATTR_POSITION]
        payload = json.dumps(payload)
        await put_state(
            self._session,
            self._api_key,
            self._attr_unique_id,
            payload,
        )
        await self.coordinator.async_request_refresh()
