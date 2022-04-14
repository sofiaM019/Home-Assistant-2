"""Test UPnP/IGD config flow."""

from copy import deepcopy
from datetime import timedelta

import pytest

from homeassistant import config_entries, data_entry_flow
from homeassistant.components import ssdp
from homeassistant.components.upnp.const import (
    CONFIG_ENTRY_LOCATION,
    CONFIG_ENTRY_MAC_ADDRESS,
    CONFIG_ENTRY_ORIGINAL_UDN,
    CONFIG_ENTRY_ST,
    CONFIG_ENTRY_UDN,
    DOMAIN,
)
from homeassistant.core import HomeAssistant

from .conftest import (
    TEST_DISCOVERY,
    TEST_FRIENDLY_NAME,
    TEST_LOCATION,
    TEST_MAC_ADDRESS,
    TEST_ST,
    TEST_UDN,
    TEST_USN,
)

from tests.common import MockConfigEntry


@pytest.mark.usefixtures(
    "ssdp_instant_discovery",
    "mock_setup_entry",
    "mock_get_source_ip",
)
async def test_flow_ssdp(hass: HomeAssistant):
    """Test config flow: discovered + configured through ssdp."""
    # Discovered via step ssdp.
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_SSDP},
        data=TEST_DISCOVERY,
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "ssdp_confirm"

    # Confirm via step ssdp_confirm.
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={},
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == TEST_FRIENDLY_NAME
    assert result["data"] == {
        CONFIG_ENTRY_ST: TEST_ST,
        CONFIG_ENTRY_UDN: TEST_UDN,
        CONFIG_ENTRY_ORIGINAL_UDN: TEST_UDN,
        CONFIG_ENTRY_LOCATION: TEST_LOCATION,
        CONFIG_ENTRY_MAC_ADDRESS: TEST_MAC_ADDRESS,
    }


@pytest.mark.usefixtures("mock_get_source_ip")
async def test_flow_ssdp_incomplete_discovery(hass: HomeAssistant):
    """Test config flow: incomplete discovery through ssdp."""
    # Discovered via step ssdp.
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_SSDP},
        data=ssdp.SsdpServiceInfo(
            ssdp_usn=TEST_USN,
            ssdp_st=TEST_ST,
            ssdp_location=TEST_LOCATION,
            upnp={
                # ssdp.ATTR_UPNP_UDN: TEST_UDN,  # Not provided.
            },
        ),
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "incomplete_discovery"


async def test_flow_ssdp_discovery_changed_udn(hass: HomeAssistant):
    """Test config flow: discovery through ssdp, same device, but new UDN, matched on mac address."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=TEST_USN,
        data={
            CONFIG_ENTRY_ST: TEST_ST,
            CONFIG_ENTRY_UDN: TEST_UDN,
            CONFIG_ENTRY_ORIGINAL_UDN: TEST_UDN,
            CONFIG_ENTRY_LOCATION: TEST_LOCATION,
            CONFIG_ENTRY_MAC_ADDRESS: TEST_MAC_ADDRESS,
        },
        source=config_entries.SOURCE_SSDP,
    )
    entry.add_to_hass(hass)

    # New discovery via step ssdp.
    new_udn = TEST_UDN + "2"
    new_discovery = deepcopy(TEST_DISCOVERY)
    new_discovery.ssdp_usn = f"{new_udn}::{TEST_ST}"
    new_discovery.upnp["_udn"] = new_udn
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_SSDP},
        data=new_discovery,
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "config_entry_updated"


async def test_flow_ssdp_discovery_changed_location(hass: HomeAssistant):
    """Test config flow: discovery through ssdp, same device, but new location."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=TEST_USN,
        data={
            CONFIG_ENTRY_ST: TEST_ST,
            CONFIG_ENTRY_UDN: TEST_UDN,
            CONFIG_ENTRY_ORIGINAL_UDN: TEST_UDN,
            CONFIG_ENTRY_LOCATION: TEST_LOCATION,
            CONFIG_ENTRY_MAC_ADDRESS: TEST_MAC_ADDRESS,
        },
        source=config_entries.SOURCE_SSDP,
    )
    entry.add_to_hass(hass)

    # Discovery via step ssdp.
    new_location = TEST_DISCOVERY.ssdp_location + "2"
    new_discovery = deepcopy(TEST_DISCOVERY)
    new_discovery.ssdp_location = new_location
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_SSDP},
        data=new_discovery,
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"

    # Test if location is updated.
    assert entry.data[CONFIG_ENTRY_LOCATION] == new_location


