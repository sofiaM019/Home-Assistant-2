""""Config flow for Lupusec integration."""

import ipaddress
import logging
import socket

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(CONF_NAME): str,
    }
)


class LupusecConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Lupusec config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle a flow initiated by the user."""
        errors = {}

        if user_input is not None:
            host = user_input.get(CONF_HOST)
            username = user_input.get(CONF_USERNAME)
            password = user_input.get(CONF_PASSWORD)
            name = user_input.get(CONF_NAME)

            errors = await validate_configuration(host, username, password, name)

            if not errors:
                return self.async_create_entry(
                    title=host,
                    data={
                        CONF_HOST: host,
                        CONF_USERNAME: username,
                        CONF_PASSWORD: password,
                        CONF_NAME: name,
                    },
                )

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )


async def validate_configuration(host, username, password, name):
    """Validate the provided configuration."""
    errors = {}

    if not is_valid_host(host):
        errors[CONF_HOST] = "invalid_host"

    return errors


def is_valid_host(host):
    """Check if the provided value is a valid DNS name or IP address."""
    try:
        # Try to parse the host as an IP address
        ipaddress.ip_address(host)
        return True
    except ValueError:
        # If parsing as an IP address fails, try as a DNS name
        try:
            ipaddress.ip_address(socket.gethostbyname(host))
            return True
        except (socket.herror, ValueError, socket.gaierror):
            return False


async def validate_update_interval(update_interval):
    """Validate the provided update_interval."""
    # Return True if the update_interval is valid, False otherwise
    return True
