"""
Support for BT Home Hub 5.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/device_tracker.bt_home_hub_5/
"""

import logging
import re
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.device_tracker import (DOMAIN, PLATFORM_SCHEMA,
                                                     DeviceScanner)
from homeassistant.const import CONF_HOST

REQUIREMENTS = ['bthomehub5-devicelist==0.1.1']

_LOGGER = logging.getLogger(__name__)
_MAC_REGEX = re.compile(r'(([0-9A-Fa-f]{1,2}:){5}[0-9A-Fa-f]{1,2})')

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string
})


def get_scanner(hass, config):
    """Return a BT Home Hub 5 scanner if successful."""
    scanner = BTHomeHub5DeviceScanner(config[DOMAIN])

    return scanner if scanner.success_init else None


class BTHomeHub5DeviceScanner(DeviceScanner):
    """This class queries a BT Home Hub 5."""

    def __init__(self, config):
        import bthomehub5_devicelist

        """Initialise the scanner."""
        _LOGGER.info("Initialising BT Home Hub 5")
        self.host = config.get(CONF_HOST, '192.168.1.254')
        self.last_results = {}

        # Test the router is accessible
        data = bthomehub5_devicelist.get_devicelist(self.host)
        self.success_init = data is not None

    def scan_devices(self):
        """Scan for new devices and return a list with found device IDs."""
        self.update_info()

        return (device for device in self.last_results)

    def get_device_name(self, device):
        """Return the name of the given device or None if we don't know."""
        # If not initialised and not already scanned and not found.
        if device not in self.last_results:
            self.update_info()

            if not self.last_results:
                return None

        return self.last_results.get(device)

    def update_info(self):
        """Ensure the information from the BT Home Hub 5 is up to date.
        Return boolean if scanning successful.
        """

        import bthomehub5_devicelist

        if not self.success_init:
            return False

        _LOGGER.info("Scanning")

        data = bthomehub5_devicelist.get_devicelist(self.host)

        if not data:
            _LOGGER.warning("Error scanning devices")
            return False

        self.last_results = data

        return True
