"""Datacoordinator for InComfort integration."""

from dataclasses import dataclass, field
from datetime import timedelta
import logging
from typing import Any

from aiohttp import ClientResponseError
from incomfortclient import (
    Gateway as InComfortGateway,
    Heater as InComfortHeater,
    IncomfortError,
)

from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.util.hass_dict import HassKey

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = 30


@dataclass
class InComfortData:
    """Keep the Intergas InComfort entry data."""

    client: InComfortGateway
    heaters: list[InComfortHeater] = field(default_factory=list)


async def async_connect_gateway(
    hass: HomeAssistant,
    entry_data: dict[str, Any],
) -> InComfortData:
    """Validate the configuration."""
    credentials = dict(entry_data)
    hostname = credentials.pop(CONF_HOST)

    client = InComfortGateway(
        hostname, **credentials, session=async_get_clientsession(hass)
    )
    heaters = await client.heaters()

    return InComfortData(client=client, heaters=heaters)


class InComfortDataCoordinator(DataUpdateCoordinator[InComfortData]):
    """Data coordinator for InComfort entities."""

    def __init__(self, hass: HomeAssistant, incomfort_data: InComfortData) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="InComfort datacoordinator",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )
        self.incomfort_data = incomfort_data

    async def _async_update_data(self) -> InComfortData:
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            for heater in self.incomfort_data.heaters:
                await heater.update()
        except TimeoutError as exc:
            raise UpdateFailed from exc
        except IncomfortError as exc:
            if isinstance(exc.message, ClientResponseError):
                if exc.message.status == 401:
                    raise ConfigEntryAuthFailed("Incorrect credentials") from exc
            raise UpdateFailed from exc
        return self.incomfort_data


DATA_INCOMFORT: HassKey[dict[str, InComfortDataCoordinator]] = HassKey(DOMAIN)


class IncomfortEntity(CoordinatorEntity[InComfortDataCoordinator]):
    """Base class for all InComfort entities."""

    _attr_should_poll = False
    _attr_has_entity_name = True
