"""Tests for Intergas InComfort integration."""

from datetime import timedelta
from unittest.mock import MagicMock, patch

from aiohttp import ClientResponseError
from freezegun.api import FrozenDateTimeFactory
from incomfortclient import IncomfortError
import pytest
from syrupy import SnapshotAssertion

from homeassistant.components.incomfort import DOMAIN
from homeassistant.components.incomfort.coordinator import UPDATE_INTERVAL
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.util.dt import utcnow

from .conftest import MOCK_CONFIG

from tests.common import MockConfigEntry, async_fire_time_changed


async def test_setup_platforms(
    hass: HomeAssistant,
    mock_incomfort: MagicMock,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
) -> None:
    """Test the incomfort integration is set up correctly."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG)
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    entity_entries = er.async_entries_for_config_entry(entity_registry, entry.entry_id)
    assert entity_entries
    for entity_entry in entity_entries:
        assert entity_entry == snapshot(name=f"{entity_entry.entity_id}-entry")
        assert hass.states.get(entity_entry.entity_id) == snapshot(
            name=f"{entity_entry.entity_id}-state"
        )


async def test_coordinator_updates(
    hass: HomeAssistant,
    mock_incomfort: MagicMock,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test the incomfort coordinator is updating."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG)
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    state = hass.states.get("climate.thermostat_1")
    assert state is not None
    assert state.attributes["current_temperature"] == 21.4
    mock_incomfort().mock_room_status["room_temp"] = 20.91

    state = hass.states.get("sensor.boiler_cv_pressure")
    assert state is not None
    assert state.state == "1.86"
    mock_incomfort().mock_heater_status["pressure"] = 1.84

    async_fire_time_changed(hass, utcnow() + timedelta(seconds=UPDATE_INTERVAL))
    await hass.async_block_till_done()

    state = hass.states.get("climate.thermostat_1")
    assert state is not None
    assert state.attributes["current_temperature"] == 20.9

    state = hass.states.get("sensor.boiler_cv_pressure")
    assert state is not None
    assert state.state == "1.84"


@pytest.mark.parametrize(
    "exc",
    [
        IncomfortError(ClientResponseError(None, None, status=401)),
        IncomfortError(ClientResponseError(None, None, status=500)),
        IncomfortError(ValueError("some_error")),
        TimeoutError,
    ],
)
async def test_coordinator_update_fails(
    hass: HomeAssistant,
    mock_incomfort: MagicMock,
    freezer: FrozenDateTimeFactory,
    exc: Exception,
) -> None:
    """Test the incomfort coordinator update fails."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG)
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    state = hass.states.get("sensor.boiler_cv_pressure")
    assert state is not None
    assert state.state == "1.86"

    with patch.object(
        mock_incomfort().heaters.return_value[0], "update", side_effect=exc
    ):
        async_fire_time_changed(hass, utcnow() + timedelta(seconds=UPDATE_INTERVAL))
        await hass.async_block_till_done()

    state = hass.states.get("sensor.boiler_cv_pressure")
    assert state is not None
    assert state.state == STATE_UNAVAILABLE
