"""
homeassistant.components.sensor.arduino
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Support for getting information from Arduino pins. Only analog pins are
supported.

Configuration:

To use the arduino sensor you will need to add something like the following
to your configuration.yaml file.

sensor:
  platform: arduino
  pins:
    7:
      name: Door switch
      type: analog
    0:
      name: Brightness
      type: analog

Variables:

pins
*Required
An array specifying the digital pins to use on the Arduino board.

These are the variables for the pins array:

name
*Required
The name for the pin that will be used in the frontend.

type
*Required
The type of the pin: 'analog'.
"""
import logging

import homeassistant.components.arduino as arduino
from homeassistant.helpers.entity import Entity
from homeassistant.helpers import set_log_severity
from homeassistant.const import DEVICE_DEFAULT_NAME

DEPENDENCIES = ['arduino']

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_devices, discovery_info=None):
    """ Sets up the Arduino platform. """

    set_log_severity(hass, config, _LOGGER)

    # Verify that the Arduino board is present
    if arduino.BOARD is None:
        _LOGGER.error('A connection has not been made to the Arduino board.')
        return False

    sensors = []
    pins = config.get('pins')
    for pinnum, pin in pins.items():
        if pin.get('name'):
            sensors.append(ArduinoSensor(pin.get('name'),
                                         pinnum,
                                         'analog'))
    add_devices(sensors)


class ArduinoSensor(Entity):
    """ Represents an Arduino Sensor. """
    def __init__(self, name, pin, pin_type):
        self._pin = pin
        self._name = name or DEVICE_DEFAULT_NAME
        self.pin_type = pin_type
        self.direction = 'in'
        self._value = None

        arduino.BOARD.set_mode(self._pin, self.direction, self.pin_type)

    @property
    def state(self):
        """ Returns the state of the sensor. """
        return self._value

    @property
    def name(self):
        """ Get the name of the sensor. """
        return self._name

    def update(self):
        """ Get the latest value from the pin. """
        self._value = arduino.BOARD.get_analog_inputs()[self._pin][1]
