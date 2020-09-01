"""Support for Met.no weather service."""
import logging

import voluptuous as vol

from homeassistant.components.weather import (
    ATTR_FORECAST_CONDITION,
    ATTR_FORECAST_WIND_BEARING,
    ATTR_WEATHER_CONDITION,
    ATTR_WEATHER_HUMIDITY,
    ATTR_WEATHER_PRESSURE,
    ATTR_WEATHER_TEMPERATURE,
    ATTR_WEATHER_WIND_BEARING,
    ATTR_WEATHER_WIND_SPEED,
    PLATFORM_SCHEMA,
    WeatherEntity,
)
from homeassistant.config_entries import SOURCE_IMPORT
from homeassistant.const import (
    CONF_ELEVATION,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_NAME,
    LENGTH_KILOMETERS,
    LENGTH_MILES,
    PRESSURE_HPA,
    PRESSURE_INHG,
    TEMP_CELSIUS,
)
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.distance import convert as convert_distance
from homeassistant.util.pressure import convert as convert_pressure

from .const import (
    ATTR_MAP,
    COMPASS_CODES,
    CONDITIONS_MAP,
    CONF_TRACK_HOME,
    DOMAIN,
    FORECAST_MAP,
)

_LOGGER = logging.getLogger(__name__)

ATTRIBUTION = (
    "Weather forecast from met.no, delivered by the Norwegian "
    "Meteorological Institute."
)
DEFAULT_NAME = "Met.no"


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Inclusive(
            CONF_LATITUDE, "coordinates", "Latitude and longitude must exist together"
        ): cv.latitude,
        vol.Inclusive(
            CONF_LONGITUDE, "coordinates", "Latitude and longitude must exist together"
        ): cv.longitude,
        vol.Optional(CONF_ELEVATION): int,
    }
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Met.no weather platform."""
    _LOGGER.warning("Loading Met.no via platform config is deprecated")

    # Add defaults.
    config = {CONF_ELEVATION: hass.config.elevation, **config}

    if config.get(CONF_LATITUDE) is None:
        config[CONF_TRACK_HOME] = True

    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_IMPORT}, data=config
        )
    )


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add a weather entity from a config_entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities(
        [
            MetWeather(
                coordinator, config_entry.data, hass.config.units.is_metric, False
            ),
            MetWeather(
                coordinator, config_entry.data, hass.config.units.is_metric, True
            ),
        ]
    )


def compass_degrees_to_code(compass_value: float) -> str:
    """Convert a compass heading in degrees to a 1-3 letter code."""
    compass_degrees = 360.0
    segment_angle = compass_degrees / len(COMPASS_CODES)
    offset = segment_angle / 2.0
    for idx, code in enumerate(COMPASS_CODES):
        angle = segment_angle * idx
        if angle - offset < compass_value < angle + offset:
            return code
    return COMPASS_CODES[0]


def format_condition(condition: str) -> str:
    """Return condition from dict CONDITIONS_MAP."""
    for key, value in CONDITIONS_MAP.items():
        if condition in value:
            return key
    return condition


class MetWeather(CoordinatorEntity, WeatherEntity):
    """Implementation of a Met.no weather condition."""

    def __init__(self, coordinator, config, is_metric, hourly):
        """Initialise the platform with a data instance and site."""
        super().__init__(coordinator)
        self._config = config
        self._is_metric = is_metric
        self._hourly = hourly
        self._name_appendix = "-hourly" if hourly else ""

    @property
    def track_home(self):
        """Return if we are tracking home."""
        return self._config.get(CONF_TRACK_HOME, False)

    @property
    def unique_id(self):
        """Return unique ID."""
        if self.track_home:
            return f"home{self._name_appendix}"

        return f"{self._config[CONF_LATITUDE]}-{self._config[CONF_LONGITUDE]}{self._name_appendix}"

    @property
    def name(self):
        """Return the name of the sensor."""
        name = self._config.get(CONF_NAME)

        if name is not None:
            return f"{name}{self._name_appendix}"

        if self.track_home:
            return f"{self.hass.config.location_name}{self._name_appendix}"

        return f"{DEFAULT_NAME}{self._name_appendix}"

    @property
    def condition(self):
        """Return the current condition."""
        condition = self.coordinator.data.current_weather_data.get(
            ATTR_MAP[ATTR_WEATHER_CONDITION]
        )
        return format_condition(condition)

    @property
    def temperature(self):
        """Return the temperature."""
        return self.coordinator.data.current_weather_data.get(
            ATTR_MAP[ATTR_WEATHER_TEMPERATURE]
        )

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    @property
    def pressure(self):
        """Return the pressure."""
        pressure_hpa = self.coordinator.data.current_weather_data.get(
            ATTR_MAP[ATTR_WEATHER_PRESSURE]
        )
        if self._is_metric or pressure_hpa is None:
            return pressure_hpa

        return round(convert_pressure(pressure_hpa, PRESSURE_HPA, PRESSURE_INHG), 2)

    @property
    def humidity(self):
        """Return the humidity."""
        return self.coordinator.data.current_weather_data.get(
            ATTR_MAP[ATTR_WEATHER_HUMIDITY]
        )

    @property
    def wind_speed(self):
        """Return the wind speed."""
        speed_km_h = self.coordinator.data.current_weather_data.get(
            ATTR_MAP[ATTR_WEATHER_WIND_SPEED]
        )
        if self._is_metric or speed_km_h is None:
            return speed_km_h

        speed_mi_h = convert_distance(speed_km_h, LENGTH_KILOMETERS, LENGTH_MILES)
        return int(round(speed_mi_h))

    @property
    def wind_bearing(self):
        """Return the wind direction."""
        degrees = self.coordinator.data.current_weather_data.get(
            ATTR_MAP[ATTR_WEATHER_WIND_BEARING]
        )
        if degrees is None:
            return
        return compass_degrees_to_code(degrees)

    @property
    def attribution(self):
        """Return the attribution."""
        return ATTRIBUTION

    @property
    def forecast(self):
        """Return the forecast array."""
        if self._hourly:
            met_forecast = self.coordinator.data.hourly_forecast
        else:
            met_forecast = self.coordinator.data.daily_forecast
        ha_forecast = []
        for met_item in met_forecast:
            ha_item = {k: met_item.get(v) for k, v in FORECAST_MAP.items()}
            ha_item[ATTR_FORECAST_CONDITION] = format_condition(
                ha_item[ATTR_FORECAST_CONDITION]
            )
            ha_item[ATTR_FORECAST_WIND_BEARING] = compass_degrees_to_code(
                ha_item[ATTR_FORECAST_WIND_BEARING]
            )
            ha_forecast.append(ha_item)
        return ha_forecast
