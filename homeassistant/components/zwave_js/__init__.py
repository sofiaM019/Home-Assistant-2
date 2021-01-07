"""The Z-Wave JS integration."""
import asyncio
import logging

from async_timeout import timeout
from zwave_js_server.client import Client as ZwaveClient
from zwave_js_server.model.node import Node as ZwaveNode

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_URL, EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, PLATFORMS

LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Z-Wave JS component."""
    hass.data[DOMAIN] = {}
    return True


@callback
def register_node_in_dev_reg(
    entry: ConfigEntry,
    dev_reg: device_registry.DeviceRegistry,
    client: ZwaveClient,
    node: ZwaveNode,
) -> None:
    """Register node in dev reg."""
    dev_reg.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, client.driver.controller.home_id, node.node_id)},
        sw_version=node.firmware_version,
        name=node.name,
        model=node.product_type,
        manufacturer=str(node.manufacturer_id),
    )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Z-Wave JS from a config entry."""
    client = ZwaveClient(entry.data[CONF_URL], async_get_clientsession(hass))
    initialized = asyncio.Event()

    async def async_on_initialized():
        """Handle initial full state received."""
        # TODO: signal entities to update availability state
        LOGGER.info("Connection to Zwave JS Server initialized")
        initialized.set()

        # This should be moved to the Node Ready command or something
        # And then listen to new nodes too.
        dev_reg = await device_registry.async_get_registry(hass)
        for node in client.driver.controller.nodes.values():
            register_node_in_dev_reg(entry, dev_reg, client, node)

    async def async_on_disconnect():
        """Handle websocket is disconnected."""
        LOGGER.info("Disconnected from Zwave JS Server")
        # TODO: signal entities to update availability state

    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )

    # register main event callbacks.
    unsubs = [
        client.register_on_initialized(async_on_initialized),
        client.register_on_disconnect(async_on_disconnect),
    ]

    asyncio.create_task(client.connect())

    try:
        async with timeout(10):
            await initialized.wait()
    except asyncio.TimeoutError as err:
        for unsub in unsubs:
            unsub()
        await client.disconnect()
        raise ConfigEntryNotReady from err

    async def handle_ha_shutdown(event):
        """Handle HA shutdown."""
        await client.disconnect()

    unsubs.append(hass.bus.async_listen(EVENT_HOMEASSISTANT_STOP, handle_ha_shutdown))

    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "unsubs": unsubs,
    }

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )
    if not unload_ok:
        return False

    info = hass.data[DOMAIN].pop(entry.entry_id)

    for unsub in info["unsubs"]:
        unsub()

    await info["client"].disconnect()

    return True
