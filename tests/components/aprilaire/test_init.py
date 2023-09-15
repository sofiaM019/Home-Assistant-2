"""Tests for the Aprilaire integration setup."""

from collections.abc import Awaitable, Callable
import logging
from unittest.mock import AsyncMock, Mock, patch

from pyaprilaire.client import AprilaireClient
import pytest

from homeassistant.components.aprilaire import async_setup_entry, async_unload_entry
from homeassistant.components.aprilaire.const import DOMAIN
from homeassistant.components.aprilaire.coordinator import AprilaireCoordinator
from homeassistant.config_entries import ConfigEntries, ConfigEntry
from homeassistant.core import EventBus, HomeAssistant
from homeassistant.util import uuid as uuid_util


@pytest.fixture
def logger() -> logging.Logger:
    """Return a logger."""
    logger = logging.getLogger(__name__)
    logger.propagate = False

    return logger


@pytest.fixture
def unique_id() -> str:
    """Return a random ID."""
    return uuid_util.random_uuid_hex()


@pytest.fixture
def hass() -> HomeAssistant:
    """Return a mock HomeAssistant instance."""

    hass_mock = AsyncMock(HomeAssistant)
    hass_mock.data = {}
    hass_mock.config_entries = AsyncMock(ConfigEntries)
    hass_mock.bus = AsyncMock(EventBus)

    return hass_mock


@pytest.fixture
def config_entry(unique_id: str) -> ConfigEntry:
    """Return a mock config entry."""

    config_entry_mock = AsyncMock(ConfigEntry)
    config_entry_mock.data = {"host": "test123", "port": 123}
    config_entry_mock.unique_id = unique_id

    return config_entry_mock


@pytest.fixture
def client() -> AprilaireClient:
    """Return a mock client."""
    return AsyncMock(AprilaireClient)


async def test_async_setup_entry(
    client: AprilaireClient,
    config_entry: ConfigEntry,
    unique_id: str,
    hass: HomeAssistant,
    logger: logging.Logger,
) -> None:
    """Test handling of setup with missing MAC address."""

    with patch(
        "pyaprilaire.client.AprilaireClient",
        return_value=client,
    ):
        setup_result = await async_setup_entry(hass, config_entry)

    assert setup_result is True

    client.start_listen.assert_called_once()

    assert isinstance(hass.data[DOMAIN][unique_id], AprilaireCoordinator)


async def test_async_setup_entry_ready(
    client: AprilaireClient,
    config_entry: ConfigEntry,
    hass: HomeAssistant,
    logger: logging.Logger,
) -> None:
    """Test setup entry with valid data."""

    async def wait_for_ready(self, ready_callback: Callable[[bool], Awaitable[None]]):
        await ready_callback(True)

    with patch(
        "pyaprilaire.client.AprilaireClient",
        return_value=client,
    ), patch(
        "homeassistant.components.aprilaire.coordinator.AprilaireCoordinator.wait_for_ready",
        new=wait_for_ready,
    ):
        setup_result = await async_setup_entry(hass, config_entry)

    assert setup_result is True


async def test_async_setup_entry_not_ready(
    client: AprilaireClient,
    config_entry: ConfigEntry,
    hass: HomeAssistant,
    logger: logging.Logger,
) -> None:
    """Test handling of setup when client is not ready."""

    async def wait_for_ready(self, ready_callback: Callable[[bool], Awaitable[None]]):
        await ready_callback(False)

    with patch(
        "pyaprilaire.client.AprilaireClient",
        return_value=client,
    ), patch(
        "homeassistant.components.aprilaire.coordinator.AprilaireCoordinator.wait_for_ready",
        new=wait_for_ready,
    ):
        setup_result = await async_setup_entry(hass, config_entry)

    assert setup_result is True

    client.stop_listen.assert_called_once()


async def test_unload_entry_ok(
    client: AprilaireClient,
    config_entry: ConfigEntry,
    hass: HomeAssistant,
    logger: logging.Logger,
) -> None:
    """Test unloading the config entry."""

    async def wait_for_ready(self, ready_callback: Callable[[bool], Awaitable[None]]):
        await ready_callback(True)

    stop_listen_mock = Mock()

    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)

    with patch(
        "pyaprilaire.client.AprilaireClient",
        return_value=client,
    ), patch(
        "homeassistant.components.aprilaire.coordinator.AprilaireCoordinator.wait_for_ready",
        new=wait_for_ready,
    ), patch(
        "homeassistant.components.aprilaire.coordinator.AprilaireCoordinator.stop_listen",
        new=stop_listen_mock,
    ):
        await async_setup_entry(hass, config_entry)

        unload_result = await async_unload_entry(hass, config_entry)

    hass.config_entries.async_unload_platforms.assert_called_once()

    assert unload_result is True

    stop_listen_mock.assert_called_once()


async def test_unload_entry_not_ok(
    client: AprilaireClient,
    config_entry: ConfigEntry,
    hass: HomeAssistant,
    logger: logging.Logger,
) -> None:
    """Test handling of unload failure."""

    async def wait_for_ready(self, ready_callback: Callable[[bool], Awaitable[None]]):
        await ready_callback(True)

    with patch(
        "pyaprilaire.client.AprilaireClient",
        return_value=client,
    ), patch(
        "homeassistant.components.aprilaire.coordinator.AprilaireCoordinator.wait_for_ready",
        new=wait_for_ready,
    ):
        await async_setup_entry(hass, config_entry)

    hass.config_entries.async_unload_platforms = AsyncMock(return_value=False)

    unload_result = await async_unload_entry(hass, config_entry)

    hass.config_entries.async_unload_platforms.assert_called_once()

    assert unload_result is False
