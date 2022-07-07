"""The bluetooth integration."""
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
import dataclasses
from enum import Enum
import logging
from typing import Any

from bleak import BleakError, BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

# from homeassistant import config_entries
# from homeassistant.components import websocket_api
# from homeassistant.components.websocket_api.connection import ActiveConnection
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED, EVENT_HOMEASSISTANT_STOP
from homeassistant.core import Event, HomeAssistant, callback as hass_callback
from homeassistant.data_entry_flow import BaseServiceInfo

# from homeassistant.helpers import discovery_flow, system_info
# from homeassistant.helpers.debounce import Debouncer
from homeassistant.helpers.typing import ConfigType
from homeassistant.loader import bind_hass

from .const import DOMAIN

# import voluptuous as vol

# from homeassistant.loader import async_get_bluetooth


_LOGGER = logging.getLogger(__name__)


@dataclasses.dataclass
class BluetoothServiceInfo(BaseServiceInfo):
    """Prepared info from bluetooth entries."""

    name: str
    address: str
    details: Any
    rssi: int
    metadata: Any
    manufacturer_data: dict[int, str]
    service_data: dict[str, bytes]
    service_uuids: list[str]
    platform_data: Any

    @property
    def hci_packet(self):
        """Return the HCI packet for this service."""
        # TODO:
        return "043E%02X0201%02X%02X%02X%02X%02X%02X%02X%02X%02X%*s%02X"

    @classmethod
    def from_advertisement(
        cls, device: BLEDevice, advertisement_data: AdvertisementData
    ) -> BluetoothServiceInfo:
        """Create a BluetoothServiceInfo from an advertisement."""
        return cls(
            name=advertisement_data.local_name or device.name,
            address=device.address,
            details=device.details,
            rssi=device.rssi,
            metadata=device.metadata,
            manufacturer_data=advertisement_data.manufacturer_data,
            service_data=advertisement_data.service_data,
            service_uuids=advertisement_data.service_uuids,
            platform_data=advertisement_data.platform_data,
        )


BluetoothChange = Enum("BluetoothChange", "ADVERTISEMENT")
BluetoothCallback = Callable[[BluetoothServiceInfo, BluetoothChange], Awaitable]


@bind_hass
async def async_register_callback(
    hass: HomeAssistant,
    callback: BluetoothCallback,
    match_dict: None | dict[str, str] = None,
) -> Callable[[], None]:
    """Register to receive a callback on bluetooth change.

    Returns a callback that can be used to cancel the registration.
    """
    manager: BluetoothManager = hass.data[DOMAIN]
    return await manager.async_register_callback(callback, match_dict)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the bluetooth integration."""
    # bt = await async_get_bluetooth(hass)
    bluetooth: list[dict[str, str]] = []
    bluetooth_discovery = BluetoothManager(hass, bluetooth)
    await bluetooth_discovery.async_setup()
    hass.data[DOMAIN] = bluetooth

    # TODO:
    # websocket_api.async_register_command(hass, list_devices)
    # websocket_api.async_register_command(hass, set_devices)

    return True


class BluetoothManager:
    """Manage Bluetooth."""

    def __init__(
        self,
        hass: HomeAssistant,
        bluetooth: list[dict[str, str]],
    ) -> None:
        """Init USB Discovery."""
        self.hass = hass
        self.bluetooth = bluetooth
        self.scanner: BleakScanner | None = None
        self._scan_task: asyncio.Task | None = None
        self._callbacks: list[tuple[BluetoothCallback, dict[str, str]]] = []

    async def async_setup(self) -> None:
        """Set up BT Discovery."""
        self.hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, self.async_start)

    async def _async_start_scanner(self) -> None:
        """Start scanner and wait until canceled."""
        future: asyncio.Future[bool] = asyncio.Future()
        assert self.scanner is not None
        async with self.scanner:
            await future

    @hass_callback
    def async_start(self, event: Event) -> None:
        """Start BT Discovery and run a manual scan."""
        _LOGGER.debug("Starting bluetooth scanner")
        try:
            self.scanner = BleakScanner()
        except BleakError as ex:
            _LOGGER.warning(
                "Could not create bluetooth scanner (is bluetooth present and enabled?): %s",
                ex,
            )
            return
        self.scanner.register_detection_callback(self._device_detected)
        self.hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, self.async_stop)
        self._scan_task = self.hass.async_create_task(self._async_start_scanner())

    @hass_callback
    def _device_detected(
        self, device: BLEDevice, advertisement_data: AdvertisementData
    ) -> None:
        """Handle a detected device."""
        service_info = BluetoothServiceInfo.from_advertisement(
            device, advertisement_data
        )
        _LOGGER.debug("Device detected: %s", service_info)

    async def async_register_callback(
        self, callback: BluetoothCallback, match_dict: None | dict[str, str] = None
    ) -> Callable[[], None]:
        """Register a callback."""
        # if match_dict is None:
        lower_match_dict: dict[str, Any] = {}

        callback_entry = (callback, lower_match_dict)
        self._callbacks.append(callback_entry)

        @hass_callback
        def _async_remove_callback() -> None:
            self._callbacks.remove(callback_entry)

        return _async_remove_callback

    @hass_callback
    def async_stop(self, event: Event) -> None:
        """Stop bluetooth discovery."""
        if self._scan_task:
            self._scan_task.cancel()
            self._scan_task = None
