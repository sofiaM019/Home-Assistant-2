"""Data coordinators."""

from datetime import timedelta

from aiohttp import ClientResponseError
from weatherflow4py.api import WeatherFlowRestAPI
from weatherflow4py.models.rest.stations import StationsResponseREST
from weatherflow4py.models.rest.unified import WeatherFlowDataREST
from weatherflow4py.models.ws.obs import WebsocketObservation
from weatherflow4py.models.ws.types import EventType
from weatherflow4py.models.ws.websocket_request import (
    ListenStartMessage,
    RapidWindListenStartMessage,
)
from weatherflow4py.models.ws.websocket_response import (
    EventDataRapidWind,
    ObservationTempestWS,
    RapidWindWS,
)
from weatherflow4py.ws import WeatherFlowWebsocketAPI

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util.ssl import client_context

from .const import DOMAIN, LOGGER


class BaseWeatherFlowCoordinator[T](DataUpdateCoordinator[dict[int, T]]):
    """Base class for WeatherFlow coordinators."""

    # Define static variables
    # _session: ClientSession
    # _ssl_context: SSLContext
    # _rest_api: WeatherFlowRestAPI
    # stations: StationsResponseREST | None = None
    # device_to_station_map: dict[int, int] = {}
    # device_ids: list[int] = []

    def __init__(
        self,
        hass: HomeAssistant,
        rest_api: WeatherFlowRestAPI,
        stations: StationsResponseREST,
        update_interval: timedelta | None = None,
        always_update: bool = False,
    ) -> None:
        """Initialize Coordinator."""
        self._token = rest_api.api_token
        self._rest_api = rest_api
        self.stations = stations
        LOGGER.error(f"🌮️  {self}")
        LOGGER.error(f"🌮️  {dir(stations)}")
        LOGGER.error(f"🌮️  {stations}")
        LOGGER.error(f"🌮️  {stations}")
        self.device_to_station_map = stations.device_station_map

        self.device_ids = list(stations.device_station_map.keys())

        self._ssl_context = client_context()

        # # Use these variables as static
        # if not hasattr(BaseWeatherFlowCoordinator, "_session"):
        #     BaseWeatherFlowCoordinator._session = async_get_clientsession(hass)
        # if not hasattr(BaseWeatherFlowCoordinator, "_ssl_context"):
        #     BaseWeatherFlowCoordinator._ssl_context = client_context()
        #
        # # Initialize the API once
        # if not hasattr(BaseWeatherFlowCoordinator, "_rest_api"):
        #     BaseWeatherFlowCoordinator._rest_api = WeatherFlowRestAPI(
        #         api_token=self._token, session=BaseWeatherFlowCoordinator._session
        #     )

        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            always_update=always_update,
            update_interval=update_interval,
        )

    def get_station_name(self, station_id: int):
        """Define a default implementation - that should always be overridden."""
        return "UNSET"


class WeatherFlowCloudUpdateCoordinatorREST(
    BaseWeatherFlowCoordinator[WeatherFlowDataREST]
):
    """Class to manage fetching REST Based WeatherFlow Forecast data."""

    def __init__(
        self,
        hass: HomeAssistant,
        rest_api: WeatherFlowRestAPI,
        stations: StationsResponseREST,
    ) -> None:
        """Initialize global WeatherFlow forecast data updater."""

        super().__init__(
            hass,
            rest_api,
            stations,
            update_interval=timedelta(seconds=60),
            always_update=True,
        )

    async def _async_update_data(self) -> dict[int, WeatherFlowDataREST]:
        """Update rest data."""
        try:
            async with self._rest_api:
                return await self._rest_api.get_all_data()
        except ClientResponseError as err:
            if err.status == 401:
                raise ConfigEntryAuthFailed(err) from err
            raise UpdateFailed(f"Update failed: {err}") from err

    def get_station(self, station_id: int):
        """Return station for id."""
        return self.data[station_id]

    def get_station_name(self, station_id: int):
        """Return station name for id."""
        return self.data[station_id].station.name


