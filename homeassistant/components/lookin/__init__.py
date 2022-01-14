"""The lookin integration."""
from __future__ import annotations

import asyncio
from collections.abc import Callable, Coroutine
from datetime import timedelta
import logging
from typing import Any

import aiohttp
from aiolookin import (
    LookInHttpProtocol,
    LookinUDPSubscriptions,
    MeteoSensor,
    Remote,
    start_lookin_udp,
)
from aiolookin.models import UDPCommandType, UDPEvent

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, PLATFORMS, TYPE_TO_PLATFORM
from .models import LookinData

LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up lookin from a config entry."""

    host = entry.data[CONF_HOST]
    lookin_protocol = LookInHttpProtocol(
        api_uri=f"http://{host}", session=async_get_clientsession(hass)
    )

    try:
        lookin_device = await lookin_protocol.get_info()
        devices = await lookin_protocol.get_devices()
    except (asyncio.TimeoutError, aiohttp.ClientError) as ex:
        raise ConfigEntryNotReady from ex

    meteo_coordinator: DataUpdateCoordinator = DataUpdateCoordinator(
        hass,
        LOGGER,
        name=entry.title,
        update_method=lookin_protocol.get_meteo_sensor,
        update_interval=timedelta(
            minutes=5
        ),  # Updates are pushed (fallback is polling)
    )
    await meteo_coordinator.async_config_entry_first_refresh()

    device_coordinators: dict[str, DataUpdateCoordinator] = {}
    for remote in devices:
        if remote["Type"] not in TYPE_TO_PLATFORM:
            continue
        uuid = remote["UUID"]

        def _wrap_async_update(
            uuid: str,
        ) -> Callable[[], Coroutine[None, Any, Remote]]:
            """Create a function to capture the uuid cell variable."""

            async def _async_update() -> Remote:
                return await lookin_protocol.get_remote(uuid)

            return _async_update

        coordinator = DataUpdateCoordinator(
            hass,
            LOGGER,
            name=f"{entry.title} {uuid}",
            update_method=_wrap_async_update(uuid),
            update_interval=timedelta(
                seconds=60
            ),  # Updates are pushed (fallback is polling)
        )
        await coordinator.async_config_entry_first_refresh()
        device_coordinators[uuid] = coordinator

    @callback
    def _async_meteo_push_update(event: UDPEvent) -> None:
        """Process an update pushed via UDP."""
        LOGGER.debug("Processing push message for meteo sensor: %s", event)
        meteo: MeteoSensor = meteo_coordinator.data
        meteo.update_from_value(event.value)
        meteo_coordinator.async_set_updated_data(meteo)

    lookin_udp_subs = LookinUDPSubscriptions()
    entry.async_on_unload(
        lookin_udp_subs.subscribe_event(
            lookin_device.id, UDPCommandType.meteo, None, _async_meteo_push_update
        )
    )

    entry.async_on_unload(await start_lookin_udp(lookin_udp_subs, lookin_device.id))

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = LookinData(
        lookin_udp_subs=lookin_udp_subs,
        lookin_device=lookin_device,
        meteo_coordinator=meteo_coordinator,
        devices=devices,
        lookin_protocol=lookin_protocol,
        device_coordinators=device_coordinators,
    )

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
