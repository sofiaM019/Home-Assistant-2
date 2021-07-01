"""Common methods used across tests for Rituals Perfume Genie."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.components.rituals_perfume_genie.const import (
    ACCOUNT_HASH,
    DOMAIN,
    HUBLOT,
    SENSORS,
)
from homeassistant.components.rituals_perfume_genie.entity import (
    ATTRIBUTES,
    AVAILABLE_STATE,
    ROOMNAME,
    STATUS,
    VERSION,
)
from homeassistant.components.rituals_perfume_genie.sensor import (
    FILL,
    FILL_NO_CARTRIDGE_ID,
    ID,
    PERFUME,
    PERFUME_NO_CARTRIDGE_ID,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry


def mock_config_entry(uniqe_id: str, entry_id: str = "an_entry_id") -> MockConfigEntry:
    """Return a mock Config Entry for the Rituals Perfume Genie integration."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="name@example.com",
        unique_id=uniqe_id,
        data={ACCOUNT_HASH: "an_account_hash"},
        entry_id=entry_id,
    )


def mock_diffuser(
    hublot: str,
    available: bool = True,
    battery_percentage: int | Exception = 100,
    charging: bool | Exception = True,
    fill: str = "90-100%",
    has_battery: bool = True,
    has_cartridge: bool = True,
    is_on: bool = True,
    name: str = "Genie",
    perfume: str = "Ritual of Sakura",
    version: str = "4.0",
    wifi_percentage: int = 75,
) -> MagicMock:
    """Return a mock Diffuser initialized with the given data."""
    diffuser_mock = MagicMock()
    diffuser_mock.battery_percentage = battery_percentage
    diffuser_mock.charging = charging
    diffuser_mock.fill = fill
    diffuser_mock.has_battery = has_battery
    diffuser_mock.hub_data = {
        ATTRIBUTES: {ROOMNAME: name},
        HUBLOT: hublot,
        STATUS: AVAILABLE_STATE if available else 0,
        SENSORS: {
            FILL: {ID: 0 if has_cartridge else FILL_NO_CARTRIDGE_ID},
            PERFUME: {ID: 0 if has_cartridge else PERFUME_NO_CARTRIDGE_ID},
            VERSION: version,
        },
    }
    diffuser_mock.is_on = is_on
    diffuser_mock.perfume = perfume
    diffuser_mock.turn_off = AsyncMock()
    diffuser_mock.turn_on = AsyncMock()
    diffuser_mock.update_data = AsyncMock()
    diffuser_mock.wifi_percentage = wifi_percentage
    return diffuser_mock


def mock_diffuser_v1_battery_cartridge():
    """Create and return a mock version 1 Diffuser with battery and a cartridge."""
    return mock_diffuser(hublot="lot123v1")


def mock_diffuser_v2_no_battery_no_cartridge():
    """Create and return a mock version 2 Diffuser without battery and cartridge."""
    return mock_diffuser(
        hublot="lot123v2",
        battery_percentage=Exception(),
        charging=Exception(),
        has_battery=False,
        has_cartridge=False,
        name="Genie V2",
        perfume="No Cartridge",
        version="5.0",
    )


async def init_integration(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_diffusers: list[MagicMock] = [mock_diffuser(hublot="lot123")],
) -> None:
    """Initialize the Rituals Perfume Genie integration with the given Config Entry and Diffuser list."""
    mock_config_entry.add_to_hass(hass)
    with patch(
        "homeassistant.components.rituals_perfume_genie.Account.get_devices",
        return_value=mock_diffusers,
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)

    assert mock_config_entry.state is ConfigEntryState.LOADED
    assert mock_config_entry.entry_id in hass.data[DOMAIN]
    assert hass.data[DOMAIN]

    await hass.async_block_till_done()
