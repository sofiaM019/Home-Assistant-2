"""Test reproduce state for Automation."""
from homeassistant.core import State

from tests.common import async_mock_service


async def test_reproducing_states(hass, caplog):
    """Test reproducing Automation states."""
    hass.states.async_set("automation.entity_off", "off", {})
    hass.states.async_set("automation.entity_on", "on", {})

    turn_on_calls = async_mock_service(hass, "automation", "turn_on")
    turn_off_calls = async_mock_service(hass, "automation", "turn_off")

    # These calls should do nothing as entities already in desired state
    await hass.helpers.state.async_reproduce_state(
        [State("automation.entity_off", "off"), State("automation.entity_on", "on")],
        blocking=True,
    )

    assert len(turn_on_calls) == 0
    assert len(turn_off_calls) == 0

    # Test invalid state is handled
    await hass.helpers.state.async_reproduce_state(
        [State("automation.entity_off", "not_supported")], blocking=True
    )

    assert "not_supported" in caplog.text
    assert len(turn_on_calls) == 0
    assert len(turn_off_calls) == 0

    # Make sure correct services are called
    await hass.helpers.state.async_reproduce_state(
        [
            State("automation.entity_on", "off"),
            State("automation.entity_off", "on"),
            # Should not raise
            State("automation.non_existing", "on"),
        ],
        blocking=True,
    )

    assert len(turn_on_calls) == 1
    assert turn_on_calls[0].domain == "automation"
    assert turn_on_calls[0].data == {"entity_id": "automation.entity_off"}

    assert len(turn_off_calls) == 1
    assert turn_off_calls[0].domain == "automation"
    assert turn_off_calls[0].data == {"entity_id": "automation.entity_on"}
