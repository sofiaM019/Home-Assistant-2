"""
Manufacturer specific channels module for Zigbee Home Automation.

For more details about this component, please refer to the documentation at
https://home-assistant.io/integrations/zha/
"""
import logging

from homeassistant.core import callback

from .. import registries
from ..const import (
    ATTR_ATTRIBUTE_ID,
    ATTR_ATTRIBUTE_NAME,
    ATTR_VALUE,
    REPORT_CONFIG_ASAP,
    REPORT_CONFIG_MAX_INT,
    REPORT_CONFIG_MIN_INT,
    SIGNAL_ATTR_UPDATED,
    UNKNOWN,
)
from .base import AttributeListeningChannel, ZigbeeChannel

_LOGGER = logging.getLogger(__name__)


@registries.ZIGBEE_CHANNEL_REGISTRY.register(registries.SMARTTHINGS_HUMIDITY_CLUSTER)
class SmartThingsHumidity(AttributeListeningChannel):
    """Smart Things Humidity channel."""

    REPORT_CONFIG = [
        {
            "attr": "measured_value",
            "config": (REPORT_CONFIG_MIN_INT, REPORT_CONFIG_MAX_INT, 50),
        }
    ]


@registries.CHANNEL_ONLY_CLUSTERS.register(0xFD00)
@registries.ZIGBEE_CHANNEL_REGISTRY.register(0xFD00)
class OsramButton(ZigbeeChannel):
    """Osram button channel."""

    REPORT_CONFIG = []


@registries.ZIGBEE_CHANNEL_REGISTRY.register(
    registries.SMARTTHINGS_ACCELERATION_CLUSTER
)
class SmartThingsAcceleration(AttributeListeningChannel):
    """Smart Things Acceleration channel."""

    REPORT_CONFIG = [
        {"attr": "acceleration", "config": REPORT_CONFIG_ASAP},
        {"attr": "x_axis", "config": REPORT_CONFIG_ASAP},
        {"attr": "y_axis", "config": REPORT_CONFIG_ASAP},
        {"attr": "z_axis", "config": REPORT_CONFIG_ASAP},
    ]

    @callback
    def attribute_updated(self, attrid, value):
        """Handle attribute updates on this cluster."""
        if attrid == self.value_attribute:
            self.async_send_signal(f"{self.unique_id}_{SIGNAL_ATTR_UPDATED}", value)
            return

        self.zha_send_event(
            SIGNAL_ATTR_UPDATED,
            {
                ATTR_ATTRIBUTE_ID: attrid,
                ATTR_ATTRIBUTE_NAME: self._cluster.attributes.get(attrid, [UNKNOWN])[0],
                ATTR_VALUE: value,
            },
        )
