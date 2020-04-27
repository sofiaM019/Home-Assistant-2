"""The config flow tests for the forked_daapd media player platform."""

from unittest.mock import patch

import pytest

from homeassistant import data_entry_flow
from homeassistant.components.forked_daapd.const import (
    CONF_PIPE_CONTROL,
    CONF_TTS_PAUSE_TIME,
    CONF_TTS_VOLUME,
    CONFIG_FLOW_UNIQUE_ID,
    DOMAIN,
    FD_NAME,
)
from homeassistant.config_entries import (
    CONN_CLASS_LOCAL_PUSH,
    SOURCE_USER,
    SOURCE_ZEROCONF,
)
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT

from tests.common import MockConfigEntry

SAMPLE_CONFIG = {
    "websocket_port": 3688,
    "version": "25.0",
    "buildoptions": [
        "ffmpeg",
        "iTunes XML",
        "Spotify",
        "LastFM",
        "MPD",
        "Device verification",
        "Websockets",
        "ALSA",
    ],
}


@pytest.fixture(name="config_entry")
def config_entry_fixture():
    """Create hass config_entry fixture."""
    data = {
        CONF_HOST: "192.168.1.1",
        CONF_PORT: "2345",
        CONF_PASSWORD: "",
    }
    return MockConfigEntry(
        version=1,
        domain=DOMAIN,
        title="",
        data=data,
        options={},
        system_options={},
        source=SOURCE_USER,
        connection_class=CONN_CLASS_LOCAL_PUSH,
        unique_id=CONFIG_FLOW_UNIQUE_ID,
        entry_id=1,
    )


async def test_show_form(hass):
    """Test that the form is served with no input."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == SOURCE_USER


async def test_config_flow(hass, config_entry):
    """Test that the user step works."""
    with patch(
        "homeassistant.components.forked_daapd.config_flow.ForkedDaapdAPI.test_connection"
    ) as mock_test_connection:
        with patch(
            "homeassistant.components.forked_daapd.media_player.ForkedDaapdAPI.get_request"
        ) as mock_get_request:
            mock_get_request.return_value = SAMPLE_CONFIG
            mock_test_connection.return_value = "ok"
            config_data = config_entry.data
            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": SOURCE_USER}, data=config_data
            )
            await hass.async_block_till_done()
            assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
            assert result["title"] == f"{FD_NAME} server"
            assert result["data"][CONF_HOST] == config_data[CONF_HOST]
            assert result["data"][CONF_PORT] == config_data[CONF_PORT]
            assert result["data"][CONF_PASSWORD] == config_data[CONF_PASSWORD]

            # remove entry
            await config_entry.async_unload(hass)

        # test invalid config data
        mock_test_connection.return_value = "websocket_not_enabled"
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=config_data
        )
        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM


async def test_config_flow_zeroconf(hass):
    """Test that the user step works."""
    # test invalid zeroconf entry
    discovery_info = {"host": "127.0.0.1", "port": 23}
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=discovery_info
    )  # doesn't create the entry, tries to show form but gets abort
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "not_forked_daapd"

    # now test valid entry
    discovery_info["properties"] = {
        "mtd-version": 1,
        "Machine Name": "zeroconf_test",
    }
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=discovery_info
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM


async def test_options_flow(hass, config_entry):
    """Test config flow options."""

    with patch(
        "homeassistant.components.forked_daapd.media_player.ForkedDaapdAPI.get_request"
    ) as mock_get_request:
        mock_get_request.return_value = SAMPLE_CONFIG
        config_entry.add_to_hass(hass)
        await config_entry.async_setup(hass)
        await hass.async_block_till_done()

        result = await hass.config_entries.options.async_init(config_entry.entry_id)
        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_TTS_PAUSE_TIME: 0.05,
                CONF_TTS_VOLUME: 0.8,
                CONF_PIPE_CONTROL: "",
            },
        )
