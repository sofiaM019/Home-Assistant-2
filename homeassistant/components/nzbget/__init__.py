"""The NZBGet integration."""
import asyncio
from datetime import timedelta
import logging

from async_timeout import timeout
from pynzbgetapi import NZBGetAPI, NZBGetAPIException
import voluptuous as vol

from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_SSL,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
)
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.typing import HomeAssistantType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    ATTR_SPEED,
    DATA_COORDINATOR,
    DATA_UNDO_UPDATE_LISTENER,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SPEED_LIMIT,
    DEFAULT_SSL,
    DOMAIN,
    SERVICE_PAUSE,
    SERVICE_RESUME,
    SERVICE_SET_SPEED,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_HOST): cv.string,
                vol.Optional(CONF_PASSWORD): cv.string,
                vol.Optional(CONF_USERNAME): cv.string,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                ): cv.time_period,
                vol.Optional(CONF_SSL, default=DEFAULT_SSL): cv.boolean,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

SPEED_LIMIT_SCHEMA = vol.Schema(
    {vol.Optional(ATTR_SPEED, default=DEFAULT_SPEED_LIMIT): cv.positive_int}
)


async def async_setup(hass: HomeAssistantType, config: dict) -> bool:
    """Set up the NZBGet integration."""
    hass.data.setdefault(DOMAIN, {})

    if hass.config_entries.async_entries(DOMAIN):
        return True

    if DOMAIN in config:
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN, context={"source": SOURCE_IMPORT}, data=config[DOMAIN],
            )
        )

    return True


async def async_setup_entry(hass: HomeAssistantType, entry: ConfigEntry) -> bool:
    """Set up NZBGet from a config entry."""
    if not entry.options:
        options = {
            CONF_SCAN_INTERVAL: entry.data.get(
                CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
            ),
        }
        hass.config_entries.async_update_entry(entry, options=options)

    coordinator = NZBGetDataUpdateCoordinator(
        hass, config=entry.data, options=entry.options,
    )

    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    undo_listener = entry.add_update_listener(_async_update_listener)

    hass.data[DOMAIN][entry.entry_id] = {
        DATA_COORDINATOR: coordinator,
        DATA_UNDO_UPDATE_LISTENER: undo_listener,
    }

    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )

    def pause(call) -> None:
        """Service call to pause downloads in NZBGet."""
        coordinator.nzbget.pausedownload()

    def resume(call) -> None:
        """Service call to resume downloads in NZBGet."""
        coordinator.nzbget.resumedownload()

    def set_speed(call) -> None:
        """Service call to rate limit speeds in NZBGet."""
        coordinator.nzbget.rate(call.data[ATTR_SPEED])

    hass.services.async_register(DOMAIN, SERVICE_PAUSE, pause, schema=vol.Schema({}))

    hass.services.async_register(DOMAIN, SERVICE_RESUME, resume, schema=vol.Schema({}))

    hass.services.async_register(
        DOMAIN, SERVICE_SET_SPEED, set_speed, schema=SPEED_LIMIT_SCHEMA
    )

    return True


async def async_unload_entry(hass: HomeAssistantType, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )

    if unload_ok:
        hass.data[DOMAIN][entry.entry_id][DATA_UNDO_UPDATE_LISTENER]()
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


def _async_register_services(
    hass: HomeAssistantType,
    coordinator:NZBGetDataUpdateCoordinator,
) -> None:
    """Register integration-level services."""

    def pause(call) -> None:
        """Service call to pause downloads in NZBGet."""
        coordinator.nzbget.pausedownload()

    def resume(call) -> None:
        """Service call to resume downloads in NZBGet."""
        coordinator.nzbget.resumedownload()

    def set_speed(call) -> None:
        """Service call to rate limit speeds in NZBGet."""
        coordinator.nzbget.rate(call.data[ATTR_SPEED])

    hass.services.async_register(DOMAIN, SERVICE_PAUSE, pause, schema=vol.Schema({}))
    hass.services.async_register(DOMAIN, SERVICE_RESUME, resume, schema=vol.Schema({}))
    hass.services.async_register(
        DOMAIN, SERVICE_SET_SPEED, set_speed, schema=SPEED_LIMIT_SCHEMA
    )


async def _async_update_listener(hass: HomeAssistantType, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


class NZBGetDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching NZBGet data."""

    def __init__(self, hass: HomeAssistantType, *, config: dict, options: dict):
        """Initialize global NZBGet data updater."""
        self.nzbget = NZBGetAPI(
            config[CONF_HOST],
            config[CONF_USERNAME] if config[CONF_USERNAME] != "" else None,
            config[CONF_PASSWORD] if config[CONF_PASSWORD] != "" else None,
            config[CONF_SSL],
            config[CONF_VERIFY_SSL],
            config[CONF_PORT],
        )

        self._completed_downloads_init = False
        self._completed_downloads = {}

        update_interval = timedelta(seconds=options[CONF_SCAN_INTERVAL])

        super().__init__(
            hass, _LOGGER, name=DOMAIN, update_interval=update_interval,
        )

    def _check_completed_downloads(self, history):
        """Check history for newly completed downloads."""
        actual_completed_downloads = {
            (x["Name"], x["Category"], x["Status"]) for x in history
        }

        if self._completed_downloads_init:
            tmp_completed_downloads = list(
                actual_completed_downloads.difference(self._completed_downloads)
            )

            for download in tmp_completed_downloads:
                self.hass.bus.fire(
                    "nzbget_download_complete",
                    {
                        "name": download[0],
                        "category": download[1],
                        "status": download[2],
                    },
                )

        self._completed_downloads = actual_completed_downloads
        self._completed_downloads_init = True

    async def _async_update_data(self) -> dict:
        """Fetch data from NZBGet."""

        def _update_data() -> dict:
            """Fetch data from NZBGet via sync functions."""
            status = self.nzbget.status()
            history = self.nzbget.history()

            self._check_completed_downloads(history)

            return {
                "status": status,
                "downloads": history,
            }

        try:
            async with timeout(4):
                return await self.hass.async_add_executor_job(_update_data)
        except NZBGetAPIException as error:
            raise UpdateFailed(f"Invalid response from API: {error}")


class NZBGetEntity(Entity):
    """Defines a base NZBGet entity."""

    def __init__(
        self, *, entry_id: str, name: str, coordinator: NZBGetDataUpdateCoordinator
    ) -> None:
        """Initialize the NZBGet entity."""
        self._name = name
        self._entry_id = entry_id
        self.coordinator = coordinator

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name

    @property
    def should_poll(self) -> bool:
        """Return the polling requirement of the entity."""
        return False

    async def async_added_to_hass(self) -> None:
        """Connect to dispatcher listening for entity data notifications."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

    async def async_update(self) -> None:
        """Request an update from the coordinator of this entity."""
        await self.coordinator.async_request_refresh()
