"""iAlarm integration."""
import asyncio
import logging

from async_timeout import timeout
from pyialarm import IAlarm

from homeassistant.components.alarm_control_panel import SCAN_INTERVAL
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DATA_COORDINATOR, DOMAIN, IALARM_TO_HASS

PLATFORMS = ["alarm_control_panel"]
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up iAlarm config."""
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
    ialarm = IAlarm(host, port)

    try:
        async with timeout(10):
            mac = await hass.async_add_executor_job(ialarm.get_mac)
    except (asyncio.TimeoutError, ConnectionError) as ex:
        raise ConfigEntryNotReady from ex

    coordinator = IAlarmDataUpdateCoordinator(hass, ialarm, mac)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})

    hass.data[DOMAIN][entry.entry_id] = {
        DATA_COORDINATOR: coordinator,
    }

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload iAlarm config."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


class IAlarmDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching iAlarm data."""

    def __init__(self, hass, ialarm, mac):
        """Initialize global iAlarm data updater."""
        self.ialarm = ialarm
        self.state = None
        self.host = ialarm.host
        self.mac = mac

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )

    def _update_data(self) -> None:
        """Fetch data from iAlarm via sync functions."""
        status = self.ialarm.get_status()
        _LOGGER.debug("iAlarm status: %s", status)

        self.state = IALARM_TO_HASS.get(status)

    async def _async_update_data(self) -> None:
        """Fetch data from iAlarm."""
        try:
            async with timeout(10):
                await self.hass.async_add_executor_job(self._update_data)
        except ConnectionError as error:
            raise UpdateFailed(error) from error
