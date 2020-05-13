"""Config flow for Logitech Squeezebox integration."""
import asyncio
import logging

from pysqueezebox import Server, async_discover
import voluptuous as vol

from homeassistant import config_entries, core, data_entry_flow, exceptions
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
    HTTP_UNAUTHORIZED,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DEFAULT_PORT, DOMAIN

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Optional(CONF_USERNAME): str,
        vol.Optional(CONF_PASSWORD): str,
    }
)

TIMEOUT = 5


async def validate_input(hass: core.HomeAssistant, data):
    """
    Validate the user input allows us to connect.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """
    server = Server(
        async_get_clientsession(hass),
        data[CONF_HOST],
        data[CONF_PORT],
        data.get(CONF_USERNAME),
        data.get(CONF_PASSWORD),
    )

    status = await server.async_query("serverstatus")
    if not status:
        if server.http_status == HTTP_UNAUTHORIZED:
            raise InvalidAuth
        raise CannotConnect

    return status


class SqueezeboxConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Logitech Squeezebox."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self):
        """Initialize an instance of the squeezebox config flow."""
        self.data_schema = DATA_SCHEMA
        self.data = None

    async def async_step_user(self, user_input=None, errors=None):
        """Handle a flow initialized by the user."""
        if user_input is None:
            # display the form
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema({vol.Optional(CONF_HOST): str}),
                errors=errors,
            )
        if CONF_HOST in user_input:
            # update with host provided by user
            self.data_schema = vol.Schema(
                {
                    vol.Required(
                        CONF_HOST,
                        description={"suggested_value": user_input.get(CONF_HOST)},
                    ): str,
                    vol.Required(CONF_PORT, default=DEFAULT_PORT,): int,
                    vol.Optional(CONF_USERNAME): str,
                    vol.Optional(CONF_PASSWORD): str,
                }
            )
            return await self.async_step_edit()

        # no host specified, see if we can discover an unconfigured LMS server
        async def discover():
            """Discover an unconfigured LMS server."""
            self.data = None

            def _discovery_callback(server):
                if server.uuid:
                    for entry in self._async_current_entries():
                        if entry.unique_id == server.uuid:
                            # ignore already configured uuids
                            return
                    self.data = {
                        "host": server.host,
                        "port": server.port,
                        "uuid": server.uuid,
                    }
                    _LOGGER.debug("Discovered server: %s", self.data)

            discovery_task = self.hass.async_create_task(
                async_discover(_discovery_callback)
            )
            while not self.data:
                await asyncio.sleep(1)
            discovery_task.cancel()  # stop searching as soon as we find a server
            return self.data

        try:
            discovery_info = await asyncio.wait_for(discover(), timeout=TIMEOUT)
            # got a new server
            # update with suggested values from discovery
            self.data_schema = vol.Schema(
                {
                    vol.Required(
                        CONF_HOST,
                        description={"suggested_value": discovery_info.get(CONF_HOST)},
                    ): str,
                    vol.Required(
                        CONF_PORT,
                        default=DEFAULT_PORT,
                        description={"suggested_value": discovery_info.get(CONF_PORT)},
                    ): int,
                    vol.Optional(CONF_USERNAME): str,
                    vol.Optional(CONF_PASSWORD): str,
                }
            )
            return await self.async_step_edit()
        except asyncio.TimeoutError:
            return self.async_abort(reason="no_server_found")

    async def async_step_edit(self, user_input=None):
        """Edit a discovered or manually inputted server."""
        errors = {}
        if user_input:
            try:
                info = await validate_input(self.hass, user_input)
                if "uuid" in info:
                    await self.async_set_unique_id(info["uuid"])
                    self._abort_if_unique_id_configured()
                return self.async_create_entry(title=info.get("ip"), data=user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="edit", data_schema=self.data_schema, errors=errors
        )

    async def async_step_import(self, config, errors=None):
        """Import a config flow from configuration."""
        try:
            DATA_SCHEMA(config)
            info = await validate_input(self.hass, config)
            if "uuid" in info:
                await self.async_set_unique_id(info["uuid"])
                self._abort_if_unique_id_configured()
            return self.async_create_entry(title=info.get("ip"), data=config)
        except CannotConnect:
            return self.async_abort(reason="cannot_connect")
        except InvalidAuth:
            return self.async_abort(reason="invalid_auth")
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            return self.async_abort(reason="unknown")

    async def async_step_discovery(self, discovery_info):
        """Handle discovery."""
        _LOGGER.debug("Reached discovery flow with info: %s", discovery_info)
        if "uuid" not in discovery_info:
            DATA_SCHEMA(discovery_info)
            try:
                info = await validate_input(self.hass, discovery_info)
                discovery_info.update(info)
            except CannotConnect:
                return self.async_abort(reason="cannot_connect")
            except InvalidAuth:
                return self.async_abort(reason="invalid_auth")
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                return self.async_abort(reason="unknown")
        if "uuid" in discovery_info:
            try:
                await self.async_set_unique_id(discovery_info["uuid"])
                self._abort_if_unique_id_configured()
            except data_entry_flow.AbortFlow:
                # ignore already discovered servers
                return self.async_abort(reason="already_configured")

            # update schema with suggested values from discovery
            self.data_schema = vol.Schema(
                {
                    vol.Required(
                        CONF_HOST,
                        description={"suggested_value": discovery_info.get(CONF_HOST)},
                    ): str,
                    vol.Required(
                        CONF_PORT,
                        default=DEFAULT_PORT,
                        description={"suggested_value": discovery_info.get(CONF_PORT)},
                    ): int,
                    vol.Optional(CONF_USERNAME): str,
                    vol.Optional(CONF_PASSWORD): str,
                }
            )
            return await self.async_step_edit()


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""
