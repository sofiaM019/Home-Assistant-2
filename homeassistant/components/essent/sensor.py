"""Support for Essent API."""
from datetime import timedelta

from pyessent import PyEssent
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_PASSWORD, CONF_USERNAME, ENERGY_KILO_WATT_HOUR)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

SCAN_INTERVAL = timedelta(hours=1)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the Essent platform."""
    username = config[CONF_USERNAME]
    password = config[CONF_PASSWORD]

    essent = EssentBase(username, password)
    add_devices(essent.retrieve_meters(), True)


class EssentBase():
    """Essent Base."""

    def __init__(self, username, password):
        """Initialize the Essent API."""
        self._username = username
        self._password = password
        self._meters = []
        self._meter_data = {}

        self.update()

    def get_session(self):
        """Return the active session."""
        return self._essent

    def retrieve_meters(self):
        """Retrieve the IDs of the meters used by Essent."""
        meters = []
        for meter in self._meters:
            data = self._meter_data[meter]
            self._meter_data[meter] = data
            for tariff in data['values']['LVR'].keys():
                meters.append(EssentMeter(
                    self,
                    meter,
                    data['type'],
                    tariff,
                    data['values']['LVR'][tariff]['unit']))

        return meters

    def retrieve_meter_data(self, meter):
        """Retrieve the data for this meter."""
        return self._meter_data[meter]

    @Throttle(timedelta(minutes=30))
    def update(self):
        """Retrieve the latest meter data from Essent."""
        essent = PyEssent(self._username, self._password)
        self._meters = essent.get_EANs()
        for meter in self._meters:
            self._meter_data[meter] = essent.read_meter(
                meter, only_last_meter_reading=True)


class EssentMeter(Entity):
    """Representation of Essent measurements."""

    def __init__(self, essent_base, meter, meter_type, tariff, unit):
        """Initialize the sensor."""
        self._state = None
        self._essent_base = essent_base
        self._meter = meter
        self._type = meter_type
        self._tariff = tariff
        self._unit = unit

    @property
    def name(self):
        """Return the name of the sensor."""
        return "Essent {} ({})".format(self._type, self._tariff)

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        if self._unit.lower() == 'kwh':
            return ENERGY_KILO_WATT_HOUR

        return self._unit

    def update(self):
        """Fetch the energy usage."""
        # Ensure our data isn't too old
        self._essent_base.update()

        # Retrieve our meter
        data = self._essent_base.retrieve_meter_data(self._meter)

        # Set our value
        self._state = next(
            iter(data['values']['LVR'][self._tariff]['records'].values()))
