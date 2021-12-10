"""Tests for the config_flow of the twinly component."""

from unittest.mock import patch

from homeassistant import config_entries
from homeassistant.components.twinkly.const import (
    CONF_ENTRY_HOST,
    CONF_ENTRY_ID,
    CONF_ENTRY_MODEL,
    CONF_ENTRY_NAME,
    DOMAIN as TWINKLY_DOMAIN,
)

from . import TEST_MODEL, ClientMock


async def test_invalid_host(hass):
    """Test the failure when invalid host provided."""
    client = ClientMock()
    client.is_offline = True
    with patch("twinkly_client.TwinklyClient", return_value=client):
        result = await hass.config_entries.flow.async_init(
            TWINKLY_DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] == "form"
        assert result["step_id"] == "user"
        assert result["errors"] == {}
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_ENTRY_HOST: "dummy"},
        )

    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert result["errors"] == {CONF_ENTRY_HOST: "cannot_connect"}


async def test_success_flow(hass):
    """Test that an entity is created when the flow completes."""
    client = ClientMock()
    with patch("twinkly_client.TwinklyClient", return_value=client):
        result = await hass.config_entries.flow.async_init(
            TWINKLY_DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        assert result["type"] == "form"
        assert result["step_id"] == "user"
        assert result["errors"] == {}

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_ENTRY_HOST: "dummy"},
        )

    assert result["type"] == "create_entry"
    assert result["title"] == client.id
    assert result["data"] == {
        CONF_ENTRY_HOST: "dummy",
        CONF_ENTRY_ID: client.id,
        CONF_ENTRY_NAME: client.id,
        CONF_ENTRY_MODEL: TEST_MODEL,
    }


async def test_dhcp_can_confirm(hass):
    """Test DHCP discovery flow can confirm right away."""
    client = ClientMock()
    with patch("twinkly_client.TwinklyClient", return_value=client):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DHCP},
            data=dhcp.DhcpServiceInfo(
                hostname="Twinkly_XYZ",
                ip="1.2.3.4",
                macaddress="aa:bb:cc:dd:ee:ff",
            ),
        )
        await hass.async_block_till_done()

    assert result["type"] == "form"
    assert result["step_id"] == "confirm"


async def test_dhcp_already_exists(hass):
    """Test DHCP discovery flow that fails to connect."""
    client = ClientMock()

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "1.2.3.4"},
        unique_id=client.id,
    )
    entry.add_to_hass(hass)

    client = ClientMock()
    with patch("twinkly_client.TwinklyClient", return_value=client):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DHCP},
            data=dhcp.DhcpServiceInfo(
                hostname="Twinkly_XYZ",
                ip="1.2.3.4",
                macaddress="aa:bb:cc:dd:ee:ff",
            ),
        )
        await hass.async_block_till_done()

    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"
