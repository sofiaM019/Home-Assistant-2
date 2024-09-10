"""Data coordinator for WeatherFlow Cloud Data."""

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta

from aiohttp import ClientResponseError
from weatherflow4py.api import WeatherFlowRestAPI
from weatherflow4py.models.rest.stations import StationsResponseREST
from weatherflow4py.models.rest.unified import WeatherFlowDataREST
from weatherflow4py.models.ws.obs import WebsocketObservation
from weatherflow4py.models.ws.websocket_request import (
    ListenStartMessage,
    RapidWindListenStartMessage,
)
from weatherflow4py.models.ws.websocket_response import EventDataRapidWind, RapidWindWS
from weatherflow4py.ws import WeatherFlowWebsocketAPI

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util.ssl import client_context

from .const import DOMAIN, LOGGER


@dataclass
class CallbackMapping:
    """Mapping class for callbacks."""

    station_id: int
    device_id: int


class WeatherFlowCloudDataUpdateCoordinator(
    DataUpdateCoordinator[dict[int, WeatherFlowDataREST]]
):
    """Class to manage fetching REST Based WeatherFlow Forecast data."""

    def __init__(self, hass: HomeAssistant, api_token: str) -> None:
        """Initialize global WeatherFlow forecast data updater."""
        self.weather_api = WeatherFlowRestAPI(
            api_token=api_token, session=async_get_clientsession(hass)
        )
        self._token = api_token
        self._wind_callbacks: dict[int, dict[str, Callable]] = {}
        self._observation_callbacks: dict[int, dict[str, Callable]] = {}
        self.mapping_ids: list[CallbackMapping] = []

        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=60),
        )

    async def _async_setup(self) -> None:
        """Set up the WeatherFlow API."""

        # Setup blockign context
        ssl_context = client_context()

        async with self.weather_api:
            try:
                stations: StationsResponseREST = (
                    await self.weather_api.async_get_stations()
                )
            except ClientResponseError as err:
                if err.status == 401:
                    raise ConfigEntryAuthFailed(err) from err
                raise UpdateFailed(f"Update failed: {err}") from err

        self.mapping_ids = [
            CallbackMapping(x.station_id, x.outdoor_devices[0].device_id)
            for x in stations.stations
        ]
        for mapping in self.mapping_ids:
            api = WeatherFlowWebsocketAPI(str(mapping.device_id), self._token)

            await api.connect(ssl_context)
            await asyncio.gather(
                api.send_message(ListenStartMessage(device_id=str(mapping.device_id))),
                api.send_message(
                    RapidWindListenStartMessage(device_id=str(mapping.device_id))
                ),
            )
            api.register_wind_callback(self._wind_cb)
            api.register_observation_callback(self._observation_cb)

    async def _observation_cb(self, observation: WebsocketObservation):
        """Define a callback for observation (obs_st) events."""

        device_id = observation.device_id
        if device_id in self._observation_callbacks:
            for key, cb in self._observation_callbacks[device_id].items():
                LOGGER.debug(f"Calling Callback for Device ID: {device_id} - {key}")
                cb(observation)
            LOGGER.debug(
                "No [OBSERVATION] Callbacks Registered for Device ID: %s", device_id
            )

    async def _wind_cb(self, data: RapidWindWS):
        """Define callback for wind events."""
        device_id = data.device_id
        value: EventDataRapidWind = data.ob
        if device_id in self._wind_callbacks:
            for key, cb in self._wind_callbacks[device_id].items():
                LOGGER.debug(f"Calling Callback for Device ID: {device_id} - {key}")
                cb(value)
        else:
            LOGGER.debug("No [WIND] Callbacks Registered for Device ID: %s", device_id)

    def register_wind_callback(self, device_id: int, key: str, callback: Callable):
        """Register a callback for the 'rapid_wind' event."""
        LOGGER.info("Registering Callback for Device ID: %s %s", device_id, key)
        if self._wind_callbacks.get(device_id):
            self._wind_callbacks[device_id][key] = callback
        else:
            self._wind_callbacks[device_id] = {key: callback}

    def register_observation_callback(
        self, device_id: int, key: str, callback: Callable
    ):
        """Register a callback for the 'obs_st' event."""

        LOGGER.info("Registering Callback for Device ID: %s %s", device_id, key)
        if self._observation_callbacks.get(device_id):
            self._observation_callbacks[device_id][key] = callback
        else:
            self._observation_callbacks[device_id] = {key: callback}

    async def _async_update_data(self) -> dict[int, WeatherFlowDataREST]:
        """Update rest data."""
        try:
            async with self.weather_api:
                return await self.weather_api.get_all_data()
        except ClientResponseError as err:
            if err.status == 401:
                raise ConfigEntryAuthFailed(err) from err
            raise UpdateFailed(f"Update failed: {err}") from err
