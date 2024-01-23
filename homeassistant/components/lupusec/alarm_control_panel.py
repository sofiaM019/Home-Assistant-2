"""Support for Lupusec System alarm control panels."""
from __future__ import annotations

from datetime import timedelta

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
)
from homeassistant.const import (
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_DISARMED,
    STATE_ALARM_TRIGGERED,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from . import DOMAIN as LUPUSEC_DOMAIN, LupusecDevice

SCAN_INTERVAL = timedelta(seconds=2)


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up an alarm control panel for a Lupusec device."""
    if discovery_info is None:
        return

    data = hass.data[LUPUSEC_DOMAIN]

    alarm_devices = [LupusecAlarm(data, data.lupusec.get_alarm())]

    add_entities(alarm_devices)


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Set up an alarm control panel for a Lupusec device."""
    data = hass.data[LUPUSEC_DOMAIN]

    alarm_devices = [LupusecAlarm(data, data.lupusec.get_alarm(), config_entry)]

    async_add_devices(alarm_devices)


def get_unique_id(config_entry_id: str, key: str) -> str:
    """Create a unique_id id for a lupusec entity."""
    return f"{LUPUSEC_DOMAIN}_{config_entry_id}_{key}"


class LupusecAlarm(LupusecDevice, AlarmControlPanelEntity):
    """An alarm_control_panel implementation for Lupusec."""

    _attr_icon = "mdi:security"
    _attr_supported_features = (
        AlarmControlPanelEntityFeature.ARM_HOME
        | AlarmControlPanelEntityFeature.ARM_AWAY
    )

    def __init__(self, data, device, config_entry=None) -> None:
        """Initialize a Lupusec alarm control panel."""
        super().__init__(data, device, config_entry)
        self._attr_unique_id = get_unique_id(config_entry.entry_id, device.device_id)

    @property
    def state(self) -> str | None:
        """Return the state of the device."""
        if self._device.is_standby:
            state = STATE_ALARM_DISARMED
        elif self._device.is_away:
            state = STATE_ALARM_ARMED_AWAY
        elif self._device.is_home:
            state = STATE_ALARM_ARMED_HOME
        elif self._device.is_alarm_triggered:
            state = STATE_ALARM_TRIGGERED
        else:
            state = None
        return state

    def alarm_arm_away(self, code: str | None = None) -> None:
        """Send arm away command."""
        self._device.set_away()

    def alarm_disarm(self, code: str | None = None) -> None:
        """Send disarm command."""
        self._device.set_standby()

    def alarm_arm_home(self, code: str | None = None) -> None:
        """Send arm home command."""
        self._device.set_home()
