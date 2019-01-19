"""
Support for the for Danfoss Air HRV binary sensor platform.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/binary_sensor.danfoss_air/
"""
from homeassistant.components.binary_sensor import BinarySensorDevice
from homeassistant.components.danfoss_air import DOMAIN


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the available Danfoss Air sensors etc."""
    from pydanfossair.commands import ReadCommand
    data = hass.data[DOMAIN]

    sensors = [["Danfoss Air Bypass Active", ReadCommand.bypass]]

    dev = []

    for sensor in sensors:
        dev.append(DanfossAirBinarySensor(data, sensor[0], sensor[1]))

    add_devices(dev, True)


class DanfossAirBinarySensor(BinarySensorDevice):
    """Representation of a Danfoss Air binary sensor."""

    def __init__(self, data, name, sensor_type):
        """Initialize the Danfoss Air binary sensor."""
        self._data = data
        self._name = name
        self._state = None
        self._type = sensor_type

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def is_on(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def device_class(self):
        """Type of device class."""
        return "opening"

    def update(self):
        """Fetch new state data for the sensor."""
        self._data.update()

        self._state = self._data.get_value(self._type)
