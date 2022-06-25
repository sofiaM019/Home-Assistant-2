"""Config flow to configure the Season integration."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow
from homeassistant.const import CONF_NAME, CONF_TYPE
from homeassistant.data_entry_flow import FlowResult

from .const import DEFAULT_NAME, DOMAIN, TYPE_ASTRONOMICAL, TYPE_METEOROLOGICAL


class SeasonConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow for Season."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initialized by the user."""
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_TYPE])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=user_input.get(CONF_NAME, DEFAULT_NAME),
                data={CONF_TYPE: user_input[CONF_TYPE]},
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_TYPE, default=TYPE_ASTRONOMICAL): vol.In(
                        {
                            TYPE_ASTRONOMICAL: "Astronomical",
                            TYPE_METEOROLOGICAL: "Meteorological",
                        }
                    )
                },
            ),
        )

    async def async_step_import(self, user_input: dict[str, Any]) -> FlowResult:
        """Handle import from configuration.yaml."""
        return await self.async_step_user(user_input)