async def test_flow_ssdp_discovery_ignored_entry(hass: HomeAssistant):
    """Test config flow: discovery through ssdp, same device, but new UDN, matched on mac address."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=TEST_USN,
        data={
            CONFIG_ENTRY_ST: TEST_ST,
            CONFIG_ENTRY_UDN: TEST_UDN,
            CONFIG_ENTRY_ORIGINAL_UDN: TEST_UDN,
            CONFIG_ENTRY_LOCATION: TEST_LOCATION,
            CONFIG_ENTRY_MAC_ADDRESS: TEST_MAC_ADDRESS,
        },
        source=config_entries.SOURCE_IGNORE,
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_SSDP},
        data=TEST_DISCOVERY,
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"


async def test_flow_ssdp_discovery_changed_udn_ignored_entry(hass: HomeAssistant):
    """Test config flow: discovery through ssdp, same device, but new UDN, matched on mac address, entry ignored."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=TEST_USN,
        data={
            CONFIG_ENTRY_ST: TEST_ST,
            CONFIG_ENTRY_UDN: TEST_UDN,
            CONFIG_ENTRY_ORIGINAL_UDN: TEST_UDN,
            CONFIG_ENTRY_LOCATION: TEST_LOCATION,
            CONFIG_ENTRY_MAC_ADDRESS: TEST_MAC_ADDRESS,
        },
        source=config_entries.SOURCE_IGNORE,
    )
    entry.add_to_hass(hass)

    # New discovery via step ssdp.
    new_udn = TEST_UDN + "2"
    new_discovery = deepcopy(TEST_DISCOVERY)
    new_discovery.ssdp_usn = f"{new_udn}::{TEST_ST}"
    new_discovery.upnp["_udn"] = new_udn
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_SSDP},
        data=new_discovery,
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "discovery_ignored"


@pytest.mark.usefixtures(
    "ssdp_instant_discovery", "mock_setup_entry", "mock_get_source_ip"
)
async def test_flow_user(hass: HomeAssistant):
    """Test config flow: discovered + configured through user."""
    # Discovered via step user.
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    # Confirmed via step user.
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"unique_id": TEST_USN},
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == TEST_FRIENDLY_NAME
    assert result["data"] == {
        CONFIG_ENTRY_ST: TEST_ST,
        CONFIG_ENTRY_UDN: TEST_UDN,
        CONFIG_ENTRY_ORIGINAL_UDN: TEST_UDN,
        CONFIG_ENTRY_LOCATION: TEST_LOCATION,
        CONFIG_ENTRY_MAC_ADDRESS: TEST_MAC_ADDRESS,
    }


@pytest.mark.usefixtures(
    "ssdp_instant_discovery",
    "mock_setup_entry",
    "mock_get_source_ip",
)
async def test_flow_import(hass: HomeAssistant):
    """Test config flow: configured through configuration.yaml."""
    # Discovered via step import.
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_IMPORT}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == TEST_FRIENDLY_NAME
    assert result["data"] == {
        CONFIG_ENTRY_ST: TEST_ST,
        CONFIG_ENTRY_UDN: TEST_UDN,
        CONFIG_ENTRY_ORIGINAL_UDN: TEST_UDN,
        CONFIG_ENTRY_LOCATION: TEST_LOCATION,
        CONFIG_ENTRY_MAC_ADDRESS: TEST_MAC_ADDRESS,
    }


@pytest.mark.usefixtures("ssdp_instant_discovery", "mock_get_source_ip")
async def test_flow_import_already_configured(hass: HomeAssistant):
    """Test config flow: configured through configuration.yaml, but existing config entry."""
    # Existing entry.
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=TEST_USN,
        data={
            CONFIG_ENTRY_ST: TEST_ST,
            CONFIG_ENTRY_UDN: TEST_UDN,
            CONFIG_ENTRY_ORIGINAL_UDN: TEST_UDN,
            CONFIG_ENTRY_LOCATION: TEST_LOCATION,
            CONFIG_ENTRY_MAC_ADDRESS: TEST_MAC_ADDRESS,
        },
    )
    entry.add_to_hass(hass)

    # Discovered via step import.
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_IMPORT}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"


@pytest.mark.usefixtures("ssdp_no_discovery", "mock_get_source_ip")
async def test_flow_import_no_devices_found(hass: HomeAssistant):
    """Test config flow: no devices found, configured through configuration.yaml."""
    # Discovered via step import.
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_IMPORT}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "no_devices_found"
