"""Support for ZHA sirens."""

from __future__ import annotations

import functools
from typing import Any

from homeassistant.components.siren import (
    ATTR_DURATION,
    DOMAIN,
    SUPPORT_DURATION,
    SUPPORT_TURN_OFF,
    SUPPORT_TURN_ON,
    SirenEntity,
)
from homeassistant.components.siren.const import (
    ATTR_TONE,
    ATTR_VOLUME_LEVEL,
    SUPPORT_TONES,
    SUPPORT_VOLUME_SET,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_call_later

from .core import discovery
from .core.channels.security import IasWd
from .core.const import (
    CHANNEL_IAS_WD,
    DATA_ZHA,
    DATA_ZHA_DISPATCHERS,
    SIGNAL_ADD_ENTITIES,
    WARNING_DEVICE_MODE_BURGLAR,
    WARNING_DEVICE_MODE_EMERGENCY,
    WARNING_DEVICE_MODE_EMERGENCY_PANIC,
    WARNING_DEVICE_MODE_FIRE,
    WARNING_DEVICE_MODE_FIRE_PANIC,
    WARNING_DEVICE_MODE_POLICE_PANIC,
    WARNING_DEVICE_MODE_STOP,
    WARNING_DEVICE_SOUND_HIGH,
    WARNING_DEVICE_STROBE_NO,
)
from .core.registries import ZHA_ENTITIES
from .core.typing import ChannelType, ZhaDeviceType
from .entity import ZhaEntity

STRICT_MATCH = functools.partial(ZHA_ENTITIES.strict_match, DOMAIN)
FIVE_SECONDS = 5


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Zigbee Home Automation siren from config entry."""
    entities_to_create = hass.data[DATA_ZHA][DOMAIN]

    unsub = async_dispatcher_connect(
        hass,
        SIGNAL_ADD_ENTITIES,
        functools.partial(
            discovery.async_add_entities,
            async_add_entities,
            entities_to_create,
            update_before_add=False,
        ),
    )
    hass.data[DATA_ZHA][DATA_ZHA_DISPATCHERS].append(unsub)


@STRICT_MATCH(channel_names=CHANNEL_IAS_WD)
class ZHASiren(ZhaEntity, SirenEntity):
    """Representation of a ZHA siren."""

    def __init__(
        self,
        unique_id: str,
        zha_device: ZhaDeviceType,
        channels: list[ChannelType],
        **kwargs,
    ) -> None:
        """Init this sensor."""
        super().__init__(unique_id, zha_device, channels, **kwargs)
        self._channel: IasWd = channels[0]
        self._attr_supported_features = (
            SUPPORT_TURN_ON
            | SUPPORT_TURN_OFF
            | SUPPORT_DURATION
            | SUPPORT_VOLUME_SET
            | SUPPORT_TONES
        )
        self._attr_is_on: bool = False
        self._attr_available_tones: list[int | str] | dict[int, str] | None = {
            WARNING_DEVICE_MODE_BURGLAR: "Burglar",
            WARNING_DEVICE_MODE_FIRE: "Fire",
            WARNING_DEVICE_MODE_EMERGENCY: "Emergency",
            WARNING_DEVICE_MODE_POLICE_PANIC: "Police Panic",
            WARNING_DEVICE_MODE_FIRE_PANIC: "Fire Panic",
            WARNING_DEVICE_MODE_EMERGENCY_PANIC: "Emergency Panic",
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on siren."""
        siren_tone = WARNING_DEVICE_MODE_EMERGENCY
        siren_duration = FIVE_SECONDS
        siren_level = WARNING_DEVICE_SOUND_HIGH
        if (duration := kwargs.get(ATTR_DURATION)) is not None:
            siren_duration = duration
        if (tone := kwargs.get(ATTR_TONE)) is not None:
            siren_tone = tone
        if (level := kwargs.get(ATTR_VOLUME_LEVEL)) is not None:
            siren_level = int(level)
        await self._channel.issue_start_warning(
            mode=siren_tone, warning_duration=siren_duration, siren_level=siren_level
        )
        self._attr_is_on = True
        async_call_later(self._zha_device.hass, siren_duration, self.async_set_off)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off siren."""
        await self._channel.issue_start_warning(
            mode=WARNING_DEVICE_MODE_STOP, strobe=WARNING_DEVICE_STROBE_NO
        )
        self._attr_is_on = False
        self.async_write_ha_state()

    @callback
    def async_set_off(self, _) -> None:
        """Set is_on to False and write HA state."""
        self._attr_is_on = False
        self.async_write_ha_state()
