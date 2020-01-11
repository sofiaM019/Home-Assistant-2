"""Config flow for Vera."""
import re
from typing import List

import pyvera as pv
from requests.exceptions import RequestException
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_EXCLUDE, CONF_LIGHTS, CONF_SOURCE
from homeassistant.core import callback

from .const import CONF_CONTROLLER, DOMAIN

LIST_REGEX = re.compile("[^0-9]+")


def str_to_int_list(data: str) -> List[int]:
    """Convert a string to an int list."""
    return [int(s) for s in LIST_REGEX.split(data) if len(s) > 0]


def int_list_to_str(data: List[int]) -> str:
    """Convert an int list to a string."""
    return " ".join([str(i) for i in data])


def new_options(lights: List[int], exclude: List[int]) -> dict:
    """Create a standard options object."""
    return {CONF_LIGHTS: lights, CONF_EXCLUDE: exclude}


def options_schema(options: dict = None) -> dict:
    """Return options schema."""
    options = options or {}
    return {
        vol.Optional(
            CONF_LIGHTS, default=int_list_to_str(options.get(CONF_LIGHTS, [])),
        ): str,
        vol.Optional(
            CONF_EXCLUDE, default=int_list_to_str(options.get(CONF_EXCLUDE, [])),
        ): str,
    }


def options_data(user_input: dict) -> dict:
    """Return options dict."""
    return new_options(
        str_to_int_list(user_input.get(CONF_LIGHTS, "")),
        str_to_int_list(user_input.get(CONF_EXCLUDE, "")),
    )


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Options for the component."""

    def __init__(self, config_entry: config_entries.ConfigEntry):
        """Init object."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if self.config_entry.data.get(CONF_SOURCE) == config_entries.SOURCE_IMPORT:
            return self.async_show_form(step_id="from_config")

        if user_input is not None:
            return self.async_create_entry(title="", data=options_data(user_input),)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(options_schema(self.config_entry.options)),
        )


class VeraFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Vera config flow."""

    @staticmethod
    @callback
    def async_get_options_flow(config_entry) -> OptionsFlowHandler:
        """Get the options flow."""
        return OptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input: dict = None):
        """Handle user initiated flow."""
        if self.hass.config_entries.async_entries(DOMAIN):
            return self.async_abort(reason="already_setup")

        if user_input is not None:
            return await self.async_step_finish(
                {**user_input, **{CONF_SOURCE: config_entries.SOURCE_USER}}
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {**{vol.Required(CONF_CONTROLLER): str}, **options_schema()}
            ),
        )

    async def async_step_import(self, config: dict):
        """Handle a flow initialized by import."""
        if self.hass.config_entries.async_entries(DOMAIN):
            return self.async_abort(reason="already_setup")

        return await self.async_step_finish(
            {**config, **{CONF_SOURCE: config_entries.SOURCE_IMPORT}}
        )

    async def async_step_finish(self, config: dict):
        """Validate and create config entry."""
        base_url = config[CONF_CONTROLLER] = config.get(CONF_CONTROLLER).rstrip("/")
        controller = pv.VeraController(base_url)

        try:
            await self.hass.async_add_executor_job(controller.refresh_data)
        except RequestException:
            return self.async_abort(
                reason="cannot_connect", description_placeholders={"base_url": base_url}
            )

        await self.async_set_unique_id(controller.serial_number)

        return self.async_create_entry(title=base_url, data=config)