class WeatherFlowCloudDataCallbackCoordinator[
    T: EventDataRapidWind | WebsocketObservation,
    M: RapidWindListenStartMessage | ListenStartMessage,
    C: RapidWindWS | ObservationTempestWS,
](BaseWeatherFlowCoordinator[dict[int, T | None]]):
    """A Generic coordinator to handle Websocket connections."""

    def __init__(
        self,
        hass: HomeAssistant,
        rest_api: WeatherFlowRestAPI,
        websocket_api: WeatherFlowWebsocketAPI,
        stations: StationsResponseREST,
        listen_request_type: type[M],
        event_type: EventType,
    ) -> None:
        """Initialize Coordinator."""

        super().__init__(hass=hass, rest_api=rest_api, stations=stations)

        self._event_type = event_type
        self.websocket_api = websocket_api
        self._listen_request_type = listen_request_type

        # pre-initialize ws data
        self._ws_data: dict[int, dict[int, T | None]] = {
            station: {device: None for device in devices}
            for station, devices in self.stations.station_device_map.items()
        }

    async def _generic_callback(self, data: C):
        device_id = data.device_id
        station_id = self.device_to_station_map[device_id]
        self._ws_data[station_id][device_id] = getattr(data, "ob", data)
        self.async_set_updated_data(self._ws_data)

    async def _async_setup(self) -> None:
        LOGGER.error(f"Setup {self.__class__.__name__} with token: {self._token}")
        await self.websocket_api.connect(self._ssl_context)
        # Register callback
        self.websocket_api._register_callback(  # noqa:SLF001
            message_type=self._event_type,
            callback=self._generic_callback,
        )
        # Subscribe to messages
        for device_id in self.device_ids:
            await self.websocket_api.send_message(
                self._listen_request_type(device_id=str(device_id))
            )
            LOGGER.error(f"Sending listen request for {self.__class__.__name__}")

    def get_station(self, station_id: int):
        """Return station for id."""
        return self.stations.stations[station_id]

    def get_station_name(self, station_id: int) -> str:
        """Return station name for id."""
        if name := self.stations.station_map[station_id].name:
            return name
        return ""

        #
        # class WeatherFlowCloudDataUpdateCoordinatorObservation(
        #     BaseWeatherFlowCoordinator[dict[int, WebsocketObservation]]
        # ):
        #     """A Generic coordinator to handle Websocket connections."""
        #
        #     def __init__(
        #         self,
        #         hass: HomeAssistant,
        #         token: str,
        #         stations: StationsResponseREST,
        #         websocket_api: WeatherFlowWebsocketAPI,
        #     ) -> None:
        #         """Initialize Coordinator."""
        #         super().__init__(hass=hass, token=token)
        #         self.stations = stations
        #         self.websocket_api = websocket_api
        #
        #         self._ws_data: dict[int, dict[int, WebsocketObservation]] = {
        #             station: {device: None for device in devices}
        #             for station, devices in self.stations.station_device_map.items()
        #         }
        #
        #
        #
        #     async def _observation_callback(self, data: WebsocketObservation):
        #         """Define callback for observation events."""
        #         device_id = data.device_id
        #         station_id = self.device_to_station_map[device_id]
        #         self._ws_data[station_id][device_id] = data
        #         LOGGER.debug(f"Updated Observation Data for: {station_id}:{device_id} = {data}")
        #         self.async_set_updated_data(self._ws_data)
        #
        #     # async def _async_setup(self) -> None:
        #     #     """Set up the coordinator."""
        #     #     LOGGER.debug(f"Setup {self.__class__.__name__} with token: {self.token}")
        #     #
        #
        #     async def _async_setup(self) -> None:
        #         await self.api.connect(self._ssl_context)
        #
        #         # Register callback
        # self.api.register_observation_callback(self._observation_callback)


#         # Subscribe to messages
#         for device_id in self.device_ids:
#             await self.api.send_message(ListenStartMessage(device_id=str(device_id)))
#
#
# class WeatherFlowCloudDataCoordinatorWind(
#     BaseWeatherFlowCoordinator[dict[int, EventDataRapidWind]]
# ):
#     """Websocket coordinator for wind."""
#
#     def __init__(
#         self,
#         hass: HomeAssistant,
#         token: str,
#         # Optional Fields
#         stations: StationsResponseREST,
#         websocket_api: WeatherFlowWebsocketAPI,
#     ) -> None:
#         """Initialize Coordinator."""
#         super().__init__(hass=hass, token=token)
#
#         self.stations = stations
#         self.websocket_api = websocket_api
#
#         self._ws_data: dict[int, dict[int, EventDataRapidWind]] = {
#             station: {device: None for device in devices}
#             for station, devices in self.stations.station_device_map.items()
#         }
#
#     async def _rapid_wind_callback(self, data: RapidWindWS):
#         """Define callback for wind events."""
#         device_id = data.device_id
#         station_id = self.device_to_station_map[device_id]
#         self._ws_data[station_id][device_id] = data.ob
#         LOGGER.debug(f"Updated Wind Data for: {station_id}:{device_id} = {data.ob}")
#         self.async_set_updated_data(self._ws_data)
#
#     async def _async_setup(self) -> None:
#         # Connect the socket -> this is likely duplicate code we should fix
#         await self.api.connect(self._ssl_context)
#         # Register callback
#         self.api.register_wind_callback(self._rapid_wind_callback)
#         # Send listen Request
#         for device_id in self.device_ids:
#             await self.api.send_message(
#                 RapidWindListenStartMessage(device_id=str(device_id))
#             )
#
