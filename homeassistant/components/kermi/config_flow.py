"""Config flow for kermi."""

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry, ConfigFlowResult
from homeassistant.const import CONF_HOST

from .const import DOMAIN


class KermiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Kermi."""



    async def async_step_user(self, user_input=None) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            # If the input is valid, create the config entry
            if not errors:
                entry = self.async_create_entry(
                    title=user_input[CONF_HOST],
                    data=user_input,
                )
                self._abort_if_unique_id_configured()
                return entry

        # Provide default values only when user_input is not None
        default_host = user_input[CONF_HOST] if user_input else ""

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=default_host): str,
                    vol.Required("heatpump_device_address", default=40): int,
                    vol.Optional("climate_device_address", default=50): int,
                    vol.Optional("water_heater_device_address", default=51): int,
                }
            ),
            errors=errors,
        )
