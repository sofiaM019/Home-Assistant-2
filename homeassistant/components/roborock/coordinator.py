"""Roborock Coordinator."""
from __future__ import annotations

from datetime import timedelta
import logging

from roborock.code_mappings import ModelSpecification
from roborock.containers import (
    HomeDataDevice,
    HomeDataProduct,
    NetworkInfo,
    RoborockDeviceInfo,
)
from roborock.exceptions import RoborockException
from roborock.local_api import RoborockLocalClient
from roborock.roborock_typing import DeviceProp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN
from .models import RoborockHassDeviceInfo

SCAN_INTERVAL = timedelta(seconds=30)

_LOGGER = logging.getLogger(__name__)


class RoborockDataUpdateCoordinator(DataUpdateCoordinator[DeviceProp]):
    """Class to manage fetching data from the API."""

    def __init__(
        self,
        hass: HomeAssistant,
        device: HomeDataDevice,
        device_networking: NetworkInfo,
        product_info: HomeDataProduct,
        model_specification: ModelSpecification,
    ) -> None:
        """Initialize."""
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)
        self.device_info = RoborockHassDeviceInfo(
            device,
            device_networking,
            product_info,
            DeviceProp(),
            model_specification,
        )
        device_info = RoborockDeviceInfo(device, model_specification)
        self.api = RoborockLocalClient(device_info, device_networking.ip)

    async def release(self) -> None:
        """Disconnect from API."""
        await self.api.async_disconnect()

    async def _update_device_prop(self) -> None:
        """Update device properties."""
        device_prop = await self.api.get_prop()
        if device_prop:
            if self.device_info.props:
                self.device_info.props.update(device_prop)
            else:
                self.device_info.props = device_prop

    async def _async_update_data(self) -> DeviceProp:
        """Update data via library."""
        try:
            await self._update_device_prop()
        except RoborockException as ex:
            raise UpdateFailed(ex) from ex
        return self.device_info.props
