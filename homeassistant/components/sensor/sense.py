"""
Support for monitoring a Sense energy sensor.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.sense/
"""
import logging

from datetime import timedelta

from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle
from homeassistant.components.sense import SENSE_DATA

REQUIREMENTS = ['sense']

_LOGGER = logging.getLogger(__name__)

ACTIVE_NAME = 'Energy'
PRODUCTION_NAME = 'Production'
CONSUMPTION_NAME = 'Usage'

ACTIVE_TYPE = 'active'


class SensorConfig:
    """Data structure holding sensor config."""

    def __init__(self, name, sensor_type):
        """Sensor name and type to pass to API."""
        self.name = name
        self.sensor_type = sensor_type


# Sensor types/ranges
SENSOR_TYPES = {'active': SensorConfig(ACTIVE_NAME, ACTIVE_TYPE),
                'daily': SensorConfig('Daily', 'DAY'),
                'weekly': SensorConfig('Weekly', 'WEEK'),
                'monthly': SensorConfig('Monthly', 'MONTH'),
                'yearly': SensorConfig('Yearly', 'YEAR')}

# Production/consumption variants
SENSOR_VARIANTS = [PRODUCTION_NAME.lower(), CONSUMPTION_NAME.lower()]

ICON = 'mdi:flash'

MIN_TIME_BETWEEN_DAILY_UPDATES = timedelta(seconds=300)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Sense sensor."""
    if SENSE_DATA not in hass.data:
        _LOGGER.error("Requires Sense component loaded")
        return False
    data = hass.data[SENSE_DATA]

    @Throttle(MIN_TIME_BETWEEN_DAILY_UPDATES)
    def update_trends():
        """Update the daily power usage."""
        data.update_trend_data()

    def update_active():
        """Update the active power usage."""
        data.get_realtime()

    devices = []
    for typ in SENSOR_TYPES.values():
        for var in SENSOR_VARIANTS:
            name = typ.name
            sensor_type = typ.sensor_type
            is_production = var == PRODUCTION_NAME.lower()
            if sensor_type == ACTIVE_TYPE:
                update_call = update_active
            else:
                update_call = update_trends
            devices.append(Sense(data, name, sensor_type,
                                 is_production, update_call))

    add_entities(devices)


class Sense(Entity):
    """Implementation of a Sense energy sensor."""

    def __init__(self, data, name, sensor_type, is_production, update_call):
        """Initialize the sensor."""
        name_type = PRODUCTION_NAME if is_production else CONSUMPTION_NAME
        self._name = "%s %s" % (name, name_type)
        self._data = data
        self._sensor_type = sensor_type
        self.update_sensor = update_call
        self._is_production = is_production
        self._state = None

        if sensor_type == ACTIVE_TYPE:
            self._unit_of_measurement = 'W'
        else:
            self._unit_of_measurement = 'kWh'

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self._unit_of_measurement

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return ICON

    def update(self):
        """Get the latest data, update state."""
        from sense_energy import SenseAPITimeoutException
        try:
            self.update_sensor()
        except SenseAPITimeoutException:
            _LOGGER.error("Timeout retrieving data")
            return

        if self._sensor_type == ACTIVE_TYPE:
            if self._is_production:
                self._state = round(self._data.active_solar_power)
            else:
                self._state = round(self._data.active_power)
        else:
            state = self._data.get_trend(self._sensor_type,
                                         self._is_production)
            self._state = round(state, 1)
