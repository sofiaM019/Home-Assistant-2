"""Tests for the Device Registry."""
import asyncio

from unittest.mock import patch

import pytest

from homeassistant.helpers import device_registry


def mock_registry(hass, mock_entries=None):
    """Mock the Device Registry."""
    registry = device_registry.DeviceRegistry(hass)
    registry.devices = mock_entries or []

    async def _get_reg():
        return registry

    hass.data[device_registry.DATA_REGISTRY] = \
        hass.loop.create_task(_get_reg())
    return registry


@pytest.fixture
def registry(hass):
    """Return an empty, loaded, registry."""
    return mock_registry(hass)


async def test_get_or_create_returns_same_entry(registry):
    """Make sure we do not duplicate entries."""
    entry = registry.async_get_or_create(
        [['bridgeid', '0123']], 'Dresden Elektronik', 'Conbee',
        [['Ethernet', '1.0.0.0']])
    entry2 = registry.async_get_or_create(
        [['bridgeid', '0123']], 'Dresden Elektronik', 'Conbee',
        [['Ethernet', '1.0.0.0']])
    entry3 = registry.async_get_or_create(
        [['bridgeid', '1234']], 'Dresden Elektronik', 'Conbee',
        [['Ethernet', '1.0.0.0']])

    assert len(registry.devices) == 1
    assert entry is entry2
    assert entry is entry3
    assert entry.identifiers == [['bridgeid', '0123']]


async def test_loading_from_storage(hass, hass_storage):
    """Test loading stored devices on start."""
    hass_storage[device_registry.STORAGE_KEY] = {
        'version': device_registry.STORAGE_VERSION,
        'data': {
            'devices': [
                {
                    'connection': [
                        [
                            'Zigbee',
                            '01.23.45.67.89'
                        ]
                    ],
                    'id': 'abcdefghijklm',
                    'identifiers': [
                        [
                            'serial',
                            '12:34:56:78:90:AB:CD:EF'
                        ]
                    ],
                    'manufacturer': 'manufacturer name',
                    'model': 'brand new',
                    'name': 'wireless sensor',
                    'sw_version': 'V1'
                }
            ]
        }
    }

    registry = await device_registry.async_get_registry(hass)

    entry = registry.async_get_or_create(
        [['serial', '12:34:56:78:90:AB:CD:EF']], 'manufacturer name',
        'brand new', [['Zigbee', '01.23.45.67.89']])
    assert entry.id == 'abcdefghijklm'
