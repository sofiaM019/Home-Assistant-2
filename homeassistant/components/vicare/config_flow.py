"""Config flow for ViCare integration."""

from __future__ import annotations

import logging
from typing import Any

# from PyViCare.PyViCareUtils import (
#     PyViCareInvalidConfigurationError,
#     PyViCareInvalidCredentialsError,
# )
import voluptuous as vol

# from homeassistant.components import dhcp
from homeassistant.config_entries import ConfigEntry, ConfigFlowResult

# from homeassistant.const import CONF_CLIENT_ID, CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers import config_entry_oauth2_flow

from .const import CONF_HEATING_TYPE, DEFAULT_HEATING_TYPE, DOMAIN, HeatingType

_LOGGER = logging.getLogger(__name__)

SCOPES = [
    "IoT User",
    "offline_access",  # required to get a refresh_token
]

# REAUTH_SCHEMA = vol.Schema(
#     {
#         vol.Required(CONF_PASSWORD): cv.string,
#         vol.Required(CONF_CLIENT_ID): cv.string,
#     }
# )

USER_SCHEMA = vol.Schema(
    # REAUTH_SCHEMA.extend(
    {
        #     vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_HEATING_TYPE, default=DEFAULT_HEATING_TYPE.value): vol.In(
            [e.value for e in HeatingType]
        ),
    }
)


# class ViCareConfigFlow(ConfigFlow, domain=DOMAIN):
#     """Handle a config flow for ViCare."""
# AbstractOAuth2FlowHandler
# LocalOAuth2Implementation
class OAuth2FlowHandler(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN
):
    """Config flow to handle Viessmann ViCare OAuth2 authentication."""

    DOMAIN = DOMAIN
    VERSION = 1
    entry: ConfigEntry | None

    @property
    def logger(self) -> logging.Logger:
        """Return logger."""
        return logging.getLogger(__name__)

    @property
    def extra_authorize_data(self) -> dict[str, Any]:
        """Extra data that needs to be appended to the authorize url."""
        return {
            "scope": " ".join(SCOPES),
        }

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Invoke when a user initiates a flow via the user interface."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        #     errors: dict[str, str] = {}

        #     if user_input is not None:
        #         try:
        #             await self.hass.async_add_executor_job(
        #                 vicare_login, user_input
        #             )
        #         except (PyViCareInvalidConfigurationError, PyViCareInvalidCredentialsError):
        #             errors["base"] = "invalid_auth"
        #         else:
        #             return self.async_create_entry(title=VICARE_NAME, data=user_input)

        #     return self.async_show_form(
        #         step_id="user",
        #         data_schema=USER_SCHEMA,
        #         errors=errors,
        #     )

        return await super().async_step_user(user_input)

    # async def async_step_reauth(
    #     self, entry_data: Mapping[str, Any]
    # ) -> ConfigFlowResult:
    #     """Handle re-authentication with ViCare."""
    #     self.entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
    #     return await self.async_step_reauth_confirm()

    # async def async_step_reauth_confirm(
    #     self, user_input: dict[str, Any] | None = None
    # ) -> ConfigFlowResult:
    #     """Confirm re-authentication with ViCare."""
    #     errors: dict[str, str] = {}
    #     assert self.entry is not None

    #     if user_input:
    #         data = {
    #             **self.entry.data,
    #             **user_input,
    #         }

    #         try:
    #             await self.hass.async_add_executor_job(vicare_login, data)
    #         except (PyViCareInvalidConfigurationError, PyViCareInvalidCredentialsError):
    #             errors["base"] = "invalid_auth"
    #         else:
    #             self.hass.config_entries.async_update_entry(
    #                 self.entry,
    #                 data=data,
    #             )
    #             await self.hass.config_entries.async_reload(self.entry.entry_id)
    #             return self.async_abort(reason="reauth_successful")

    #     return self.async_show_form(
    #         step_id="reauth_confirm",
    #         data_schema=self.add_suggested_values_to_schema(
    #             REAUTH_SCHEMA, self.entry.data
    #         ),
    #         errors=errors,
    #     )

    # async def async_step_dhcp(
    #     self, discovery_info: dhcp.DhcpServiceInfo
    # ) -> ConfigFlowResult:
    #     """Invoke when a Viessmann MAC address is discovered on the network."""
    #     formatted_mac = format_mac(discovery_info.macaddress)
    #     _LOGGER.debug("Found device with mac %s", formatted_mac)

    #     await self.async_set_unique_id(formatted_mac)
    #     self._abort_if_unique_id_configured()

    #     if self._async_current_entries():
    #         return self.async_abort(reason="single_instance_allowed")

    #     return await self.async_step_user()
