"""The tests for the group fan platform."""
from datetime import timedelta

import pytest

from homeassistant.components.fan import (
    ATTR_DIRECTION,
    ATTR_OSCILLATING,
    ATTR_PERCENTAGE,
    ATTR_PERCENTAGE_STEP,
    DIRECTION_FORWARD,
    DIRECTION_REVERSE,
    DOMAIN,
    PLATFORM_SCHEMA,
    SERVICE_OSCILLATE,
    SERVICE_SET_DIRECTION,
    SERVICE_SET_PERCENTAGE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    SUPPORT_DIRECTION,
    SUPPORT_OSCILLATE,
    SUPPORT_SET_SPEED,
)
from homeassistant.components.group.fan import DEFAULT_NAME
from homeassistant.const import (
    ATTR_ASSUMED_STATE,
    ATTR_ENTITY_ID,
    ATTR_FRIENDLY_NAME,
    ATTR_SUPPORTED_FEATURES,
    CONF_ENTITIES,
    CONF_UNIQUE_ID,
    EVENT_HOMEASSISTANT_START,
    STATE_OFF,
    STATE_ON,
)
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component
import homeassistant.util.dt as dt_util

from tests.common import assert_setup_component, async_fire_time_changed

FAN_GROUP = "fan.fan_group"

LIVING_ROOM_FAN_ENTITY_ID = "fan.living_room_fan"
PERCENTAGE_FULL_FAN_ENTITY_ID = "fan.percentage_full_fan"
CEILING_FAN_ENTITY_ID = "fan.ceiling_fan"
PERCENTAGE_LIMITED_FAN_ENTITY_ID = "fan.percentage_limited_fan"

FULL_FAN_ENTITY_IDS = [LIVING_ROOM_FAN_ENTITY_ID, PERCENTAGE_FULL_FAN_ENTITY_ID]
LIMITED_FAN_ENTITY_IDS = [CEILING_FAN_ENTITY_ID, PERCENTAGE_LIMITED_FAN_ENTITY_ID]


FULL_SUPPORT_FEATURES = SUPPORT_SET_SPEED | SUPPORT_DIRECTION | SUPPORT_OSCILLATE


CONFIG_ALL = {
    DOMAIN: [
        {
            "platform": "group",
            CONF_ENTITIES: [*FULL_FAN_ENTITY_IDS, *LIMITED_FAN_ENTITY_IDS],
        },
    ]
}

CONFIG_FULL_SUPPORT = {
    DOMAIN: [
        {
            "platform": "group",
            CONF_ENTITIES: [*FULL_FAN_ENTITY_IDS],
        },
    ]
}

CONFIG_LIMITED_SUPPORT = {
    DOMAIN: [
        {
            "platform": "group",
            CONF_ENTITIES: [*LIMITED_FAN_ENTITY_IDS],
        },
    ]
}


CONFIG_ATTRIBUTES = {
    DOMAIN: {
        "platform": "group",
        CONF_ENTITIES: [*FULL_FAN_ENTITY_IDS, *LIMITED_FAN_ENTITY_IDS],
        CONF_UNIQUE_ID: "unique_identifier",
    }
}


@pytest.fixture
async def setup_comp(hass, config_count):
    """Set up group fan component."""
    config, count = config_count
    with assert_setup_component(count, DOMAIN):
        await async_setup_component(hass, DOMAIN, config)
    await hass.async_block_till_done()
    await hass.async_start()
    await hass.async_block_till_done()


