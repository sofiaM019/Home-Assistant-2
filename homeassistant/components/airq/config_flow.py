"""Config flow for air-Q integration.

Off all integration components, the content of this file is being executed first
when the user sets up the integration.
"""
from __future__ import annotations

import logging
from typing import Any

from aioairq import AirQ
from aiohttp.client_exceptions import ClientConnectionError
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import (
    CONF_INTERVAL_SEC,
    CONF_IP_ADDRESS,
    CONF_SECRET,
    CONF_SHOW_AVG,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_IP_ADDRESS): str,
        vol.Required(CONF_SECRET): str,
    }
)
STEP_CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_INTERVAL_SEC, default=2): vol.All(
            int, vol.Range(min=2, min_included=True)
        ),
        vol.Required(CONF_SHOW_AVG, default=True): bool,
    }
)


async def validate_input(_: HomeAssistant, data: dict[str, Any]) -> tuple[str, str]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """

    airq = AirQ(data[CONF_IP_ADDRESS], data[CONF_SECRET])

    try:
        auth_success = await airq.test_authentication()
    except ClientConnectionError as exc:
        raise CannotConnect from exc

    if not auth_success:
        raise InvalidAuth

    config = await airq.get("config")
    device_id: str = config["id"]
    device_name: str = config["devicename"]
    return device_name, device_id


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for air-Q."""

    VERSION = 1
    _title: str = "Air-Q "
    _data: dict[str, str | int | bool] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial configuration step: authentication.

        This prompts the user to enter the credentials to access the device.
        It then tries to connect to the device, and to assess the validity
        of the password.

        If authentication is successful, next step handles minimal configuration
        for the integration.
        """
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        try:
            device_name, device_id = await validate_input(self.hass, user_input)
        except CannotConnect:
            # Is it ok to print the IP? Looks so, judging by this
            # https://developers.home-assistant.io/docs/development_guidelines?_highlight=print&_highlight=out#log-messages
            # Also, I am opting for .error over .exception since the latter includes
            # a humongous traceback, which looks far too scary for such a minor thing
            _LOGGER.error(
                "Failed to connect to device %s. Check the specified IP address / mDNS, "
                "as well as whether the device is connected to power and the WiFi",
                user_input[CONF_IP_ADDRESS],
            )
            errors["base"] = "cannot_connect"
        except InvalidAuth:
            _LOGGER.error(
                "Incorrect password for device %s", user_input[CONF_IP_ADDRESS]
            )
            errors["base"] = "invalid_auth"
        except Exception:  # pylint: disable=broad-except
            # This really shouldn't happen, so .exception is perhaps more appropriate
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            _LOGGER.debug("Successfully connected to %s", user_input[CONF_IP_ADDRESS])
            await self.async_set_unique_id(device_id)
            self._abort_if_unique_id_configured()

            self._title += device_name
            self._data.update(user_input)

            return await self.async_step_configure()

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_configure(
        self, user_input: dict[str, str] | None = None
    ) -> FlowResult:
        """Handle the second step of setup: specify the minimal config.

        This prompts the user to specify the scanning interval and whether to
        return the smoothed (average) data or the momentary readings.
        """
        if not user_input:
            return self.async_show_form(
                step_id="configure", data_schema=STEP_CONFIG_SCHEMA
            )

        self._data.update(user_input)

        return self.async_create_entry(title=self._title, data=self._data)


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
