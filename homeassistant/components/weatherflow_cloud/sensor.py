"""Sensors for cloud based weatherflow."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from weatherflow4py.models.rest.observation import Observation
from weatherflow4py.models.ws.websocket_response import EventDataRapidWind

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfLength,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.util.dt import UTC

from .const import DOMAIN
from .coordinator import WeatherFlowCloudDataUpdateCoordinator
from .entity import WeatherFlowCloudEntity


@dataclass(frozen=True, kw_only=True)
class WeatherFlowCloudSensorEntityDescription(
    SensorEntityDescription,
):
    """Describes a weatherflow sensor."""

    value_fn: Callable[[Observation], StateType | datetime]


@dataclass(frozen=True, kw_only=True)
class WeatherFlowCloudSensorEntityDescriptionWebsocketWind(
    SensorEntityDescription,
):
    """Describes a weatherflow sensor."""

    value_fn: Callable[[EventDataRapidWind], StateType | datetime]


WEBSOCKET_WIND_SENSORS: tuple[
    WeatherFlowCloudSensorEntityDescriptionWebsocketWind, ...
] = (
    WeatherFlowCloudSensorEntityDescriptionWebsocketWind(
        key="wind_speed",
        translation_key="wind_speed",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.WIND_SPEED,
        suggested_display_precision=1,
        value_fn=lambda data: data.wind_speed_meters_per_second,
        native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
    ),
    WeatherFlowCloudSensorEntityDescriptionWebsocketWind(
        key="wind_direction",
        translation_key="wind_direction",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.wind_direction_degrees,
        native_unit_of_measurement="°",
    ),
)


WF_SENSORS: tuple[WeatherFlowCloudSensorEntityDescription, ...] = (
    # Air Sensors
    WeatherFlowCloudSensorEntityDescription(
        key="air_density",
        translation_key="air_density",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=5,
        value_fn=lambda data: data.air_density,
        native_unit_of_measurement="kg/m³",
    ),
    # Temp Sensors
    WeatherFlowCloudSensorEntityDescription(
        key="air_temperature",
        translation_key="air_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data: data.air_temperature,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    WeatherFlowCloudSensorEntityDescription(
        key="dew_point",
        translation_key="dew_point",
        value_fn=lambda data: data.dew_point,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    WeatherFlowCloudSensorEntityDescription(
        key="feels_like",
        translation_key="feels_like",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data: data.feels_like,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    WeatherFlowCloudSensorEntityDescription(
        key="heat_index",
        translation_key="heat_index",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data: data.heat_index,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    WeatherFlowCloudSensorEntityDescription(
        key="wind_chill",
        translation_key="wind_chill",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data: data.wind_chill,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    WeatherFlowCloudSensorEntityDescription(
        key="wet_bulb_temperature",
        translation_key="wet_bulb_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data: data.wet_bulb_temperature,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    WeatherFlowCloudSensorEntityDescription(
        key="wet_bulb_globe_temperature",
        translation_key="wet_bulb_globe_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data: data.wet_bulb_globe_temperature,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    # Pressure Sensors
    WeatherFlowCloudSensorEntityDescription(
        key="barometric_pressure",
        translation_key="barometric_pressure",
        value_fn=lambda data: data.barometric_pressure,
        native_unit_of_measurement=UnitOfPressure.MBAR,
        device_class=SensorDeviceClass.ATMOSPHERIC_PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=3,
    ),
    WeatherFlowCloudSensorEntityDescription(
        key="sea_level_pressure",
        translation_key="sea_level_pressure",
        value_fn=lambda data: data.sea_level_pressure,
        native_unit_of_measurement=UnitOfPressure.MBAR,
        device_class=SensorDeviceClass.ATMOSPHERIC_PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=3,
    ),
    # Lightning Sensors
    WeatherFlowCloudSensorEntityDescription(
        key="lightning_strike_count",
        translation_key="lightning_strike_count",
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data.lightning_strike_count,
    ),
    WeatherFlowCloudSensorEntityDescription(
        key="lightning_strike_count_last_1hr",
        translation_key="lightning_strike_count_last_1hr",
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data.lightning_strike_count_last_1hr,
    ),
    WeatherFlowCloudSensorEntityDescription(
        key="lightning_strike_count_last_3hr",
        translation_key="lightning_strike_count_last_3hr",
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data.lightning_strike_count_last_3hr,
    ),
    WeatherFlowCloudSensorEntityDescription(
        key="lightning_strike_last_distance",
        translation_key="lightning_strike_last_distance",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        value_fn=lambda data: data.lightning_strike_last_distance,
    ),
    WeatherFlowCloudSensorEntityDescription(
        key="lightning_strike_last_epoch",
        translation_key="lightning_strike_last_epoch",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=(
            lambda data: datetime.fromtimestamp(
                data.lightning_strike_last_epoch, tz=UTC
            )
            if data.lightning_strike_last_epoch is not None
            else None
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up WeatherFlow sensors based on a config entry."""

    coordinator: WeatherFlowCloudDataUpdateCoordinator = hass.data[DOMAIN][
        entry.entry_id
    ]

    async_add_entities(
        WeatherFlowCloudSensor(coordinator, sensor_description, station_id)
        for station_id in coordinator.data
        for sensor_description in WF_SENSORS
    )

    async_add_entities(
        WeatherFlowWebsocketSensorWind(
            coordinator, sensor_description, mapping.station_id, mapping.device_id
        )
        for mapping in coordinator.mapping_ids
        for sensor_description in WEBSOCKET_WIND_SENSORS
    )


class WeatherFlowWebsocketSensorWind(WeatherFlowCloudEntity, SensorEntity):
    """Class for weatherflow wind data."""

    entity_description: WeatherFlowCloudSensorEntityDescriptionWebsocketWind

    def __init__(
        self,
        coordinator: WeatherFlowCloudDataUpdateCoordinator,
        description: WeatherFlowCloudSensorEntityDescriptionWebsocketWind,
        station_id: int,
        device_id: int,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, station_id)
        self._data: EventDataRapidWind | None = None
        self.entity_description = description
        self._attr_unique_id = f"{station_id}_{description.key}"

        coordinator.register_callback(
            device_id, self.entity_description.key, self.update_callback
        )

    @callback
    def update_callback(self, event: EventDataRapidWind) -> None:
        """Signal to HA UpdateReceived."""
        self._data = event
        self.schedule_update_ha_state()

    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
        """Return the state of the sensor."""
        if self._data is None:
            return None
        return self.entity_description.value_fn(self._data)


class WeatherFlowCloudSensor(WeatherFlowCloudEntity, SensorEntity):
    """Implementation of a WeatherFlow sensor."""

    entity_description: WeatherFlowCloudSensorEntityDescription

    def __init__(
        self,
        coordinator: WeatherFlowCloudDataUpdateCoordinator,
        description: WeatherFlowCloudSensorEntityDescription,
        station_id: int,
    ) -> None:
        """Initialize the sensor."""
        # Initialize the Entity Class
        super().__init__(coordinator, station_id)
        self.entity_description = description
        self._attr_unique_id = f"{station_id}_{description.key}"

    @property
    def native_value(self) -> StateType | datetime:
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self.station.observation.obs[0])
