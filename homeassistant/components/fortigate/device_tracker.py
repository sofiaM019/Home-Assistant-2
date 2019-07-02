"""Device tracker for Fortigate Firewalls."""
from collections import namedtuple
import logging

import voluptuous as vol

from homeassistant.const import CONF_HOST, CONF_USERNAME, \
    CONF_PASSWORD, CONF_DEVICES
from homeassistant.components.device_tracker import DeviceScanner
from homeassistant.helpers import config_validation as cv
from homeassistant.components.device_tracker import PLATFORM_SCHEMA


from . import DATA_FGT

_LOGGER = logging.getLogger(__name__)

DETECTED_DEVICES = "/monitor/user/detected-device"


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Optional(CONF_DEVICES, default=[]):
        vol.All(cv.ensure_list, [cv.string]),
})


async def async_get_scanner(hass, config):
    """Validate the configuration and return a Freebox scanner."""
    scanner = FortigateDeviceScanner(hass.data[DATA_FGT])
    await scanner.async_connect()
    return scanner if scanner.success_init else None


Device = namedtuple('Device', ['hostname', 'mac'])


def _build_device(device_dict):
    return Device(
        device_dict['hostname'],
        device_dict['mac'])


class FortigateDeviceScanner(DeviceScanner):
    """Queries the Fortigate firewall."""

    def __init__(self, hass_data):
        """Initialize the scanner."""
        self.last_results = {}
        self.success_init = False
        self.connection = hass_data['fgt']
        self.devices = hass_data['devices']

    def get_results(self):
        """Get the results from the fortigate."""
        results = self.connection.get(
            DETECTED_DEVICES, "vdom=root")[1]['results']

        ret = []
        for result in results:
            try:
                # some device does not have a hostname
                assert 'hostname' in result
                ret.append(result)
            except AssertionError:
                pass

        return ret

    async def async_connect(self):
        """Initialize connection to the router."""
        # Test the firewall is accessible.
        data = self.get_results()
        self.success_init = data is not None

    async def async_scan_devices(self):
        """Scan for new devices and return a list with found device MACs."""
        await self.async_update_info()
        return [device.mac for device in self.last_results]

    async def get_device_name(self, device):
        """Return the name of the given device or None if we don't know."""
        name = next((
            result.hostname for result in self.last_results
            if result.mac == device), None)
        return name

    async def async_update_info(self):
        """Ensure the information from the Fortigate firewall is up to date."""
        _LOGGER.debug('Checking Devices')

        hosts = self.get_results()

        all_results = [_build_device(device) for device in hosts
                       if device['is_online']]

        # if the 'devices' configuration field is filled
        if self.devices is not None:
            last_results = [
                device for device in all_results
                if device.hostname in self.devices
            ]
            _LOGGER.debug(last_results)
        # if the 'devices' configuration field is not filled
        else:
            last_results = all_results

        self.last_results = last_results
