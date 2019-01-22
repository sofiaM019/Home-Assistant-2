"""Battery Charge and Range Support for the Nissan Leaf.

Please refer to the main platform component for configuration details
"""

import logging
from homeassistant.util.unit_system import IMPERIAL_SYSTEM, METRIC_SYSTEM
from homeassistant.util.distance import LENGTH_KILOMETERS, LENGTH_MILES
from homeassistant.helpers.icon import icon_for_battery_level
from homeassistant.components.nissan_leaf import (
    DATA_BATTERY, DATA_CHARGING, DATA_LEAF, DATA_RANGE_AC, DATA_RANGE_AC_OFF,
    LeafEntity
)

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ['nissan_leaf']


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Sensors setup."""
    _LOGGER.debug("setup_platform nissan_leaf sensors, discovery_info=%s",
                  discovery_info)

    devices = []
    for key, value in hass.data[DATA_LEAF].items():
        _LOGGER.debug("adding sensor for item key=%s, value=%s", key, value)
        devices.append(LeafBatterySensor(value))
        devices.append(LeafRangeSensor(value, True))
        devices.append(LeafRangeSensor(value, False))

    add_devices(devices, True)


class LeafBatterySensor(LeafEntity):
    """Nissan Leaf Battery Sensor."""

    @property
    def name(self):
        """Sensor Name."""
        return self.car.leaf.nickname + " Charge"

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        return 'battery'

    @property
    def state(self):
        """Battery state percentage."""
        return round(self.car.data[DATA_BATTERY], 0)

    @property
    def unit_of_measurement(self):
        """Battery state measured in percentage."""
        return '%'

    @property
    def icon(self):
        """Battery state icon handling."""
        chargestate = self.car.data[DATA_CHARGING]
        return icon_for_battery_level(
            battery_level=self.state,
            charging=chargestate
        )


class LeafRangeSensor(LeafEntity):
    """Nissan Leaf Range Sensor."""

    def __init__(self, car, ac_on):
        """Set-up range sensor. Store if AC on."""
        self.ac_on = ac_on
        super().__init__(car)

    @property
    def name(self):
        """Update sensor name depending on AC."""
        if self.ac_on is True:
            return self.car.leaf.nickname + " Range (AC)"
        return self.car.leaf.nickname + " Range"

    def log_registration(self):
        """Log registration."""
        _LOGGER.debug(
            "Registered LeafRangeSensor component with HASS for VIN %s",
            self.car.leaf.vin)

    @property
    def state(self):
        """Battery range in miles or kms."""
        ret = 0

        if self.ac_on:
            ret = self.car.data[DATA_RANGE_AC]
        else:
            ret = self.car.data[DATA_RANGE_AC_OFF]

        if (not self.car.hass.config.units.is_metric or
                self.car.force_miles):
            ret = IMPERIAL_SYSTEM.length(ret, METRIC_SYSTEM.length_unit)

        return round(ret, 0)

    @property
    def unit_of_measurement(self):
        """Battery range unit."""
        if (not self.car.hass.config.units.is_metric or
                self.car.force_miles):
            return LENGTH_MILES
        return LENGTH_KILOMETERS

    @property
    def icon(self):
        """Nice icon for range."""
        return 'mdi:speedometer'
