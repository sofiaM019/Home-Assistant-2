"""Support for Xiaomi Mi WiFi Repeater 2."""
import logging

import voluptuous as vol

from homeassistant.components.device_tracker import (
    DOMAIN, PLATFORM_SCHEMA, DeviceScanner)
from homeassistant.const import CONF_HOST, CONF_TOKEN
import homeassistant.helpers.config_validation as cv

REQUIREMENTS = ['python-miio==0.4.5', 'construct==2.9.45']

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_TOKEN): vol.All(cv.string, vol.Length(min=32, max=32)),
})


def get_scanner(hass, config):
    """Return a Xiaomi MiIO device scanner."""
    from miio import WifiRepeater, DeviceException

    scanner = None
    host = config[DOMAIN].get(CONF_HOST)
    token = config[DOMAIN].get(CONF_TOKEN)

    _LOGGER.info(
        "Initializing with host %s (token %s...)", host, token[:5])

    try:
        device = WifiRepeater(host, token)
        device_info = device.info()
        _LOGGER.info("%s %s %s detected",
                     device_info.model,
                     device_info.firmware_version,
                     device_info.hardware_version)
        scanner = XiaomiMiioDeviceScanner(device)
    except DeviceException as ex:
        _LOGGER.error("Device unavailable or token incorrect: %s", ex)

    return scanner


class XiaomiMiioDeviceScanner(DeviceScanner):
    """This class queries a Xiaomi Mi WiFi Repeater."""

    def __init__(self, device):
        """Initialize the scanner."""
        self.device = device

    async def async_scan_devices(self):
        """Scan for devices and return a list containing found device IDs."""
        from miio import DeviceException

        devices = []
        try:
            station_info = \
                await self.hass.async_add_executor_job(self.device.status)
            _LOGGER.debug("Got new station info: %s", station_info)

            for device in station_info.associated_stations:
                devices.append(device['mac'])

        except DeviceException as ex:
            _LOGGER.error("Unable to fetch the state: %s", ex)

        return devices

    async def async_get_device_name(self, device):
        """Return None.

        The repeater doesn't provide the name of the associated device.
        """
        return None
