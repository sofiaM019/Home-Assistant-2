"""Support for VELUX KLF 200 devices."""
import asyncio
import logging
from typing import Any, Optional

from pyvlx import OpeningDevice, PyVLX, PyVLXException
import voluptuous as vol

from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    EVENT_HOMEASSISTANT_STOP,
    Platform,
)
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers import discovery
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.typing import ConfigType

DOMAIN = "velux"
DATA_VELUX = "data_velux"
PLATFORMS = [Platform.COVER, Platform.LIGHT, Platform.SCENE]
_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {vol.Required(CONF_HOST): cv.string, vol.Required(CONF_PASSWORD): cv.string}
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the velux component."""
    try:
        hass.data[DATA_VELUX] = VeluxModule(hass, config[DOMAIN])
        hass.data[DATA_VELUX].setup()
        await hass.data[DATA_VELUX].async_start()

    except PyVLXException as ex:
        _LOGGER.exception("Can't connect to velux interface: %s", ex)
        return False

    for platform in PLATFORMS:
        hass.async_create_task(
            discovery.async_load_platform(hass, platform, DOMAIN, {}, config)
        )
    return True


class DelayVelux(PyVLX):
    """PyVLX, but with delays to workaround KLF 200 issues."""

    def __init__(self, *args, **kwargs):
        """Initialize DelayVelux class."""
        super().__init__(*args, **kwargs)
        self.__send_lock = asyncio.Lock()

    async def send_frame(self, frame):
        """Send frame to API via connection."""
        async with self.__send_lock:
            await asyncio.sleep(1)
        # Note we explicitly don't do the send_frame in the lock, as sometimes
        # this seems to fail to return, particularly at startup
        await super().send_frame(frame)


class VeluxModule:
    """Abstraction for velux component."""

    def __init__(self, hass: HomeAssistant, domain_config: dict[str, Any]) -> None:
        """Initialize for velux component."""
        self.pyvlx: Optional[DelayVelux] = None
        self._hass = hass
        self._domain_config = domain_config

    def setup(self):
        """Velux component setup."""

        async def on_hass_stop(event):
            """Close connection when hass stops."""
            _LOGGER.debug("Velux interface terminated")
            await self.pyvlx.disconnect()

        async def async_reboot_gateway(service_call: ServiceCall) -> None:
            assert self.pyvlx is not None
            await self.pyvlx.reboot_gateway()

        self._hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, on_hass_stop)
        host = self._domain_config.get(CONF_HOST)
        password = self._domain_config.get(CONF_PASSWORD)
        self.pyvlx = DelayVelux(host=host, password=password)

        self._hass.services.async_register(
            DOMAIN, "reboot_gateway", async_reboot_gateway
        )

    async def async_start(self):
        """Start velux component."""
        _LOGGER.debug("Velux interface started")
        await self.pyvlx.load_scenes()
        await self.pyvlx.load_nodes()


class VeluxEntity(Entity):
    """Abstraction for al Velux entities."""

    _attr_should_poll = False

    def __init__(self, node: OpeningDevice) -> None:
        """Initialize the Velux device."""
        self.node = node
        self._attr_unique_id = node.serial_number
        self._attr_name = node.name if node.name else f"#{node.node_id}"

    @callback
    def async_register_callbacks(self):
        """Register callbacks to update hass after device was changed."""

        async def after_update_callback(device):
            """Call after device was updated."""
            self.async_write_ha_state()

        self.node.register_device_updated_cb(after_update_callback)

    async def async_added_to_hass(self):
        """Store register state change callback."""
        self.async_register_callbacks()
