"""The tests for the filesize sensor."""
import os
from unittest.mock import patch

from homeassistant.const import CONF_FILE_PATH, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_component import async_update_entity

from . import TEST_FILE, TEST_FILE_NAME, create_file

from tests.common import MockConfigEntry


async def test_invalid_path(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Test that an invalid path is caught."""
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry, unique_id=TEST_FILE, data={CONF_FILE_PATH: TEST_FILE}
    )

    state = hass.states.get("sensor." + TEST_FILE_NAME)
    assert not state


async def test_cannot_access_file(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Test that an invalid path is caught."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.filesize.sensor.pathlib",
        side_effect=OSError("Can not access"),
    ):
        hass.config_entries.async_update_entry(
            mock_config_entry, unique_id=TEST_FILE, data={CONF_FILE_PATH: TEST_FILE}
        )
        await hass.async_block_till_done()

    state = hass.states.get("sensor." + TEST_FILE_NAME)
    assert not state


async def test_valid_path(
    hass: HomeAssistant, tmpdir: str, mock_config_entry: MockConfigEntry
) -> None:
    """Test for a valid path."""
    testfile = f"{tmpdir}/file.txt"
    create_file(testfile)
    hass.config.allowlist_external_dirs = {tmpdir}
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry, unique_id=testfile, data={CONF_FILE_PATH: testfile}
    )

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.file_txt")
    assert state
    assert state.state == "0.0"
    assert state.attributes.get("bytes") == 4

    await hass.async_add_executor_job(os.remove, testfile)


async def test_state_unknown(
    hass: HomeAssistant, tmpdir: str, mock_config_entry: MockConfigEntry
) -> None:
    """Verify we handle state unavailable."""
    testfile = f"{tmpdir}/file"
    create_file(testfile)
    hass.config.allowlist_external_dirs = {tmpdir}
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry, unique_id=testfile, data={CONF_FILE_PATH: testfile}
    )

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.file")
    assert state
    assert state.state == "0.0"

    await hass.async_add_executor_job(os.remove, testfile)
    await async_update_entity(hass, "sensor.file")

    state = hass.states.get("sensor.file")
    assert state.state == STATE_UNKNOWN
