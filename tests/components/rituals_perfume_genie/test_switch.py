"""Tests for the Rituals Perfume Genie switch platform."""
from __future__ import annotations

from unittest.mock import patch

from homeassistant.components.homeassistant import SERVICE_UPDATE_ENTITY
from homeassistant.components.rituals_perfume_genie.const import (
    COORDINATORS,
    DOMAIN,
    HUBLOT,
)
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_ICON,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry
from homeassistant.setup import async_setup_component

from .common import (
    init_integration,
    mock_config_entry,
    mock_diffuser_v1_battery_cartridge,
)


async def test_switch_entity(hass: HomeAssistant) -> None:
    """Test the creation and values of the Rituals Perfume Genie diffuser switch."""
    config_entry = mock_config_entry(uniqe_id="id_123_switch_set_state_test")
    diffuser = mock_diffuser_v1_battery_cartridge()
    await init_integration(hass, config_entry, [diffuser])

    registry = entity_registry.async_get(hass)

    state = hass.states.get("switch.genie")
    assert state
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_ICON) == "mdi:fan"

    entry = registry.async_get("switch.genie")
    assert entry
    assert entry.unique_id == diffuser.hub_data[HUBLOT]


async def test_switch_handle_coordinator_update(hass: HomeAssistant) -> None:
    """Test handling a coordinator update."""
    config_entry = mock_config_entry(uniqe_id="id_123_switch_set_state_test")
    diffuser = mock_diffuser_v1_battery_cartridge()
    await init_integration(hass, config_entry, [diffuser])
    await async_setup_component(hass, "homeassistant", {})
    coordinator = hass.data[DOMAIN][config_entry.entry_id][COORDINATORS]["lot123v1"]
    diffuser.is_on = False

    state = hass.states.get("switch.genie")
    assert state
    assert state.state == STATE_ON

    with patch(
        "homeassistant.components.rituals_perfume_genie.RitualsDataUpdateCoordinator._async_update_data",
        return_value=None,
    ) as mock_update:
        await hass.services.async_call(
            "homeassistant",
            SERVICE_UPDATE_ENTITY,
            {ATTR_ENTITY_ID: ["switch.genie"]},
            blocking=True,
        )
    await hass.async_block_till_done()

    state = hass.states.get("switch.genie")
    assert state
    assert state.state == STATE_OFF

    assert coordinator.last_update_success
    mock_update.assert_called_once()


async def test_set_switch_state(hass: HomeAssistant) -> None:
    """Test changing the diffuser switch entity state."""
    config_entry = mock_config_entry(uniqe_id="id_123_switch_set_state_test")
    await init_integration(hass, config_entry, [mock_diffuser_v1_battery_cartridge()])

    state = hass.states.get("switch.genie")
    assert state
    assert state.state == STATE_ON

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: "switch.genie"},
        blocking=True,
    )

    state = hass.states.get("switch.genie")
    assert state
    assert state.state == STATE_OFF

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "switch.genie"},
        blocking=True,
    )

    state = hass.states.get("switch.genie")
    assert state
    assert state.state == STATE_ON
