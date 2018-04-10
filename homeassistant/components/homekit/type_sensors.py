"""Class to hold all sensor accessories."""
# pylint: disable=attribute-defined-outside-init
import logging

from homeassistant.const import (
    ATTR_UNIT_OF_MEASUREMENT, TEMP_CELSIUS,
    ATTR_DEVICE_CLASS, STATE_ON, STATE_HOME)

from . import TYPES
from .accessories import HomeAccessory, add_preload_service
from .const import (
    CATEGORY_SENSOR, SERV_HUMIDITY_SENSOR, SERV_TEMPERATURE_SENSOR,
    CHAR_CURRENT_HUMIDITY, CHAR_CURRENT_TEMPERATURE, PROP_CELSIUS,
    DEVICE_CLASS_CO2, SERV_CARBON_DIOXIDE_SENSOR, CHAR_CARBON_DIOXIDE_DETECTED,
    DEVICE_CLASS_GAS, SERV_CARBON_MONOXIDE_SENSOR,
    CHAR_CARBON_MONOXIDE_DETECTED,
    DEVICE_CLASS_MOISTURE, SERV_LEAK_SENSOR, CHAR_LEAK_DETECTED,
    DEVICE_CLASS_MOTION, SERV_MOTION_SENSOR, CHAR_MOTION_DETECTED,
    DEVICE_CLASS_OCCUPANCY, SERV_OCCUPANCY_SENSOR, CHAR_OCCUPANCY_DETECTED,
    DEVICE_CLASS_OPENING, SERV_CONTACT_SENSOR, CHAR_CONTACT_SENSOR_STATE,
    DEVICE_CLASS_SMOKE, SERV_SMOKE_SENSOR, CHAR_SMOKE_DETECTED)
from .util import convert_to_float, temperature_to_homekit

_LOGGER = logging.getLogger(__name__)

BINARY_SENSOR_SERVICE_MAP = {
    DEVICE_CLASS_CO2: (SERV_CARBON_DIOXIDE_SENSOR,
                       CHAR_CARBON_DIOXIDE_DETECTED),
    DEVICE_CLASS_GAS: (SERV_CARBON_MONOXIDE_SENSOR,
                       CHAR_CARBON_MONOXIDE_DETECTED),
    DEVICE_CLASS_MOISTURE: (SERV_LEAK_SENSOR, CHAR_LEAK_DETECTED),
    DEVICE_CLASS_MOTION: (SERV_MOTION_SENSOR, CHAR_MOTION_DETECTED),
    DEVICE_CLASS_OCCUPANCY: (SERV_OCCUPANCY_SENSOR, CHAR_OCCUPANCY_DETECTED),
    DEVICE_CLASS_OPENING: (SERV_CONTACT_SENSOR, CHAR_CONTACT_SENSOR_STATE),
    DEVICE_CLASS_SMOKE: (SERV_SMOKE_SENSOR, CHAR_SMOKE_DETECTED)}


@TYPES.register('TemperatureSensor')
class TemperatureSensor(HomeAccessory):
    """Generate a TemperatureSensor accessory for a temperature sensor.

    Sensor entity must return temperature in °C, °F.
    """

    category = CATEGORY_SENSOR

    def init_setup(self, config):
        """Initialize a TemperatureSensor accessory object."""
        serv_temp = add_preload_service(self, SERV_TEMPERATURE_SENSOR)
        self.char_temp = serv_temp.get_characteristic(CHAR_CURRENT_TEMPERATURE)
        self.char_temp.override_properties(properties=PROP_CELSIUS)
        self.char_temp.value = 0
        self.unit = None

    def update_state(self, new_state):
        """Update temperature after state changed."""
        unit = new_state.attributes.get(ATTR_UNIT_OF_MEASUREMENT, TEMP_CELSIUS)
        temperature = convert_to_float(new_state.state)
        if temperature:
            temperature = temperature_to_homekit(temperature, unit)
            self.char_temp.set_value(temperature)
            _LOGGER.debug('%s: Current temperature set to %d°C',
                          self.entity_id, temperature)


@TYPES.register('HumiditySensor')
class HumiditySensor(HomeAccessory):
    """Generate a HumiditySensor accessory as humidity sensor."""

    category = CATEGORY_SENSOR

    def init_setup(self, config):
        """Initialize a HumiditySensor accessory object."""
        serv_humidity = add_preload_service(self, SERV_HUMIDITY_SENSOR)
        self.char_humidity = serv_humidity \
            .get_characteristic(CHAR_CURRENT_HUMIDITY)
        self.char_humidity.value = 0

    def update_state(self, new_state):
        """Update accessory after state change."""
        humidity = convert_to_float(new_state.state)
        if humidity:
            self.char_humidity.set_value(humidity)
            _LOGGER.debug('%s: Percent set to %d%%',
                          self.entity_id, humidity)


@TYPES.register('BinarySensor')
class BinarySensor(HomeAccessory):
    """Generate a BinarySensor accessory as binary sensor."""

    category = CATEGORY_SENSOR

    def init_setup(self, config):
        """Initialize a BinarySensor accessory object."""
        device_class = self.hass.states.get(self.entity_id).attributes \
            .get(ATTR_DEVICE_CLASS)
        service_char = BINARY_SENSOR_SERVICE_MAP[device_class] \
            if device_class in BINARY_SENSOR_SERVICE_MAP \
            else BINARY_SENSOR_SERVICE_MAP[DEVICE_CLASS_OCCUPANCY]

        service = add_preload_service(self, service_char[0])
        self.char_detected = service.get_characteristic(service_char[1])
        self.char_detected.value = 0

    def update_state(self, new_state):
        """Update accessory after state change."""
        state = new_state.state
        detected = (state == STATE_ON) or (state == STATE_HOME)
        self.char_detected.set_value(detected)
        _LOGGER.debug('%s: Set to %d', self.entity_id, detected)