@pytest.mark.parametrize("config_count", [(CONFIG_ATTRIBUTES, 1)])
async def test_state(hass, setup_comp):
    """Test handling of state."""
    state = hass.states.get(FAN_GROUP)
    # No entity has a valid state -> group state off
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_FRIENDLY_NAME] == DEFAULT_NAME
    assert state.attributes[ATTR_ENTITY_ID] == [
        *FULL_FAN_ENTITY_IDS,
        *LIMITED_FAN_ENTITY_IDS,
    ]
    assert ATTR_ASSUMED_STATE not in state.attributes
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 0

    # Set all entities as on -> group state on
    hass.states.async_set(CEILING_FAN_ENTITY_ID, STATE_ON, {})
    hass.states.async_set(LIVING_ROOM_FAN_ENTITY_ID, STATE_ON, {})
    hass.states.async_set(PERCENTAGE_FULL_FAN_ENTITY_ID, STATE_ON, {})
    hass.states.async_set(PERCENTAGE_LIMITED_FAN_ENTITY_ID, STATE_ON, {})
    await hass.async_block_till_done()
    state = hass.states.get(FAN_GROUP)
    assert state.state == STATE_ON

    # Set all entities as off -> group state off
    hass.states.async_set(CEILING_FAN_ENTITY_ID, STATE_OFF, {})
    hass.states.async_set(LIVING_ROOM_FAN_ENTITY_ID, STATE_OFF, {})
    hass.states.async_set(PERCENTAGE_FULL_FAN_ENTITY_ID, STATE_OFF, {})
    hass.states.async_set(PERCENTAGE_LIMITED_FAN_ENTITY_ID, STATE_OFF, {})
    await hass.async_block_till_done()
    state = hass.states.get(FAN_GROUP)
    assert state.state == STATE_OFF

    # Set first entity as on -> group state on
    hass.states.async_set(CEILING_FAN_ENTITY_ID, STATE_ON, {})
    hass.states.async_set(LIVING_ROOM_FAN_ENTITY_ID, STATE_OFF, {})
    hass.states.async_set(PERCENTAGE_FULL_FAN_ENTITY_ID, STATE_OFF, {})
    hass.states.async_set(PERCENTAGE_LIMITED_FAN_ENTITY_ID, STATE_OFF, {})
    await hass.async_block_till_done()
    state = hass.states.get(FAN_GROUP)
    assert state.state == STATE_ON

    # Set last entity as on -> group state on
    hass.states.async_set(CEILING_FAN_ENTITY_ID, STATE_OFF, {})
    hass.states.async_set(LIVING_ROOM_FAN_ENTITY_ID, STATE_OFF, {})
    hass.states.async_set(PERCENTAGE_FULL_FAN_ENTITY_ID, STATE_OFF, {})
    hass.states.async_set(PERCENTAGE_LIMITED_FAN_ENTITY_ID, STATE_ON, {})
    await hass.async_block_till_done()
    state = hass.states.get(FAN_GROUP)
    assert state.state == STATE_ON

    # now remove an entity
    hass.states.async_remove(PERCENTAGE_LIMITED_FAN_ENTITY_ID)
    await hass.async_block_till_done()
    state = hass.states.get(FAN_GROUP)
    assert state.state == STATE_OFF
    assert ATTR_ASSUMED_STATE not in state.attributes
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 0


@pytest.mark.parametrize("config_count", [(CONFIG_ATTRIBUTES, 1)])
async def test_attributes(hass, setup_comp):
    """Test handling of state attributes."""
    state = hass.states.get(FAN_GROUP)
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_FRIENDLY_NAME] == DEFAULT_NAME
    assert state.attributes[ATTR_ENTITY_ID] == [
        *FULL_FAN_ENTITY_IDS,
        *LIMITED_FAN_ENTITY_IDS,
    ]
    assert ATTR_ASSUMED_STATE not in state.attributes
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 0
    hass.states.async_set(CEILING_FAN_ENTITY_ID, STATE_ON, {})
    hass.states.async_set(LIVING_ROOM_FAN_ENTITY_ID, STATE_ON, {})
    hass.states.async_set(PERCENTAGE_FULL_FAN_ENTITY_ID, STATE_ON, {})
    hass.states.async_set(PERCENTAGE_LIMITED_FAN_ENTITY_ID, STATE_ON, {})
    await hass.async_block_till_done()
    state = hass.states.get(FAN_GROUP)
    assert state.state == STATE_ON

    # Add Entity that supports speed
    hass.states.async_set(
        CEILING_FAN_ENTITY_ID,
        STATE_ON,
        {
            ATTR_SUPPORTED_FEATURES: SUPPORT_SET_SPEED,
            ATTR_PERCENTAGE: 50,
        },
    )
    await hass.async_block_till_done()

    state = hass.states.get(FAN_GROUP)
    assert state.state == STATE_ON
    assert ATTR_ASSUMED_STATE not in state.attributes
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == SUPPORT_SET_SPEED
    assert ATTR_PERCENTAGE in state.attributes
    assert state.attributes[ATTR_PERCENTAGE] == 50
    assert ATTR_ASSUMED_STATE not in state.attributes

    # Add Entity that supports
    # ### Test assumed state ###
    # ##########################

    # Add Entity with a different speed should set assumed state
    hass.states.async_set(
        PERCENTAGE_LIMITED_FAN_ENTITY_ID,
        STATE_ON,
        {
            ATTR_SUPPORTED_FEATURES: SUPPORT_SET_SPEED,
            ATTR_PERCENTAGE: 75,
        },
    )
    await hass.async_block_till_done()

    state = hass.states.get(FAN_GROUP)
    assert state.state == STATE_ON
    assert state.attributes[ATTR_ASSUMED_STATE] is True
    assert state.attributes[ATTR_PERCENTAGE] == int((50 + 75) / 2)


