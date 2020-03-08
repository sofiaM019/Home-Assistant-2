"""Base classes for channels."""

import asyncio
from enum import Enum
from functools import wraps
import logging
from typing import Any, Dict, List, Optional, Union

import zigpy.exceptions

from homeassistant.core import callback

from .. import typing as zha_typing
from ..const import (
    ATTR_ARGS,
    ATTR_ATTRIBUTE_ID,
    ATTR_ATTRIBUTE_NAME,
    ATTR_CLUSTER_ID,
    ATTR_COMMAND,
    ATTR_UNIQUE_ID,
    ATTR_VALUE,
    CHANNEL_EVENT_RELAY,
    CHANNEL_ZDO,
    REPORT_CONFIG_MAX_INT,
    REPORT_CONFIG_MIN_INT,
    REPORT_CONFIG_RPT_CHANGE,
    SIGNAL_ATTR_UPDATED,
)
from ..helpers import LogMixin, safe_read

_LOGGER = logging.getLogger(__name__)


def parse_and_log_command(channel, tsn, command_id, args):
    """Parse and log a zigbee cluster command."""
    cmd = channel.cluster.server_commands.get(command_id, [command_id])[0]
    channel.debug(
        "received '%s' command with %s args on cluster_id '%s' tsn '%s'",
        cmd,
        args,
        channel.cluster.cluster_id,
        tsn,
    )
    return cmd


def decorate_command(channel, command):
    """Wrap a cluster command to make it safe."""

    @wraps(command)
    async def wrapper(*args, **kwds):
        try:
            result = await command(*args, **kwds)
            channel.debug(
                "executed '%s' command with args: '%s' kwargs: '%s' result: %s",
                command.__name__,
                args,
                kwds,
                result,
            )
            return result

        except (zigpy.exceptions.DeliveryError, asyncio.TimeoutError) as ex:
            channel.debug("command failed: %s exception: %s", command.__name__, str(ex))
            return ex

    return wrapper


class ChannelStatus(Enum):
    """Status of a channel."""

    CREATED = 1
    CONFIGURED = 2
    INITIALIZED = 3


