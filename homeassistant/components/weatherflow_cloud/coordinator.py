"""Data coordinator for WeatherFlow Cloud Data."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta

from aiohttp import ClientResponseError
from weatherflow4py.api import WeatherFlowRestAPI
from weatherflow4py.models.rest.stations import StationsResponseREST
from weatherflow4py.models.rest.unified import WeatherFlowDataREST
from weatherflow4py.models.ws.websocket_request import RapidWindListenStartMessage
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
        self._callbacks: dict[int, dict[str, Callable]] = {}
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

            await api.send_message(
                RapidWindListenStartMessage(device_id=str(mapping.device_id))
            )

            api.register_wind_callback(self._wind_cb)

    async def _wind_cb(self, data: RapidWindWS):
        """Define callback for wind events."""
        device_id = data.device_id
        value: EventDataRapidWind = data.ob
        if device_id in self._callbacks:
            for key, cb in self._callbacks[device_id].items():
                LOGGER.debug(f"Calling Callback for Device ID: {device_id} - {key}")
                cb(value)
        else:
            LOGGER.info("No [WIND] Callbacks Registered for Device ID: %s", device_id)

        # self.data.websocket_wind_data[key] = value

    def register_callback(self, device_id: int, key: str, callback: Callable):
        """Register a callback for the 'rapid_wind' event."""

        LOGGER.info("Registering Callback for Device ID: %s %s", device_id, key)
        if self._callbacks.get(device_id):
            self._callbacks[device_id][key] = callback
        else:
            self._callbacks[device_id] = {key: callback}

    async def _async_update_data(self) -> dict[int, WeatherFlowDataREST]:
        """Update rest data."""
        try:
            async with self.weather_api:
                return await self.weather_api.get_all_data()
        except ClientResponseError as err:
            if err.status == 401:
                raise ConfigEntryAuthFailed(err) from err
            raise UpdateFailed(f"Update failed: {err}") from err
