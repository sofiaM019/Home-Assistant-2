"""Test UniFi Network integration setup process."""

from typing import Any
from unittest.mock import patch

from aiounifi.models.message import MessageKey

from homeassistant.components import unifi
from homeassistant.components.unifi.const import (
    CONF_ALLOW_BANDWIDTH_SENSORS,
    CONF_ALLOW_UPTIME_SENSORS,
    CONF_TRACK_CLIENTS,
    CONF_TRACK_DEVICES,
    DOMAIN as UNIFI_DOMAIN,
)
from homeassistant.components.unifi.errors import AuthenticationRequired, CannotConnect
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.setup import async_setup_component

from .test_hub import DEFAULT_CONFIG_ENTRY_ID, setup_unifi_integration

from tests.common import flush_store
from tests.test_util.aiohttp import AiohttpClientMocker
from tests.typing import WebSocketGenerator


async def test_setup_with_no_config(hass: HomeAssistant) -> None:
    """Test that we do not discover anything or try to set up a hub."""
    assert await async_setup_component(hass, UNIFI_DOMAIN, {}) is True
    assert UNIFI_DOMAIN not in hass.data


async def test_successful_config_entry(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test that configured options for a host are loaded via config entry."""
    await setup_unifi_integration(hass, aioclient_mock)
    assert hass.data[UNIFI_DOMAIN]


async def test_setup_entry_fails_config_entry_not_ready(hass: HomeAssistant) -> None:
    """Failed authentication trigger a reauthentication flow."""
    with patch(
        "homeassistant.components.unifi.get_unifi_api",
        side_effect=CannotConnect,
    ):
        await setup_unifi_integration(hass)

    assert hass.data[UNIFI_DOMAIN] == {}


async def test_setup_entry_fails_trigger_reauth_flow(hass: HomeAssistant) -> None:
    """Failed authentication trigger a reauthentication flow."""
    with (
        patch(
            "homeassistant.components.unifi.get_unifi_api",
            side_effect=AuthenticationRequired,
        ),
        patch.object(hass.config_entries.flow, "async_init") as mock_flow_init,
    ):
        await setup_unifi_integration(hass)
        mock_flow_init.assert_called_once()

    assert hass.data[UNIFI_DOMAIN] == {}


async def test_unload_entry(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test being able to unload an entry."""
    config_entry = await setup_unifi_integration(hass, aioclient_mock)
    assert hass.data[UNIFI_DOMAIN]

    assert await hass.config_entries.async_unload(config_entry.entry_id)
    assert not hass.data[UNIFI_DOMAIN]


async def test_wireless_clients(
    hass: HomeAssistant,
    hass_storage: dict[str, Any],
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Verify wireless clients class."""
    hass_storage[unifi.STORAGE_KEY] = {
        "version": unifi.STORAGE_VERSION,
        "data": {
            DEFAULT_CONFIG_ENTRY_ID: {
                "wireless_devices": ["00:00:00:00:00:00", "00:00:00:00:00:01"]
            }
        },
    }

    client_1 = {
        "hostname": "client_1",
        "ip": "10.0.0.1",
        "is_wired": False,
        "mac": "00:00:00:00:00:01",
    }
    client_2 = {
        "hostname": "client_2",
        "ip": "10.0.0.2",
        "is_wired": False,
        "mac": "00:00:00:00:00:02",
    }
    await setup_unifi_integration(
        hass, aioclient_mock, clients_response=[client_1, client_2]
    )
    await flush_store(hass.data[unifi.UNIFI_WIRELESS_CLIENTS]._store)

    assert sorted(hass_storage[unifi.STORAGE_KEY]["data"]["wireless_clients"]) == [
        "00:00:00:00:00:00",
        "00:00:00:00:00:01",
        "00:00:00:00:00:02",
    ]


async def test_remove_config_entry_device(
    hass: HomeAssistant,
    hass_storage: dict[str, Any],
    aioclient_mock: AiohttpClientMocker,
    device_registry: dr.DeviceRegistry,
    mock_unifi_websocket,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Verify removing a device manually."""
    client_1 = {
        "hostname": "Wired client",
        "is_wired": True,
        "mac": "00:00:00:00:00:01",
        "oui": "Producer",
        "wired-rx_bytes": 1234000000,
        "wired-tx_bytes": 5678000000,
        "uptime": 1600094505,
    }
    client_2 = {
        "is_wired": False,
        "mac": "00:00:00:00:00:02",
        "name": "Wireless client",
        "oui": "Producer",
        "rx_bytes": 2345000000,
        "tx_bytes": 6789000000,
        "uptime": 60,
    }
    device_1 = {
        "board_rev": 3,
        "device_id": "mock-id",
        "has_fan": True,
        "fan_level": 0,
        "ip": "10.0.1.1",
        "last_seen": 1562600145,
        "mac": "00:00:00:00:01:01",
        "model": "US16P150",
        "name": "Device 1",
        "next_interval": 20,
        "overheating": True,
        "state": 1,
        "type": "usw",
        "upgradable": True,
        "version": "4.0.42.10433",
    }
    options = {
        CONF_ALLOW_BANDWIDTH_SENSORS: True,
        CONF_ALLOW_UPTIME_SENSORS: True,
        CONF_TRACK_CLIENTS: True,
        CONF_TRACK_DEVICES: True,
    }

    config_entry = await setup_unifi_integration(
        hass,
        aioclient_mock,
        options=options,
        clients_response=[client_1, client_2],
        devices_response=[device_1],
    )

    assert await async_setup_component(hass, "config", {})
    await hass.async_block_till_done()

    client = await hass_ws_client(hass)

    # Try to remove an active client from UI: not allowed
    device_entry = device_registry.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, client_1["mac"])}
    )
    await client.send_json(
        {
            "id": 1,
            "type": "config/device_registry/remove_config_entry",
            "config_entry_id": config_entry.entry_id,
            "device_id": device_entry.id,
        }
    )
    response = await client.receive_json()
    assert not response["success"]
    await hass.async_block_till_done()
    assert device_registry.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, client_1["mac"])}
    )

    # Try to remove an active device from UI: not allowed
    device_entry = device_registry.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, device_1["mac"])}
    )
    await client.send_json(
        {
            "id": 2,
            "type": "config/device_registry/remove_config_entry",
            "config_entry_id": config_entry.entry_id,
            "device_id": device_entry.id,
        }
    )
    response = await client.receive_json()
    assert not response["success"]
    await hass.async_block_till_done()
    assert device_registry.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, device_1["mac"])}
    )

    # Remove a client from Unifi API
    mock_unifi_websocket(message=MessageKey.CLIENT_REMOVED, data=[client_2])
    await hass.async_block_till_done()

    # Try to remove an inactive client from UI: allowed
    device_entry = device_registry.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, client_2["mac"])}
    )
    await client.send_json(
        {
            "id": 3,
            "type": "config/device_registry/remove_config_entry",
            "config_entry_id": config_entry.entry_id,
            "device_id": device_entry.id,
        }
    )
    response = await client.receive_json()
    assert response["success"]
    await hass.async_block_till_done()
    assert not device_registry.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, client_2["mac"])}
    )
