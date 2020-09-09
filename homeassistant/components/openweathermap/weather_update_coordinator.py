"""Weather data coordinator for the OpenWeatherMap (OWM) service."""
from datetime import timedelta
import logging

import async_timeout
from pyowm.commons.exceptions import APIRequestError, UnauthorizedError

from homeassistant.components.weather import (
    ATTR_FORECAST_CONDITION,
    ATTR_FORECAST_PRECIPITATION,
    ATTR_FORECAST_TEMP,
    ATTR_FORECAST_TEMP_LOW,
    ATTR_FORECAST_TIME,
    ATTR_FORECAST_WIND_BEARING,
    ATTR_FORECAST_WIND_SPEED,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    ATTR_API_CLOUDS,
    ATTR_API_CONDITION,
    ATTR_API_FORECAST,
    ATTR_API_HUMIDITY,
    ATTR_API_PRESSURE,
    ATTR_API_RAIN,
    ATTR_API_SNOW,
    ATTR_API_TEMPERATURE,
    ATTR_API_WEATHER,
    ATTR_API_WEATHER_CODE,
    ATTR_API_WIND_BEARING,
    ATTR_API_WIND_SPEED,
    CONDITION_CLASSES,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class WeatherUpdateCoordinator(DataUpdateCoordinator):
    """Weather data update coordinator."""

    def __init__(self, owm, latitude, longitude, forecast_mode, hass):
        """Initialize coordinator."""
        self._owm_client = owm
        self._latitude = latitude
        self._longitude = longitude
        self._forecast_mode = forecast_mode
        if forecast_mode == "freedaily":
            # Auto convert to One Call for freedaily users
            self._forecast_mode = "onecall_daily"
        self._forecast_limit = None
        if forecast_mode == "daily":
            self._forecast_limit = 15

        self._weather_update_interval = timedelta(minutes=5)
        if forecast_mode == "freedaily":
            self._weather_update_interval = 30

        super().__init__(
            hass, _LOGGER, name=DOMAIN, update_interval=self._weather_update_interval
        )

    async def _async_update_data(self):
        data = {}
        with async_timeout.timeout(20):
            try:
                weather_response = await self._get_owm_weather()
                data = self._convert_weather_response(weather_response)
            except (APIRequestError, UnauthorizedError) as error:
                raise UpdateFailed(error) from error
        return data

    async def _get_owm_weather(self):
        weather = None
        if (
            self._forecast_mode == "onecall_hourly"
            or self._forecast_mode == "onecall_daily"
        ):
            weather = await self.hass.async_add_executor_job(
                self._owm_client.one_call, self._latitude, self._longitude
            )
        else:
            current_weather = await self.hass.async_add_executor_job(
                self._owm_client.weather_at_coords, self._latitude, self._longitude
            )
            interval = "daily"
            if self._forecast_mode == "hourly":
                interval = "3h"
            forecast = await self.hass.async_add_executor_job(
                self._owm_client.forecast_at_coords,
                self._latitude,
                self._longitude,
                interval,
                self._forecast_limit,
            )
            weather = LegacyWeather(current_weather.weather, forecast.forecast.weathers)

        return weather

    def _convert_weather_response(self, weather_response):
        current_weather = weather_response.current

        forecast_weather = []
        forecast_arg = "forecast"
        if self._forecast_mode == "onecall_hourly":
            forecast_arg = "forecast_hourly"
        elif self._forecast_mode == "onecall_daily":
            forecast_arg = "forecast_daily"
        forecast_weather = [
            self._convert_forecast(x) for x in getattr(weather_response, forecast_arg)
        ]

        return {
            ATTR_API_TEMPERATURE: current_weather.temperature("celsius").get("temp"),
            ATTR_API_PRESSURE: current_weather.pressure.get("press"),
            ATTR_API_HUMIDITY: current_weather.humidity,
            ATTR_API_WIND_BEARING: current_weather.wind().get("deg"),
            ATTR_API_WIND_SPEED: current_weather.wind().get("speed"),
            ATTR_API_CLOUDS: current_weather.clouds,
            ATTR_API_RAIN: self._get_rain(current_weather.rain),
            ATTR_API_SNOW: self._get_snow(current_weather.snow),
            ATTR_API_WEATHER: current_weather.detailed_status,
            ATTR_API_CONDITION: self._get_condition(current_weather.weather_code),
            ATTR_API_WEATHER_CODE: current_weather.weather_code,
            ATTR_API_FORECAST: forecast_weather,
        }

    def _convert_forecast(self, entry):
        forecast = {
            ATTR_FORECAST_TIME: entry.reference_time("unix") * 1000,
            ATTR_FORECAST_PRECIPITATION: self._calc_precipitation(
                entry.rain, entry.snow
            ),
            ATTR_FORECAST_WIND_SPEED: entry.wind().get("speed"),
            ATTR_FORECAST_WIND_BEARING: entry.wind().get("deg"),
            ATTR_FORECAST_CONDITION: self._get_condition(entry.weather_code),
        }

        temperature_dict = entry.temperature("celsius")
        if "max" in temperature_dict and "min" in temperature_dict:
            forecast[ATTR_FORECAST_TEMP] = entry.temperature("celsius").get("max")
            forecast[ATTR_FORECAST_TEMP_LOW] = entry.temperature("celsius").get("min")
        elif "temp" in temperature_dict:
            forecast[ATTR_FORECAST_TEMP] = entry.temperature("celsius").get("temp")

        return forecast

    @staticmethod
    def _get_rain(rain):
        if "all" in rain:
            return round(rain["all"], 0)
        return "not raining"

    @staticmethod
    def _get_snow(snow):
        if snow:
            return round(snow["all"], 0)
        return "not snowing"

    @staticmethod
    def _calc_precipitation(rain, snow):
        """Calculate the precipitation."""
        rain_value = 0 if rain.get("all", None) is None else rain.get("all", None)
        snow_value = 0 if snow.get("all", None) is None else snow.get("all", None)
        if round(rain_value + snow_value, 1) == 0:
            return None
        return round(rain_value + snow_value, 1)

    @staticmethod
    def _get_condition(weather_code):
        return [k for k, v in CONDITION_CLASSES.items() if weather_code in v][0]


class LegacyWeather:
    """Class to harmonize weather data model for hourly, daily and One Call APIs."""

    def __init__(self, current_weather, forecast):
        """Initialize weather object."""
        self.current = current_weather
        self.forecast = forecast
