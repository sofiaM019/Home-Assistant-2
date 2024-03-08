"""The tests for Netgear LTE binary sensor platform."""

from syrupy.assertion import SnapshotAssertion

from homeassistant.components.binary_sensor import DOMAIN as BINARY_SENSOR_DOMAIN
from homeassistant.components.netgear_lte.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er


async def test_binary_sensors(
    hass: HomeAssistant,
    entity_registry_enabled_by_default: None,
    setup_integration: None,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
) -> None:
    """Test for successfully setting up the Netgear LTE binary sensor platform."""
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    entity_entries = er.async_entries_for_config_entry(entity_registry, entry.entry_id)

    assert entity_entries
    for entity_entry in entity_entries:
        if entity_entry.domain != BINARY_SENSOR_DOMAIN:
            continue
        assert hass.states.get(entity_entry.entity_id) == snapshot(
            name=entity_entry.entity_id
        )
