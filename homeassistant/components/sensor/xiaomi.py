"""Support for Xiaomi sensors."""
import logging

from homeassistant.components.xiaomi import (PY_XIAOMI_GATEWAY, XiaomiDevice)
from homeassistant.const import TEMP_CELSIUS

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Perform the setup for Xiaomi devices."""
    devices = []
    for (_, gateway) in hass.data[PY_XIAOMI_GATEWAY].gateways.items():
        for device in gateway.devices['sensor']:
            if device['model'] == 'sensor_ht':
                devices.append(XiaomiSensor(device, 'Temperature',
                                            'temperature', gateway))
                devices.append(XiaomiSensor(device, 'Humidity',
                                            'humidity', gateway))
            if device['model'] == 'weather.v1':
                devices.append(XiaomiSensor(device, 'Temperature',
                                            'temperature', gateway))
                devices.append(XiaomiSensor(device, 'Humidity',
                                            'humidity', gateway))
                devices.append(XiaomiSensor(device, 'Pressure',
                                            'pressure', gateway))
            elif device['model'] == 'gateway':
                devices.append(XiaomiSensor(device, 'Illumination',
                                            'illumination', gateway))
    add_devices(devices)


class XiaomiSensor(XiaomiDevice):
    """Representation of a XiaomiSensor."""

    def __init__(self, device, name, data_key, xiaomi_hub):
        """Initialize the XiaomiSensor."""
        self._data_key = data_key
        self._battery = None
        XiaomiDevice.__init__(self, device, name, xiaomi_hub)

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        if self._data_key == 'temperature':
            return TEMP_CELSIUS
        elif self._data_key == 'humidity':
            return '%'
        elif self._data_key == 'illumination':
            return 'lm'
        elif self._data_key == 'pressure':
            return 'hPa'

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    def parse_data(self, data):
        """Parse data sent by gateway."""
        value = data.get(self._data_key)
        if value is None:
            return False
        value = int(value)
        if self._data_key == 'temperature' and value == 10000:
            return False
        elif self._data_key == 'humidity' and value == 0:
            return False
        elif self._data_key == 'illumination' and value == 0:
            return False
        elif self._data_key == 'pressure' and value == 0:
            return False
        if self._data_key in ['temperature', 'humidity']:
            value /= 100
        elif self._data_key in ['illumination']:
                value -= 300
                value = max(value, 0)
        self._state = round(value, 2)
        return True
