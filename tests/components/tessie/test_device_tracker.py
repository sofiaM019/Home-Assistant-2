"""Test the Tessie device tracker platform."""

from syrupy import SnapshotAssertion

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .common import setup_platform, test_entities


async def test_device_tracker(
    hass: HomeAssistant, snapshot: SnapshotAssertion, entity_registry: er.EntityRegistry
) -> None:
    """Tests that the device tracker entities are correct."""

    entry = await setup_platform(hass, [Platform.BINARY_SENSOR])

    test_entities(hass, entry, entity_registry, snapshot)
