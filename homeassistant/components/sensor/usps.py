"""
Sensor for USPS packages.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.usps/
"""
from collections import defaultdict
import logging

from homeassistant.components.usps import DATA_USPS
from homeassistant.const import (ATTR_ATTRIBUTION)
from homeassistant.helpers.entity import Entity
from homeassistant.util import slugify
from homeassistant.util.dt import now, parse_datetime

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ['usps']

STATUS_DELIVERED = 'delivered'


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the USPS platform."""
    if discovery_info is None:
        return

    usps = hass.data[DATA_USPS]
    _LOGGER.debug("Adding USPS Sensor devices...")
    add_devices([USPSPackageSensor(usps),
                 USPSMailSensor(usps)], True)


class USPSPackageSensor(Entity):
    """USPS Package Sensor."""

    def __init__(self, usps):
        """Initialize the sensor."""
        self._usps = usps
        self._name = self._usps.name
        self._attributes = None
        self._state = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return '{} packages'.format(self._name)

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    def update(self):
        """Update device state."""
        status_counts = defaultdict(int)
        for package in self._usps.packages:
            status = slugify(package['primary_status'])
            if status == STATUS_DELIVERED and \
                    parse_datetime(package['date']).date() < now().date():
                continue
            status_counts[status] += 1
        self._attributes = {
            ATTR_ATTRIBUTION: self._usps.attribution
        }
        self._attributes.update(status_counts)
        self._state = sum(status_counts.values())

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self._attributes

    @property
    def icon(self):
        """Icon to use in the frontend."""
        return 'mdi:package-variant-closed'


class USPSMailSensor(Entity):
    """USPS Mail Sensor."""

    def __init__(self, usps):
        """Initialize the sensor."""
        self._usps = usps
        self._name = self._usps.name
        self._attributes = None
        self._state = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return '{} mail'.format(self._name)

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    def update(self):
        """Update device state."""
        if self._usps.mail is not None:
            self._state = len(self._usps.mail)

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return {
            ATTR_ATTRIBUTION: self._usps.attribution
        }

    @property
    def icon(self):
        """Icon to use in the frontend."""
        return 'mdi:mailbox'
