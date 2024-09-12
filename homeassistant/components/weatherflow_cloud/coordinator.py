"""Data coordinators."""

from dataclasses import dataclass
from datetime import timedelta
from typing import Generic, TypeVar

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

T = TypeVar("T")


@dataclass
class CallbackMapping:
    """Mapping class for callbacks."""

    station_id: int
    device_id: int


class BaseWeatherFlowCoordinator(DataUpdateCoordinator[T], Generic[T]):
    """Base class for WeatherFlow coordinators."""

    def __init__(
        self,
        hass: HomeAssistant,
        token: str,
        stations: StationsResponseREST,
        websocket_api: WeatherFlowWebsocketAPI,
        name: str,
    ) -> None:
        """Initialize Coordinator."""
        self.token = token
        self.stations: StationsResponseREST = stations
        self._session = async_get_clientsession(hass)
        self._ssl_context = client_context()

        self.device_to_station_map: dict[int, int] = self.stations.device_station_map
        self.device_ids = list(self.device_to_station_map.keys())
        self.api = websocket_api

        super().__init__(
            hass,
            LOGGER,
            name=name,
            always_update=False,
        )

    async def _async_setup(self) -> None:
        """Set up the coordinator."""
        LOGGER.debug(f"Setup {self.__class__.__name__} with token: {self.token}")
        await self.api.connect(self._ssl_context)


class WeatherFlowCloudDataUpdateCoordinatorWebsocketObservation(
    BaseWeatherFlowCoordinator[dict[int, dict[int, WebsocketObservation]]]
):
    """Websocket coordinator for observations."""

    def __init__(
        self,
        hass: HomeAssistant,
        token: str,
        stations: StationsResponseREST,
        websocket_api: WeatherFlowWebsocketAPI,
    ) -> None:
        """Initialize Coordinator."""
        super().__init__(hass, token, stations, websocket_api, DOMAIN)
        self._ws_data: dict[int, dict[int, WebsocketObservation]] = {
            station: {device: None for device in devices}
            for station, devices in self.stations.station_device_map.items()
        }

    async def _observation_callback(self, data: WebsocketObservation):
        """Define callback for observation events."""
        device_id = data.device_id
        station_id = self.device_to_station_map[device_id]
        self._ws_data[station_id][device_id] = data
        LOGGER.debug(f"Updated Observation Data for: {station_id}:{device_id} = {data}")
        self.async_set_updated_data(self._ws_data)

    async def _async_setup(self) -> None:
        await super()._async_setup()
        self.api.register_observation_callback(self._observation_callback)
        for device_id in self.device_ids:
            await self.api.send_message(ListenStartMessage(device_id=str(device_id)))


class WeatherFlowCloudDataUpdateCoordinatorWebsocketWind(
    BaseWeatherFlowCoordinator[dict[int, dict[int, EventDataRapidWind]]]
):
    """Websocket coordinator for wind."""

    def __init__(
        self,
        hass: HomeAssistant,
        token: str,
        stations: StationsResponseREST,
        websocket_api: WeatherFlowWebsocketAPI,
    ) -> None:
        """Initialize Coordinator."""
        super().__init__(hass, token, stations, websocket_api, DOMAIN)
        self._ws_data: dict[int, dict[int, EventDataRapidWind]] = {
            station: {device: None for device in devices}
            for station, devices in self.stations.station_device_map.items()
        }

    async def _rapid_wind_callback(self, data: RapidWindWS):
        """Define callback for wind events."""
        device_id = data.device_id
        station_id = self.device_to_station_map[device_id]
        self._ws_data[station_id][device_id] = data.ob
        LOGGER.debug(f"Updated Wind Data for: {station_id}:{device_id} = {data.ob}")
        self.async_set_updated_data(self._ws_data)

    async def _async_setup(self) -> None:
        await super()._async_setup()
        self.api.register_wind_callback(self._rapid_wind_callback)
        for device_id in self.device_ids:
            await self.api.send_message(
                RapidWindListenStartMessage(device_id=str(device_id))
            )


class WeatherFlowCloudDataUpdateCoordinatorREST(
    DataUpdateCoordinator[dict[int, WeatherFlowDataREST]]
):
    """Class to manage fetching REST Based WeatherFlow Forecast data."""

    def __init__(self, hass: HomeAssistant, api_token: str) -> None:
        """Initialize global WeatherFlow forecast data updater."""
        self.weather_api = WeatherFlowRestAPI(
            api_token=api_token, session=async_get_clientsession(hass)
        )
        self._token = api_token

        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=60),
        )

    async def _async_update_data(self) -> dict[int, WeatherFlowDataREST]:
        """Update rest data."""
        try:
            async with self.weather_api:
                return await self.weather_api.get_all_data()
        except ClientResponseError as err:
            if err.status == 401:
                raise ConfigEntryAuthFailed(err) from err
            raise UpdateFailed(f"Update failed: {err}") from err
