"""Tests for the Freedompro climate."""

from datetime import timedelta
from unittest.mock import ANY, patch

from homeassistant.components.climate import (
    ATTR_CURRENT_TEMPERATURE,
    ATTR_HVAC_MODE,
    ATTR_HVAC_MODES,
    ATTR_MAX_TEMP,
    ATTR_MIN_TEMP,
    ATTR_TEMPERATURE,
    DOMAIN as CLIMATE_DOMAIN,
    HVAC_MODE_COOL,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    SERVICE_SET_HVAC_MODE,
    SERVICE_SET_TEMPERATURE,
)
from homeassistant.components.climate.const import HVAC_MODE_AUTO
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.util.dt import utcnow

from tests.common import async_fire_time_changed
from tests.components.freedompro.const import DEVICES_STATE

uid = "3WRRJR6RCZQZSND8VP0YTO3YXCSOFPKBMW8T51TU-LQ*TWMYQKL3UVED4HSIIB9GXJWJZBQCXG-9VE-N2IUAIWI"


async def test_climate_get_state(hass, init_integration):
    """Test states of the climate."""
    init_integration
    registry = er.async_get(hass)
    registry_device = dr.async_get(hass)

    device = registry_device.async_get_device({("freedompro", uid)})
    assert device is not None
    assert device.identifiers == {("freedompro", uid)}
    assert device.manufacturer == "Freedompro"
    assert device.name == "thermostat"
    assert device.model == "thermostat"

    entity_id = "climate.thermostat"
    state = hass.states.get(entity_id)
    assert state
    assert state.attributes.get("friendly_name") == "thermostat"

    assert state.attributes[ATTR_HVAC_MODES] == [
        HVAC_MODE_OFF,
        HVAC_MODE_HEAT,
        HVAC_MODE_COOL,
    ]

    assert state.attributes[ATTR_MIN_TEMP] == 7
    assert state.attributes[ATTR_MAX_TEMP] == 35
    assert state.attributes[ATTR_TEMPERATURE] == 14
    assert state.attributes[ATTR_CURRENT_TEMPERATURE] == 14

    assert state.state == HVAC_MODE_HEAT

    entry = registry.async_get(entity_id)
    assert entry
    assert entry.unique_id == uid

    get_states_response = list(DEVICES_STATE)
    for state_response in get_states_response:
        if state_response["uid"] == uid:
            state_response["state"]["currentTemperature"] = 20
            state_response["state"]["targetTemperature"] = 21
    with patch(
        "homeassistant.components.freedompro.get_states",
        return_value=get_states_response,
    ):
        async_fire_time_changed(hass, utcnow() + timedelta(hours=2))
        await hass.async_block_till_done()

        state = hass.states.get(entity_id)
        assert state
        assert state.attributes.get("friendly_name") == "thermostat"

        entry = registry.async_get(entity_id)
        assert entry
        assert entry.unique_id == uid

        assert state.attributes[ATTR_TEMPERATURE] == 21
        assert state.attributes[ATTR_CURRENT_TEMPERATURE] == 20


async def test_climate_set_off(hass, init_integration):
    """Test set off climate."""
    init_integration
    registry = er.async_get(hass)

    entity_id = "climate.thermostat"
    state = hass.states.get(entity_id)
    assert state
    assert state.attributes.get("friendly_name") == "thermostat"

    entry = registry.async_get(entity_id)
    assert entry
    assert entry.unique_id == uid

    with patch(
        "homeassistant.components.freedompro.climate.put_state"
    ) as mock_put_state:
        assert await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {ATTR_ENTITY_ID: [entity_id], ATTR_HVAC_MODE: HVAC_MODE_OFF},
            blocking=True,
        )
    mock_put_state.assert_called_once_with(ANY, ANY, ANY, '{"heatingCoolingState": 0}')

    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.state == HVAC_MODE_HEAT


async def test_climate_set_unsupported_hvac_mode(hass, init_integration):
    """Test set unsupported hvac mode climate."""
    init_integration
    registry = er.async_get(hass)

    entity_id = "climate.thermostat"
    state = hass.states.get(entity_id)
    assert state
    assert state.attributes.get("friendly_name") == "thermostat"

    entry = registry.async_get(entity_id)
    assert entry
    assert entry.unique_id == uid

    assert await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: [entity_id], ATTR_HVAC_MODE: HVAC_MODE_AUTO},
        blocking=True,
    )


async def test_climate_set_temperature(hass, init_integration):
    """Test set temperature climate."""
    init_integration
    registry = er.async_get(hass)

    entity_id = "climate.thermostat"
    state = hass.states.get(entity_id)
    assert state
    assert state.attributes.get("friendly_name") == "thermostat"

    entry = registry.async_get(entity_id)
    assert entry
    assert entry.unique_id == uid

    with patch(
        "homeassistant.components.freedompro.climate.put_state"
    ) as mock_put_state:
        assert await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_TEMPERATURE,
            {
                ATTR_ENTITY_ID: [entity_id],
                ATTR_HVAC_MODE: HVAC_MODE_OFF,
                ATTR_TEMPERATURE: 25,
            },
            blocking=True,
        )
    mock_put_state.assert_called_once_with(
        ANY, ANY, ANY, '{"heatingCoolingState": 0, "targetTemperature": 25.0}'
    )

    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.attributes[ATTR_TEMPERATURE] == 21


async def test_climate_set_temperature_unsupported_hvac_mode(hass, init_integration):
    """Test set temperature climate unsupported hvac mode."""
    init_integration
    registry = er.async_get(hass)

    entity_id = "climate.thermostat"
    state = hass.states.get(entity_id)
    assert state
    assert state.attributes.get("friendly_name") == "thermostat"

    entry = registry.async_get(entity_id)
    assert entry
    assert entry.unique_id == uid

    assert await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {
            ATTR_ENTITY_ID: [entity_id],
            ATTR_HVAC_MODE: HVAC_MODE_AUTO,
            ATTR_TEMPERATURE: 25,
        },
        blocking=True,
    )
