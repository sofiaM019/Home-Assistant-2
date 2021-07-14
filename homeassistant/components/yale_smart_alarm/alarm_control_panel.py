"""Support for Yale Alarm."""
from __future__ import annotations

import voluptuous as vol

from homeassistant.components.alarm_control_panel import (
    PLATFORM_SCHEMA as PARENT_PLATFORM_SCHEMA,
    AlarmControlPanelEntity,
)
from homeassistant.components.alarm_control_panel.const import (
    SUPPORT_ALARM_ARM_AWAY,
    SUPPORT_ALARM_ARM_HOME,
)
from homeassistant.config_entries import SOURCE_IMPORT
from homeassistant.const import (
    ATTR_IDENTIFIERS,
    ATTR_MANUFACTURER,
    ATTR_MODEL,
    ATTR_NAME,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_USERNAME,
    STATE_UNAVAILABLE,
)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_AREA_ID,
    DEFAULT_AREA_ID,
    DEFAULT_NAME,
    DOMAIN,
    LOGGER,
    MANUFACTURER,
    MODEL,
    STATE_MAP,
)

PLATFORM_SCHEMA = PARENT_PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_AREA_ID, default=DEFAULT_AREA_ID): cv.string,
    }
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Import Yale configuration from YAML."""
    LOGGER.warning(
        "Loading Yale Alarm via platform setup is depreciated; Please remove it from your configuration"
    )
    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_IMPORT},
            data=config,
        )
    )


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the alarm entry."""

    async_add_entities(
        [YaleAlarmDevice(coordinator=hass.data[DOMAIN][entry.entry_id]["coordinator"])]
    )


class YaleAlarmDevice(CoordinatorEntity, AlarmControlPanelEntity):
    """Represent a Yale Smart Alarm."""

    @property
    def name(self):
        """Return the name of the device."""
        return self.coordinator.entry.data[CONF_NAME]

    @property
    def unique_id(self) -> str:
        """Return the unique ID for this entity."""
        self.entry_id = self.coordinator.entry.entry_id
        return str(self.entry_id)

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this entity."""
        self.identifier = self.coordinator.entry.data[CONF_USERNAME]
        return {
            ATTR_NAME: self.name,
            ATTR_MANUFACTURER: MANUFACTURER,
            ATTR_MODEL: MODEL,
            ATTR_IDENTIFIERS: {(DOMAIN, self.identifier)},
        }

    @property
    def state(self):
        """Return the state of the device."""
        return STATE_MAP.get(self.coordinator.data["alarm"], STATE_UNAVAILABLE)

    @property
    def available(self):
        """Return if entity is available."""
        return (
            STATE_MAP.get(self.coordinator.data["alarm"], STATE_UNAVAILABLE)
            != STATE_UNAVAILABLE
        )

    @property
    def code_arm_required(self):
        """Whether the code is required for arm actions."""
        return False

    @property
    def supported_features(self) -> int:
        """Return the list of supported features."""
        return SUPPORT_ALARM_ARM_HOME | SUPPORT_ALARM_ARM_AWAY

    def alarm_disarm(self, code=None):
        """Send disarm command."""
        self.coordinator.yale.disarm()

    def alarm_arm_home(self, code=None):
        """Send arm home command."""
        self.coordinator.yale.arm_partial()

    def alarm_arm_away(self, code=None):
        """Send arm away command."""
        self.coordinator.yale.arm_full()
