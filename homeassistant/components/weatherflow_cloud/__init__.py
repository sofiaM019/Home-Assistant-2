"""The WeatherflowCloud integration."""

from __future__ import annotations

from dataclasses import dataclass

from weatherflow4py.models.rest.stations import StationsResponseREST

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_TOKEN, Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN, LOGGER
from .coordinator import (
    WeatherFlowCloudDataUpdateCoordinatorREST,
    WeatherFlowCloudDataUpdateCoordinatorWebsocketWind,
)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.WEATHER]


@dataclass
class WeatherFlowCoordinators:
    """Data Class for Entry Data."""

    rest: WeatherFlowCloudDataUpdateCoordinatorREST
    wind: WeatherFlowCloudDataUpdateCoordinatorWebsocketWind


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up WeatherFlowCloud from a config entry."""

    LOGGER.debug("Initializing WeatherFlowCloudDataUpdateCoordinatorREST coordinator")
    rest_data_coordinator = WeatherFlowCloudDataUpdateCoordinatorREST(
        hass=hass,
        api_token=entry.data[CONF_API_TOKEN],
    )

    # Make sure its setup
    await rest_data_coordinator.async_config_entry_first_refresh()

    # Query the weather API for a list of devices
    stations: StationsResponseREST = (
        await rest_data_coordinator.weather_api.async_get_stations()
    )

    # Construct Websocket Coordinators
    LOGGER.debug(
        "Initializing WeatherFlowCloudDataUpdateCoordinatorWebsocketWind coordinator"
    )
    websocket_wind_coordinator = WeatherFlowCloudDataUpdateCoordinatorWebsocketWind(
        hass=hass,
        token=entry.data[CONF_API_TOKEN],
        stations=stations,
    )
    # Run setup method.
    await websocket_wind_coordinator._async_setup()  # noqa: SLF001

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = WeatherFlowCoordinators(
        rest_data_coordinator, websocket_wind_coordinator
    )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
