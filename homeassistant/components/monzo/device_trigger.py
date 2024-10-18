"""Provides transaction creation triggers for Monzo."""

from __future__ import annotations

import voluptuous as vol

from homeassistant.components.device_automation import DEVICE_TRIGGER_BASE_SCHEMA
from homeassistant.components.device_automation.exceptions import (
    InvalidDeviceAutomationConfig,
)
from homeassistant.const import (
    CONF_DEVICE,
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_PLATFORM,
    CONF_TYPE,
)
from homeassistant.core import CALLBACK_TYPE, HomeAssistant
from homeassistant.helpers import config_validation as cv, device_registry as dr
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.trigger import TriggerActionType, TriggerInfo
from homeassistant.helpers.typing import ConfigType

from . import monzo_event_signal
from .const import DOMAIN, EVENT_TRANSACTION_CREATED, MODEL_POT

TRIGGER_TYPES = [
    EVENT_TRANSACTION_CREATED,
]
ACCOUNT_ID = "account_id"

TRIGGER_SCHEMA = DEVICE_TRIGGER_BASE_SCHEMA.extend(
    {
        vol.Required(ACCOUNT_ID): cv.string,
        vol.Required(CONF_TYPE): vol.In(TRIGGER_TYPES),
    }
)


async def async_validate_trigger_config(
    hass: HomeAssistant, config: ConfigType
) -> ConfigType:
    """Validate config."""
    config = TRIGGER_SCHEMA(config)

    device_registry = dr.async_get(hass)
    device = device_registry.async_get(config[CONF_DEVICE_ID])

    if not device or device.model is None:
        raise InvalidDeviceAutomationConfig(
            f"Trigger invalid, device with ID {config[CONF_DEVICE_ID]} not found"
        )

    if device.model is MODEL_POT:
        raise InvalidDeviceAutomationConfig(
            f"Trigger invalid, device with ID {config[CONF_DEVICE_ID]} is a pot"
        )

    return config


async def async_get_triggers(
    hass: HomeAssistant, device_id: str
) -> list[dict[str, str]]:
    """List device triggers for Monzo devices."""
    device_registry = dr.async_get(hass)
    device = device_registry.async_get(device_id)
    triggers = []

    if device is not None:
        triggers = [
            {
                CONF_PLATFORM: CONF_DEVICE,
                ACCOUNT_ID: next(iter(device.identifiers))[1],
                CONF_DOMAIN: DOMAIN,
                CONF_DEVICE_ID: device_id,
                CONF_TYPE: trigger,
            }
            for trigger in TRIGGER_TYPES
        ]

    return triggers


async def async_attach_trigger(
    hass: HomeAssistant,
    config: ConfigType,
    action: TriggerActionType,
    trigger_info: TriggerInfo,
) -> CALLBACK_TYPE:
    """Attach a trigger."""
    return async_dispatcher_connect(
        hass,
        monzo_event_signal(config[CONF_TYPE], config[ACCOUNT_ID]),
        action,
    )
