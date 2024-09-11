"""Entity definition."""

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTR_ATTRIBUTION, DOMAIN, MANUFACTURER
from .coordinator import (
    WeatherFlowCloudDataUpdateCoordinatorREST,
    WeatherFlowCloudDataUpdateCoordinatorWebsocketWind,
)


class WeatherFlowCloudEntity(
    CoordinatorEntity[
        WeatherFlowCloudDataUpdateCoordinatorREST
        | WeatherFlowCloudDataUpdateCoordinatorWebsocketWind
    ]
):
    """Base entity class for WeatherFlow Cloud integration."""

    _attr_attribution = ATTR_ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: WeatherFlowCloudDataUpdateCoordinatorREST
        | WeatherFlowCloudDataUpdateCoordinatorWebsocketWind,
        station_id: int,
    ) -> None:
        """Class initializer."""
        super().__init__(coordinator)
        self.station_id = station_id

        if isinstance(coordinator, WeatherFlowCloudDataUpdateCoordinatorREST):
            station_name = coordinator.data[station_id].station.name
        else:
            station_name = coordinator.stations.station_map[station_id].name

        self._attr_device_info = DeviceInfo(
            name=station_name,
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, str(station_id))},
            manufacturer=MANUFACTURER,
            configuration_url=f"https://tempestwx.com/station/{station_id}/grid",
        )

    @property
    def station(self):
        """Individual Station data."""
        if isinstance(self.coordinator, WeatherFlowCloudDataUpdateCoordinatorREST):
            return self.coordinator.data[self.station_id]
        return self.coordinator.stations[self.station_id]
