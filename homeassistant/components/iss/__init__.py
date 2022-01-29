"""The iss component."""
from __future__ import annotations

from datetime import datetime, timedelta
import logging
from typing import TypedDict

import pyiss
import requests
from requests.exceptions import HTTPError

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.BINARY_SENSOR]


class IssData(TypedDict):
    """Typed dict representation of data returned from pyiss."""

    number_of_people_in_space: int
    current_location: dict[str, str]
    is_above: bool
    next_rise: datetime


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up this integration using UI."""

    hass.data.setdefault(DOMAIN, {})
    latitude = hass.config.latitude
    longitude = hass.config.longitude

    iss = pyiss.ISS()

    async def async_update() -> IssData:
        try:
            return IssData(
                number_of_people_in_space=await hass.async_add_executor_job(
                    iss.number_of_people_in_space
                ),
                current_location=await hass.async_add_executor_job(
                    iss.current_location
                ),
                is_above=await hass.async_add_executor_job(
                    iss.is_ISS_above, latitude, longitude
                ),
                next_rise=await hass.async_add_executor_job(
                    iss.next_rise, latitude, longitude
                ),
            )
        except (HTTPError, requests.exceptions.ConnectionError) as ex:
            raise UpdateFailed("Unable to retrieve data") from ex

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=async_update,
        update_interval=timedelta(seconds=60),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN] = coordinator

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        del hass.data[DOMAIN]
    return unload_ok
