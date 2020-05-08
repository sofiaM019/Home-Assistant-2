"""Base class for UniFi clients."""

import logging

from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC

from .unifi_entity_base import UniFiBase

LOGGER = logging.getLogger(__name__)


class UniFiClient(UniFiBase):
    """Base class for UniFi clients."""

    def __init__(self, client, controller) -> None:
        """Set up client."""
        super().__init__(client, controller)

        self._is_wired = client.mac not in controller.wireless_clients

    @property
    def client(self):
        """Wrap item."""
        return self._item

    @property
    def mac(self):
        """Return MAC of client."""
        return self.client.mac

    @property
    def is_wired(self):
        """Return if the client is wired.

        Allows disabling logic to keep track of clients affected by UniFi wired bug marking wireless devices as wired. This is useful when running a network not only containing UniFi APs.
        """
        if self._is_wired and self.client.mac in self.controller.wireless_clients:
            self._is_wired = False

        if self.controller.option_ignore_wired_bug:
            return self.client.is_wired
        return self._is_wired

    @property
    def unique_id(self):
        """Return a unique identifier for this switch."""
        return f"{self.TYPE}-{self.client.mac}"

    @property
    def name(self) -> str:
        """Return the name of the client."""
        return self.client.name or self.client.hostname

    @property
    def available(self) -> bool:
        """Return if controller is available."""
        return self.controller.available

    @property
    def device_info(self) -> dict:
        """Return a client description for device registry."""
        return {"connections": {(CONNECTION_NETWORK_MAC, self.client.mac)}}
