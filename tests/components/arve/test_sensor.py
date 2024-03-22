"""Test for Arve sensors."""

from unittest.mock import MagicMock

from syrupy import SnapshotAssertion

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from . import async_init_integration

from tests.common import MockConfigEntry

SENSORS = (
    "air_quality_index",
    "carbon_dioxide",
    "humidity",
    "pm10",
    "pm2_5",
    "temperature",
    "tvoc",
)


async def test_sensors(
    hass: HomeAssistant,
    mock_arve: MagicMock,
    entity_registry: er.EntityRegistry,
    mock_config_entry: MockConfigEntry,
    snapshot: SnapshotAssertion,
) -> None:
    """Test the Arve sensors."""

    sn = mock_arve.device_sn

    await async_init_integration(hass, mock_config_entry)

    for sensor in SENSORS:
        state = hass.states.get(f"sensor.my_arve_{sensor}")
        assert state
        assert state == snapshot(name=f"my_arve_{sensor}")

        entry = entity_registry.async_get(state.entity_id)
        assert entry
        assert entry.device_id
        assert entry == snapshot(name=f"entry_{sn}_{sensor}")