@pytest.mark.parametrize("config_count", [(CONFIG_FULL_SUPPORT, 1)])
async def test_direction_oscillating(hass, setup_comp):
    """Test handling of direction and oscillating attributes."""

    hass.states.async_set(
        LIVING_ROOM_FAN_ENTITY_ID,
        STATE_ON,
        {
            ATTR_SUPPORTED_FEATURES: FULL_SUPPORT_FEATURES,
            ATTR_OSCILLATING: True,
            ATTR_DIRECTION: DIRECTION_FORWARD,
            ATTR_PERCENTAGE: 50,
        },
    )
    hass.states.async_set(
        PERCENTAGE_FULL_FAN_ENTITY_ID,
        STATE_ON,
        {
            ATTR_SUPPORTED_FEATURES: FULL_SUPPORT_FEATURES,
            ATTR_OSCILLATING: True,
            ATTR_DIRECTION: DIRECTION_FORWARD,
            ATTR_PERCENTAGE: 50,
        },
    )
    await hass.async_block_till_done()

    state = hass.states.get(FAN_GROUP)
    assert state.state == STATE_ON
    assert state.attributes[ATTR_FRIENDLY_NAME] == DEFAULT_NAME
    assert state.attributes[ATTR_ENTITY_ID] == [*FULL_FAN_ENTITY_IDS]
    assert ATTR_ASSUMED_STATE not in state.attributes
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == FULL_SUPPORT_FEATURES
    assert ATTR_PERCENTAGE in state.attributes
    assert state.attributes[ATTR_PERCENTAGE] == 50
    assert state.attributes[ATTR_OSCILLATING] is True
    assert state.attributes[ATTR_DIRECTION] == DIRECTION_FORWARD
    assert ATTR_ASSUMED_STATE not in state.attributes

    # Add Entity that supports
    # ### Test assumed state ###
    # ##########################

    # Add Entity with a different direction should set assumed state
    hass.states.async_set(
        PERCENTAGE_FULL_FAN_ENTITY_ID,
        STATE_ON,
        {
            ATTR_SUPPORTED_FEATURES: FULL_SUPPORT_FEATURES,
            ATTR_OSCILLATING: True,
            ATTR_DIRECTION: DIRECTION_REVERSE,
            ATTR_PERCENTAGE: 50,
        },
    )
    await hass.async_block_till_done()

    state = hass.states.get(FAN_GROUP)
    assert state.state == STATE_ON
    assert state.attributes[ATTR_ASSUMED_STATE] is True
    assert ATTR_PERCENTAGE in state.attributes
    assert state.attributes[ATTR_PERCENTAGE] == 50
    assert state.attributes[ATTR_OSCILLATING] is True
    assert ATTR_ASSUMED_STATE in state.attributes

    # Now that everything is the same, no longer assumed state

    hass.states.async_set(
        LIVING_ROOM_FAN_ENTITY_ID,
        STATE_ON,
        {
            ATTR_SUPPORTED_FEATURES: FULL_SUPPORT_FEATURES,
            ATTR_OSCILLATING: True,
            ATTR_DIRECTION: DIRECTION_REVERSE,
            ATTR_PERCENTAGE: 50,
        },
    )
    await hass.async_block_till_done()

    state = hass.states.get(FAN_GROUP)
    assert state.state == STATE_ON
    assert ATTR_PERCENTAGE in state.attributes
    assert state.attributes[ATTR_PERCENTAGE] == 50
    assert state.attributes[ATTR_OSCILLATING] is True
    assert state.attributes[ATTR_DIRECTION] == DIRECTION_REVERSE
    assert ATTR_ASSUMED_STATE not in state.attributes