class ZigbeeChannel(LogMixin):
    """Base channel for a Zigbee cluster."""

    CHANNEL_NAME = None
    REPORT_CONFIG = ()

    def __init__(
        self, cluster: zha_typing.ZigpyClusterType, ch_pool: zha_typing.ChannelPoolType
    ) -> None:
        """Initialize ZigbeeChannel."""
        self._channel_name: Optional[str] = cluster.ep_attribute
        if self.CHANNEL_NAME:
            self._channel_name: Optional[str] = self.CHANNEL_NAME
        self._ch_pool: zha_typing.ChannelPoolType = ch_pool
        self._generic_id: str = f"channel_0x{cluster.cluster_id:04x}"
        self._cluster: zha_typing.ZigpyClusterType = cluster
        self._id: str = f"{ch_pool.id}:0x{cluster.cluster_id:04x}"
        unique_id = ch_pool.unique_id.replace("-", ":")
        self._unique_id: str = f"{unique_id}:0x{cluster.cluster_id:04x}"
        self._report_config = self.REPORT_CONFIG
        if not hasattr(self, "_value_attribute") and len(self._report_config) > 0:
            attr = self._report_config[0].get("attr")
            if isinstance(attr, str):
                self.value_attribute: int = self.cluster.attridx.get(attr)
            else:
                self.value_attribute: int = attr
        self._status: ChannelStatus = ChannelStatus.CREATED
        self._cluster.add_listener(self)

    @property
    def id(self) -> str:
        """Return channel id unique for this device only."""
        return self._id

    @property
    def generic_id(self) -> str:
        """Return the generic id for this channel."""
        return self._generic_id

    @property
    def unique_id(self) -> str:
        """Return the unique id for this channel."""
        return self._unique_id

    @property
    def cluster(self) -> zha_typing.ZigpyClusterType:
        """Return the zigpy cluster for this channel."""
        return self._cluster

    @property
    def name(self) -> Optional[str]:
        """Return friendly name."""
        return self._channel_name

    @property
    def status(self) -> ChannelStatus:
        """Return the status of the channel."""
        return self._status

    @callback
    def async_send_signal(self, signal: str, *args: Any) -> None:
        """Send a signal through hass dispatcher."""
        self._ch_pool.async_send_signal(signal, *args)

    async def bind(self) -> None:
        """Bind a zigbee cluster.

        This also swallows DeliveryError exceptions that are thrown when
        devices are unreachable.
        """
        try:
            res = await self.cluster.bind()
            self.debug("bound '%s' cluster: %s", self.cluster.ep_attribute, res[0])
        except (zigpy.exceptions.DeliveryError, asyncio.TimeoutError) as ex:
            self.debug(
                "Failed to bind '%s' cluster: %s", self.cluster.ep_attribute, str(ex)
            )

    async def configure_reporting(
        self,
        attr: Union[int, str],
        report_config=(
            REPORT_CONFIG_MIN_INT,
            REPORT_CONFIG_MAX_INT,
            REPORT_CONFIG_RPT_CHANGE,
        ),
    ) -> None:
        """Configure attribute reporting for a cluster.

        This also swallows DeliveryError exceptions that are thrown when
        devices are unreachable.
        """
        attr_name = self.cluster.attributes.get(attr, [attr])[0]

        kwargs = {}
        if self.cluster.cluster_id >= 0xFC00 and self._ch_pool.manufacturer_code:
            kwargs["manufacturer"] = self._ch_pool.manufacturer_code

        min_report_int, max_report_int, reportable_change = report_config
        try:
            res = await self.cluster.configure_reporting(
                attr, min_report_int, max_report_int, reportable_change, **kwargs
            )
            self.debug(
                "reporting '%s' attr on '%s' cluster: %d/%d/%d: Result: '%s'",
                attr_name,
                self.cluster.ep_attribute,
                min_report_int,
                max_report_int,
                reportable_change,
                res,
            )
        except (zigpy.exceptions.DeliveryError, asyncio.TimeoutError) as ex:
            self.debug(
                "failed to set reporting for '%s' attr on '%s' cluster: %s",
                attr_name,
                self.cluster.ep_attribute,
                str(ex),
            )

    async def async_configure(self) -> None:
        """Set cluster binding and attribute reporting."""
        if not self._ch_pool.skip_configuration:
            await self.bind()
            if self.cluster.is_server:
                for report_config in self._report_config:
                    await self.configure_reporting(
                        report_config["attr"], report_config["config"]
                    )
            self.debug("finished channel configuration")
        else:
            self.debug("skipping channel configuration")
        self._status = ChannelStatus.CONFIGURED

    async def async_initialize(self, from_cache: bool) -> None:
        """Initialize channel."""
        self.debug("initializing channel: from_cache: %s", from_cache)
        attributes = []
        for report_config in self._report_config:
            attributes.append(report_config["attr"])
        if len(attributes) > 0:
            await self.get_attributes(attributes, from_cache=from_cache)
        self._status = ChannelStatus.INITIALIZED

    @callback
    def cluster_command(self, tsn: int, command_id: int, args) -> None:
        """Handle commands received to this cluster."""
        pass

    @callback
    def attribute_updated(self, attrid: int, value: Any) -> None:
        """Handle attribute updates on this cluster."""
        self.async_send_signal(
            f"{self.unique_id}_{SIGNAL_ATTR_UPDATED}",
            attrid,
            self.cluster.attributes.get(attrid, [attrid])[0],
            value,
        )

    @callback
    def zdo_command(self, *args, **kwargs) -> None:
        """Handle ZDO commands on this cluster."""
        pass

    @callback
    def zha_send_event(self, command: str, args: Union[int, dict]) -> None:
        """Relay events to hass."""
        self._ch_pool.zha_send_event(
            {
                ATTR_UNIQUE_ID: self.unique_id,
                ATTR_CLUSTER_ID: self.cluster.cluster_id,
                ATTR_COMMAND: command,
                ATTR_ARGS: args,
            }
        )

    async def async_update(self) -> None:
        """Retrieve latest state from cluster."""
        pass

    async def get_attribute_value(
        self, attribute: Union[str, int], from_cache: bool = True
    ):
        """Get the value for an attribute."""
        manufacturer = None
        manufacturer_code = self._ch_pool.manufacturer_code
        if self.cluster.cluster_id >= 0xFC00 and manufacturer_code:
            manufacturer = manufacturer_code
        result = await safe_read(
            self._cluster,
            [attribute],
            allow_cache=from_cache,
            only_cache=from_cache,
            manufacturer=manufacturer,
        )
        return result.get(attribute)

    async def get_attributes(
        self, attributes: List[str], from_cache: bool = True
    ) -> Dict[str, Any]:
        """Get the values for a list of attributes."""
        manufacturer = None
        manufacturer_code = self._ch_pool.manufacturer_code
        if self.cluster.cluster_id >= 0xFC00 and manufacturer_code:
            manufacturer = manufacturer_code
        try:
            result, _ = await self.cluster.read_attributes(
                attributes,
                allow_cache=from_cache,
                only_cache=from_cache,
                manufacturer=manufacturer,
            )
            results = {attribute: result.get(attribute) for attribute in attributes}
        except (asyncio.TimeoutError, zigpy.exceptions.DeliveryError) as ex:
            self.debug(
                "failed to get attributes '%s' on '%s' cluster: %s",
                attributes,
                self.cluster.ep_attribute,
                str(ex),
            )
            results = {}
        return results

    def log(self, level, msg, *args) -> None:
        """Log a message."""
        msg = f"[%s:%s]: {msg}"
        args = (self._ch_pool.nwk, self._id) + args
        _LOGGER.log(level, msg, *args)

    def __getattr__(self, name):
        """Get attribute or a decorated cluster command."""
        if hasattr(self._cluster, name) and callable(getattr(self._cluster, name)):
            command = getattr(self._cluster, name)
            command.__name__ = name
            return decorate_command(self, command)
        return self.__getattribute__(name)


