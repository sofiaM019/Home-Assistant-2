"""Provide the device automations for Humidifier."""
from typing import Dict, List
import voluptuous as vol

from homeassistant.const import (
    ATTR_ENTITY_ID,
    CONF_CONDITION,
    CONF_DOMAIN,
    CONF_TYPE,
    CONF_DEVICE_ID,
    CONF_ENTITY_ID,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import condition, config_validation as cv, entity_registry
from homeassistant.helpers.typing import ConfigType, TemplateVarsType
from homeassistant.helpers.config_validation import DEVICE_CONDITION_BASE_SCHEMA
from . import DOMAIN, const

CONDITION_TYPES = {"is_operation_mode", "is_preset_mode"}

OPERATION_MODE_CONDITION = DEVICE_CONDITION_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_ENTITY_ID): cv.entity_id,
        vol.Required(CONF_TYPE): "is_operation_mode",
        vol.Required(const.ATTR_OPERATION_MODE): vol.In(const.OPERATION_MODES),
    }
)

PRESET_MODE_CONDITION = DEVICE_CONDITION_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_ENTITY_ID): cv.entity_id,
        vol.Required(CONF_TYPE): "is_preset_mode",
        vol.Required(const.ATTR_PRESET_MODE): str,
    }
)

CONDITION_SCHEMA = vol.Any(OPERATION_MODE_CONDITION, PRESET_MODE_CONDITION)


async def async_get_conditions(
    hass: HomeAssistant, device_id: str
) -> List[Dict[str, str]]:
    """List device conditions for Humidifier devices."""
    registry = await entity_registry.async_get_registry(hass)
    conditions = []

    # Get all the integrations entities for this device
    for entry in entity_registry.async_entries_for_device(registry, device_id):
        if entry.domain != DOMAIN:
            continue

        state = hass.states.get(entry.entity_id)

        conditions.append(
            {
                CONF_CONDITION: "device",
                CONF_DEVICE_ID: device_id,
                CONF_DOMAIN: DOMAIN,
                CONF_ENTITY_ID: entry.entity_id,
                CONF_TYPE: "is_operation_mode",
            }
        )

        if state and state.attributes["supported_features"] & const.SUPPORT_PRESET_MODE:
            conditions.append(
                {
                    CONF_CONDITION: "device",
                    CONF_DEVICE_ID: device_id,
                    CONF_DOMAIN: DOMAIN,
                    CONF_ENTITY_ID: entry.entity_id,
                    CONF_TYPE: "is_preset_mode",
                }
            )

    return conditions


def async_condition_from_config(
    config: ConfigType, config_validation: bool
) -> condition.ConditionCheckerType:
    """Create a function to test a device condition."""
    if config_validation:
        config = CONDITION_SCHEMA(config)

    if config[CONF_TYPE] == "is_operation_mode":
        attribute = const.ATTR_OPERATION_MODE
    else:
        attribute = const.ATTR_PRESET_MODE

    def test_is_state(hass: HomeAssistant, variables: TemplateVarsType) -> bool:
        """Test if an entity is a certain state."""
        state = hass.states.get(config[ATTR_ENTITY_ID])
        return state and state.attributes.get(attribute) == config[attribute]

    return test_is_state


async def async_get_condition_capabilities(hass, config):
    """List condition capabilities."""
    state = hass.states.get(config[CONF_ENTITY_ID])
    condition_type = config[CONF_TYPE]

    fields = {}

    if condition_type == "is_operation_mode":
        operation_modes = state.attributes[const.ATTR_OPERATION_MODES] if state else []
        fields[vol.Required(const.ATTR_OPERATION_MODE)] = vol.In(operation_modes)

    elif condition_type == "is_preset_mode":
        if state:
            preset_modes = state.attributes.get(const.ATTR_PRESET_MODES, [])
        else:
            preset_modes = []

        fields[vol.Required(const.ATTR_PRESET_MODES)] = vol.In(preset_modes)

    return {"extra_fields": vol.Schema(fields)}
