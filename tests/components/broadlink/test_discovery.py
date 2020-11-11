"""Tests for device discovery."""
import socket

from homeassistant.components.broadlink.const import DOMAIN

from . import get_device

from tests.async_mock import patch


async def test_new_devices_discovered(hass):
    """Test we create flows for new devices discovered."""
    device = get_device("Office")
    devices = ["Entrance", "Bedroom", "Living Room", "Office"]
    mock_apis = [get_device(device).get_mock_api() for device in devices]
    results = {"192.168.0.255": mock_apis}

    with patch.object(hass.config_entries.flow, "async_init") as mock_init:
        *_, mock_discovery = await device.setup_entry(hass, mock_discovery=results)

    assert mock_discovery.call_count == 1
    assert mock_init.call_count == len(devices) - 1


async def test_setup_new_devices_discovered_mult_netifs(hass):
    """Test we create config flows for new devices discovered in multiple networks."""
    device = get_device("Office")
    devices_a = ["Entrance", "Bedroom", "Living Room", "Office"]
    devices_b = ["Garden", "Rooftop"]
    mock_apis_a = [get_device(device).get_mock_api() for device in devices_a]
    mock_apis_b = [get_device(device).get_mock_api() for device in devices_b]
    results = {"192.168.0.255": mock_apis_a, "192.168.1.255": mock_apis_b}

    with patch.object(hass.config_entries.flow, "async_init") as mock_init:
        *_, mock_discovery = await device.setup_entry(hass, mock_discovery=results)

    assert mock_discovery.call_count == 2
    assert mock_init.call_count == len(devices_a) + len(devices_b) - 1


async def test_setup_no_devices_discovered(hass):
    """Test we do not create flows if no devices are discovered."""
    device = get_device("Office")
    results = {"192.168.0.255": []}

    with patch.object(hass.config_entries.flow, "async_init") as mock_init:
        *_, mock_discovery = await device.setup_entry(hass, mock_discovery=results)

    assert mock_discovery.call_count == 1
    assert mock_init.call_count == 0


async def test_setup_discover_already_known_host(hass):
    """Test we do not create flows when known devices are discovered."""
    device_a = get_device("Living Room")
    mock_entry = device_a.get_mock_entry()
    mock_entry.add_to_hass(hass)

    device_b = get_device("Bedroom")
    results = {"192.168.0.255": [device_a.get_mock_api(), device_b.get_mock_api()]}

    with patch.object(hass.config_entries.flow, "async_init") as mock_init:
        *_, mock_discovery = await device_b.setup_entry(hass, mock_discovery=results)

    assert mock_discovery.call_count == 1
    assert mock_init.call_count == 0


async def test_setup_discover_update_ip_address(hass):
    """Test we update the entry when a known device is discovered with a different IP address."""
    device = get_device("Living Room")

    _, mock_entry, _ = await device.setup_entry(hass)

    previous_host = device.host
    device.host = "192.168.1.128"

    with device.patch_setup(), patch(
        "homeassistant.components.broadlink.helpers.socket.gethostbyname",
        return_value=previous_host,
    ) as mock_host:
        await hass.data[DOMAIN].discovery.coordinator.async_refresh()
        await hass.async_block_till_done()

    assert mock_host.call_count == 1
    assert mock_entry.data["host"] == device.host


async def test_setup_discover_update_hostname(hass):
    """Test we update the entry when the hostname is no longer valid."""
    device = get_device("Living Room")
    results = {"192.168.0.255": [device.get_mock_api()]}
    device.host = "invalidhostname"

    _, mock_entry, _ = await device.setup_entry(hass, mock_discovery=results)

    device.host = "192.168.1.128"

    with device.patch_setup(), patch(
        "homeassistant.components.broadlink.helpers.socket.gethostbyname",
        side_effect=OSError(socket.EAI_NONAME, None),
    ) as mock_host:
        await hass.data[DOMAIN].discovery.coordinator.async_refresh()
        await hass.async_block_till_done()

    assert mock_host.call_count == 1
    assert mock_entry.data["host"] == device.host


async def test_setup_discover_do_not_change_hostname(hass):
    """Test we do not update the entry if the hostname routes to the device."""
    device = get_device("Living Room")
    results = {"192.168.0.255": [device.get_mock_api()]}
    device.host = "somethingthatworks"

    _, mock_entry, _ = await device.setup_entry(hass, mock_discovery=results)

    with device.patch_setup(mock_discovery=results), patch(
        "homeassistant.components.broadlink.helpers.socket.gethostbyname",
        return_value=device.host,
    ) as mock_host:
        await hass.data[DOMAIN].discovery.coordinator.async_refresh()
        await hass.async_block_till_done()

    assert mock_host.call_count == 1
    assert mock_entry.data["host"] == "somethingthatworks"
