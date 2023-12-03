"""Test the Advantage Air Switch Platform."""

from homeassistant.components.switch import (
    DOMAIN as SWITCH_DOMAIN,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
)
from homeassistant.const import ATTR_ENTITY_ID, STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from . import add_mock_config, patch_get, patch_update


async def test_cover_async_setup_entry(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test switch platform."""
    with patch_get(), patch_update() as mock_update:
        await add_mock_config(hass)

        # Test Switch Entity
        entity_id = "switch.myzone_fresh_air"
        state = hass.states.get(entity_id)
        assert state
        assert state.state == STATE_OFF

        entry = entity_registry.async_get(entity_id)
        assert entry
        assert entry.unique_id == "uniqueid-ac1-freshair"

        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: [entity_id]},
            blocking=True,
        )
        mock_update.assert_called_once()
        mock_update.reset_mock()

        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: [entity_id]},
            blocking=True,
        )
        mock_update.assert_called_once()


async def test_things_switch(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test things switches."""
    with patch_get(), patch_update() as mock_update:
        await add_mock_config(hass)

        # Test Switch Entity
        entity_id = "switch.relay"
        thing_id = "205"
        state = hass.states.get(entity_id)
        assert state
        assert state.state == STATE_ON

        entry = entity_registry.async_get(entity_id)
        assert entry
        assert entry.unique_id == f"uniqueid-{thing_id}"

        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: [entity_id]},
            blocking=True,
        )
        mock_update.assert_called_once()
        mock_update.reset_mock()

        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: [entity_id]},
            blocking=True,
        )
        mock_update.assert_called_once()