class ZDOChannel(LogMixin):
    """Channel for ZDO events."""

    def __init__(
        self, cluster: zha_typing.ZigpyClusterType, device: zha_typing.ZhaDeviceType
    ):
        """Initialize ZDOChannel."""
        self.name: str = CHANNEL_ZDO
        self._cluster: zha_typing.ZigpyClusterType = cluster
        self._zha_device: zha_typing.ZhaDeviceType = device
        self._status: ChannelStatus = ChannelStatus.CREATED
        self._unique_id: str = "{}:{}_ZDO".format(str(device.ieee), device.name)
        self._cluster.add_listener(self)

    @property
    def unique_id(self) -> str:
        """Return the unique id for this channel."""
        return self._unique_id

    @property
    def cluster(self) -> zha_typing.ZigpyClusterType:
        """Return the aigpy cluster for this channel."""
        return self._cluster

    @property
    def status(self) -> ChannelStatus:
        """Return the status of the channel."""
        return self._status

    @callback
    def device_announce(self, zigpy_device: zha_typing.ZigpyDeviceType) -> None:
        """Device announce handler."""
        pass

    @callback
    def permit_duration(self, duration: int) -> None:
        """Permit handler."""
        pass

    async def async_initialize(self, from_cache: bool) -> None:
        """Initialize channel."""
        self._status = ChannelStatus.INITIALIZED

    async def async_configure(self) -> None:
        """Configure channel."""
        self._status = ChannelStatus.CONFIGURED

    def log(self, level, msg, *args):
        """Log a message."""
        msg = f"[%s:ZDO](%s): {msg}"
        args = (self._zha_device.nwk, self._zha_device.model) + args
        _LOGGER.log(level, msg, *args)


class EventRelayChannel(ZigbeeChannel):
    """Event relay that can be attached to zigbee clusters."""

    CHANNEL_NAME = CHANNEL_EVENT_RELAY

    @callback
    def attribute_updated(self, attrid: int, value: Any) -> None:
        """Handle an attribute updated on this cluster."""
        self.zha_send_event(
            SIGNAL_ATTR_UPDATED,
            {
                ATTR_ATTRIBUTE_ID: attrid,
                ATTR_ATTRIBUTE_NAME: self._cluster.attributes.get(attrid, ["Unknown"])[
                    0
                ],
                ATTR_VALUE: value,
            },
        )

    @callback
    def cluster_command(self, tsn: int, command_id: int, args) -> None:
        """Handle a cluster command received on this cluster."""
        if (
            self._cluster.server_commands is not None
            and self._cluster.server_commands.get(command_id) is not None
        ):
            self.zha_send_event(self._cluster.server_commands.get(command_id)[0], args)
