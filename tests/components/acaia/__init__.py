"""Common test tools for the acaia integration."""

from unittest.mock import MagicMock

from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry


async def setup_integration(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_scale: MagicMock
) -> None:
    """Set up the acaia integration for testing."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
