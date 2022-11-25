"""Tests for the Blue Current integration."""
from __future__ import annotations

from unittest.mock import patch

from bluecurrent_api import Client

from homeassistant.components.bluecurrent import DOMAIN, Connector
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry


async def init_integration(
    hass: HomeAssistant, platform, data: dict, charge_point: dict, grid=None
) -> MockConfigEntry:
    """Set up the Blue Current integration in Home Assistant."""

    if charge_point:
        data["101"].update(charge_point)

    if grid is None:
        grid = {}

    def init(
        self: Connector, hass: HomeAssistant, config: ConfigEntry, client: Client
    ) -> None:
        """Mock grid and charge_points."""

        self.config = config
        self.hass = hass
        self.client = client
        self.charge_points = data
        self.grid = grid

    with patch(
        "homeassistant.components.bluecurrent.PLATFORMS", [platform]
    ), patch.object(Connector, "__init__", init), patch(
        "homeassistant.components.bluecurrent.Client", autospec=True
    ):

        config_entry = MockConfigEntry(
            domain=DOMAIN,
            entry_id="uuid",
            unique_id="uuid",
            data={"api_token": "123", "card": {"123"}},
        )
        config_entry.add_to_hass(hass)

        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    return config_entry
