"""HVAC channels module for Zigbee Home Automation."""
import logging
from typing import Any

from zigpy.exceptions import DeliveryError
import zigpy.zcl.clusters.hvac as hvac

from homeassistant.core import callback

from .. import registries, typing as zha_typing
from ..const import REPORT_CONFIG_OP, SIGNAL_ATTR_UPDATED
from .base import ZigbeeChannel

_LOGGER = logging.getLogger(__name__)


@registries.ZIGBEE_CHANNEL_REGISTRY.register(hvac.Dehumidification.cluster_id)
class Dehumidification(ZigbeeChannel):
    """Dehumidification channel."""

    pass


@registries.ZIGBEE_CHANNEL_REGISTRY.register(hvac.Fan.cluster_id)
class FanChannel(ZigbeeChannel):
    """Fan channel."""

    _value_attribute: int = 0

    REPORT_CONFIG: zha_typing.AttributeReportConfigType = (
        zha_typing.AttributeReportConfig(attr="fan_mode", config=REPORT_CONFIG_OP),
    )

    async def async_set_speed(self, value: int) -> None:
        """Set the speed of the fan."""

        try:
            await self.cluster.write_attributes({"fan_mode": value})
        except DeliveryError as ex:
            self.error("Could not set speed: %s", ex)
            return

    async def async_update(self) -> None:
        """Retrieve latest state."""
        result = await self.get_attribute_value("fan_mode", from_cache=True)
        if result is not None:
            self.async_send_signal(
                f"{self.unique_id}_{SIGNAL_ATTR_UPDATED}", 0, "fan_mode", result
            )

    @callback
    def attribute_updated(self, attrid: int, value: Any) -> None:
        """Handle attribute update from fan cluster."""
        attr_name = self.cluster.attributes.get(attrid, [attrid])[0]
        self.debug(
            "Attribute report '%s'[%s] = %s", self.cluster.name, attr_name, value
        )
        if attrid == self._value_attribute:
            self.async_send_signal(
                f"{self.unique_id}_{SIGNAL_ATTR_UPDATED}", attrid, attr_name, value
            )

    async def async_initialize(self, from_cache: bool) -> None:
        """Initialize channel."""
        await self.get_attribute_value(self._value_attribute, from_cache=from_cache)
        await super().async_initialize(from_cache)


@registries.ZIGBEE_CHANNEL_REGISTRY.register(hvac.Pump.cluster_id)
class Pump(ZigbeeChannel):
    """Pump channel."""

    pass


@registries.ZIGBEE_CHANNEL_REGISTRY.register(hvac.Thermostat.cluster_id)
class Thermostat(ZigbeeChannel):
    """Thermostat channel."""

    pass


@registries.ZIGBEE_CHANNEL_REGISTRY.register(hvac.UserInterface.cluster_id)
class UserInterface(ZigbeeChannel):
    """User interface (thermostat) channel."""

    pass
