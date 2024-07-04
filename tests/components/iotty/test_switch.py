"""Unit tests the Hass SWITCH component."""

from aiohttp import ClientSession
from freezegun.api import FrozenDateTimeFactory
from iottycloud.verbs import RESULT, STATUS, STATUS_OFF, STATUS_ON
import pytest
from syrupy.assertion import SnapshotAssertion

from homeassistant.components.iotty.api import IottyProxy
from homeassistant.components.iotty.const import DOMAIN
from homeassistant.components.iotty.coordinator import UPDATE_INTERVAL
from homeassistant.components.iotty.switch import async_setup_entry
from homeassistant.components.switch import (
    DOMAIN as SWITCH_DOMAIN,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
)
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_oauth2_flow

from .conftest import test_ls_one_added, test_ls_one_removed

from tests.common import MockConfigEntry, async_fire_time_changed


async def test_turn_on_ok(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    local_oauth_impl: ClientSession,
    mock_get_devices_twolightswitches,
    mock_get_status_filled_off,
    mock_command_fn,
) -> None:
    """Issue a turnon command."""

    entity_id = (
        "switch.test_light_switch_0_test_serial_0_test_light_switch_0_test_serial_0"
    )

    mock_config_entry.add_to_hass(hass)

    config_entry_oauth2_flow.async_register_implementation(
        hass, DOMAIN, local_oauth_impl
    )

    await hass.config_entries.async_setup(mock_config_entry.entry_id)

    assert (state := hass.states.get(entity_id))
    assert state.state == STATUS_OFF

    mock_get_status_filled_off.return_value = {RESULT: {STATUS: STATUS_ON}}

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    await hass.async_block_till_done()
    mock_command_fn.assert_called_once()

    assert (state := hass.states.get(entity_id))
    assert state.state == STATUS_ON


async def test_turn_off_ok(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    local_oauth_impl: ClientSession,
    mock_get_devices_twolightswitches,
    mock_get_status_filled,
    mock_command_fn,
) -> None:
    """Issue a turnoff command."""

    entity_id = (
        "switch.test_light_switch_0_test_serial_0_test_light_switch_0_test_serial_0"
    )

    mock_config_entry.add_to_hass(hass)

    config_entry_oauth2_flow.async_register_implementation(
        hass, DOMAIN, local_oauth_impl
    )

    await hass.config_entries.async_setup(mock_config_entry.entry_id)

    assert (state := hass.states.get(entity_id))
    assert state.state == STATUS_ON

    mock_get_status_filled.return_value = {RESULT: {STATUS: STATUS_OFF}}

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    await hass.async_block_till_done()
    mock_command_fn.assert_called_once()

    assert (state := hass.states.get(entity_id))
    assert state.state == STATUS_OFF


async def test_setup_entry_wrongdomaindata_error(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_iotty: IottyProxy,
) -> None:
    """Setup the SWITCH entry with empty or wrong DOMAIN data."""

    with pytest.raises(KeyError):
        await async_setup_entry(hass, mock_config_entry, None)

    hass.data.setdefault(DOMAIN, {})
    with pytest.raises(KeyError):
        await async_setup_entry(hass, mock_config_entry, None)


async def test_setup_entry_ok_nodevices(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    local_oauth_impl: ClientSession,
    mock_get_status_filled,
    snapshot: SnapshotAssertion,
    mock_get_devices_nodevices,
) -> None:
    """Correctly setup, with no iotty Devices to add to Hass."""

    mock_config_entry.add_to_hass(hass)

    config_entry_oauth2_flow.async_register_implementation(
        hass, DOMAIN, local_oauth_impl
    )

    await hass.config_entries.async_setup(mock_config_entry.entry_id)

    assert hass.states.async_entity_ids() == snapshot


async def test_devices_creaction_ok(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    local_oauth_impl: ClientSession,
    mock_get_devices_twolightswitches,
    mock_get_status_filled,
    snapshot: SnapshotAssertion,
) -> None:
    """Test iotty switch creation."""

    mock_config_entry.add_to_hass(hass)

    config_entry_oauth2_flow.async_register_implementation(
        hass, DOMAIN, local_oauth_impl
    )

    await hass.config_entries.async_setup(mock_config_entry.entry_id)

    assert hass.states.async_entity_ids() == snapshot


async def test_devices_deletion_ok(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    local_oauth_impl: ClientSession,
    mock_get_devices_twolightswitches,
    mock_get_status_filled,
    snapshot: SnapshotAssertion,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test iotty switch deletion."""

    mock_config_entry.add_to_hass(hass)

    config_entry_oauth2_flow.async_register_implementation(
        hass, DOMAIN, local_oauth_impl
    )

    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)

    # Should have two devices
    assert hass.states.async_entity_ids() == snapshot

    mock_get_devices_twolightswitches.return_value = test_ls_one_removed

    freezer.tick(UPDATE_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    # Should have one device
    assert hass.states.async_entity_ids() == snapshot


async def test_devices_insertion_ok(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    local_oauth_impl: ClientSession,
    mock_get_devices_twolightswitches,
    mock_get_status_filled,
    snapshot: SnapshotAssertion,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test iotty switch insertion."""

    mock_config_entry.add_to_hass(hass)

    config_entry_oauth2_flow.async_register_implementation(
        hass, DOMAIN, local_oauth_impl
    )

    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)

    # Should have two devices
    assert hass.states.async_entity_ids() == snapshot

    mock_get_devices_twolightswitches.return_value = test_ls_one_added

    freezer.tick(UPDATE_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    # Should have three devices
    assert hass.states.async_entity_ids() == snapshot
