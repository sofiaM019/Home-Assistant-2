"""Support for Soma Covers."""
import logging

import logging

from requests import RequestException

from homeassistant.components.cover import (
    ATTR_POSITION,
    ATTR_TILT_POSITION,
    DEVICE_CLASS_BLIND,
    DEVICE_CLASS_SHADE,
    SUPPORT_CLOSE,
    SUPPORT_CLOSE_TILT,
    SUPPORT_OPEN,
    SUPPORT_OPEN_TILT,
    SUPPORT_SET_POSITION,
    SUPPORT_SET_TILT_POSITION,
    SUPPORT_STOP,
    SUPPORT_STOP_TILT,
    CoverEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import API, DEVICES, DOMAIN, SomaEntity

from .utils import is_api_response_success

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Soma cover platform."""

    devices = hass.data[DOMAIN][DEVICES]
    entities = []

    for device in devices:
        # Assume a shade device if the type is not present in the api response (Connect <2.2.6)
        if "type" in device and device["type"].lower() == "tilt":
            entities.append(SomaTilt(device, hass.data[DOMAIN][API]))
        else:
            entities.append(SomaShade(device, hass.data[DOMAIN][API]))

    async_add_entities(entities, True)


class SomaTilt(SomaEntity, CoverEntity):
    """Representation of a Soma Tilt device."""

    _attr_device_class = DEVICE_CLASS_BLIND
    _attr_supported_features = (
        SUPPORT_OPEN_TILT
        | SUPPORT_CLOSE_TILT
        | SUPPORT_STOP_TILT
        | SUPPORT_SET_TILT_POSITION
    )

    @property
    def current_cover_tilt_position(self):
        """Return the current cover tilt position."""
        return self.current_position

    @property
    def is_closed(self):
        """Return if the cover tilt is closed."""
        return self.current_position == 0

    def close_cover_tilt(self, **kwargs):
        """Close the cover tilt."""
        response = self.api.set_shade_position(self.device["mac"], 100)
        if is_api_response_success(response):
            self.set_position(0)
        else:
            raise HomeAssistantError(
                f'Error while closing the cover ({self.name}): {response["msg"]}'
            )

    def open_cover_tilt(self, **kwargs):
        """Open the cover tilt."""
        response = self.api.set_shade_position(self.device["mac"], -100)
        if is_api_response_success(response):
            self.set_position(100)
        else:
            raise HomeAssistantError(
                f'Error while opening the cover ({self.name}): {response["msg"]}'
            )

    def stop_cover_tilt(self, **kwargs):
        """Stop the cover tilt."""
        response = self.api.stop_shade(self.device["mac"])
        if is_api_response_success(response):
            # Set cover position to some value where up/down are both enabled
            self.set_position(50)
        else:
            raise HomeAssistantError(
                f'Error while stopping the cover ({self.name}): {response["msg"]}'
            )

    def set_cover_tilt_position(self, **kwargs):
        """Move the cover tilt to a specific position."""
        # 0 -> Closed down (api: 100)
        # 50 -> Fully open (api: 0)
        # 100 -> Closed up (api: -100)
        target_api_position = 100 - ((kwargs[ATTR_TILT_POSITION] / 50) * 100)
        response = self.api.set_shade_position(self.device["mac"], target_api_position)
        if is_api_response_success(response):
            self.set_position(kwargs[ATTR_TILT_POSITION])
        else:
            raise HomeAssistantError(
                f'Error while setting the cover position ({self.name}): {response["msg"]}'
            )

    async def async_update(self):
        """Update the entity with the latest data."""
        try:
            _LOGGER.debug("Soma Tilt Update")
            response = await self.hass.async_add_executor_job(
                self.api.get_shade_state, self.device["mac"]
            )
            if not self.api_is_available:
                self.api_is_available = True
                _LOGGER.info("Connection to SOMA Connect succeeded")
        except RequestException:
            if self.api_is_available:
                _LOGGER.warning("Connection to SOMA Connect failed")
                self.api_is_available = False
            return

        if not is_api_response_success(response):
            if self.is_available:
                self.is_available = False
                _LOGGER.warning(
                    f'Device is unreachable ({self.name}). Error while fetching the state: {response["msg"]}'
                )
            return

        if not self.is_available:
            self.is_available = True
            _LOGGER.info(f"Device {self.name} is now reachable")

        api_position = int(response["position"])

        if "closed_upwards" in response.keys():
            self.current_position = 50 + ((api_position * 50) / 100)
        else:
            self.current_position = 50 - ((api_position * 50) / 100)


class SomaShade(SomaEntity, CoverEntity):
    """Representation of a Soma Shade device."""

    _attr_device_class = DEVICE_CLASS_SHADE
    _attr_supported_features = (
        SUPPORT_OPEN | SUPPORT_CLOSE | SUPPORT_STOP | SUPPORT_SET_POSITION
    )

    @property
    def current_cover_position(self):
        """Return the current cover position."""
        return self.current_position

    @property
    def is_closed(self):
        """Return if the cover is closed."""
        return self.current_position == 0

    def close_cover(self, **kwargs):
        """Close the cover."""
        response = self.api.set_shade_position(self.device["mac"], 100)
        if not is_api_response_success(response):
            raise HomeAssistantError(
                f'Error while closing the cover ({self.name}): {response["msg"]}'
            )

    def open_cover(self, **kwargs):
        """Open the cover."""
        response = self.api.set_shade_position(self.device["mac"], 0)
        if not is_api_response_success(response):
            raise HomeAssistantError(
                f'Error while opening the cover ({self.name}): {response["msg"]}'
            )

    def stop_cover(self, **kwargs):
        """Stop the cover."""
        response = self.api.stop_shade(self.device["mac"])
        if is_api_response_success(response):
            # Set cover position to some value where up/down are both enabled
            self.set_position(50)
        else:
            raise HomeAssistantError(
                f'Error while stopping the cover ({self.name}): {response["msg"]}'
            )

    def set_cover_position(self, **kwargs):
        """Move the cover shutter to a specific position."""
        self.current_position = kwargs[ATTR_POSITION]
        response = self.api.set_shade_position(
            self.device["mac"], 100 - kwargs[ATTR_POSITION]
        )
        if not is_api_response_success(response):
            raise HomeAssistantError(
                f'Error while setting the cover position ({self.name}): {response["msg"]}'
            )

    async def async_update(self):
        """Update the cover with the latest data."""
        try:
            _LOGGER.debug("Soma Shade Update")
            response = await self.hass.async_add_executor_job(
                self.api.get_shade_state, self.device["mac"]
            )
            if not self.api_is_available:
                self.api_is_available = True
                _LOGGER.info("Connection to SOMA Connect succeeded")
        except RequestException:
            if self.api_is_available:
                _LOGGER.warning("Connection to SOMA Connect failed")
                self.api_is_available = False
            return

        if not is_api_response_success(response):
            if self.is_available:
                self.is_available = False
                _LOGGER.warning(
                    f'Device is unreachable ({self.name}). Error while fetching the state: {response["msg"]}'
                )
            return

        if not self.is_available:
            self.is_available = True
            _LOGGER.info(f"Device {self.name} is now reachable")

        self.current_position = 100 - int(response["position"])
