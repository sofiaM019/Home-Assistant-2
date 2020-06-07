"""Config flow to configure the Azure DevOps integration."""
import logging

from aioazuredevops.client import DevOpsClient
import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.azure_devops.const import (  # pylint:disable=unused-import
    CONF_ORG,
    CONF_PAT,
    CONF_PROJECT,
    DOMAIN,
)
from homeassistant.config_entries import ConfigFlow

_LOGGER = logging.getLogger(__name__)


class AzureDevOpsFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle a Azure DevOps config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize config flow."""
        self._organization = None
        self._project = None
        self._pat = None
        self._reauth = False

    async def _show_setup_form(self, errors=None):
        """Show the setup form to the user."""
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ORG, default=self._organization): str,
                    vol.Required(CONF_PROJECT, default=self._project): str,
                    vol.Optional(CONF_PAT): str,
                }
            ),
            errors=errors or {},
        )

    async def async_step_user(self, user_input=None):
        """Handle a flow initiated by the user."""
        if user_input is None:
            return await self._show_setup_form(user_input)

        self._organization = user_input[CONF_ORG]
        self._project = user_input[CONF_PROJECT]
        self._pat = user_input.get(CONF_PAT)

        return await self.async_step_confirm()

    async def async_step_reauth(self, user_input=None):
        """Handle configuration by re-auth."""
        self._organization = user_input[CONF_ORG]
        self._project = user_input[CONF_PROJECT]
        self._pat = user_input[CONF_PAT]
        self._reauth = True

        await self.async_set_unique_id(f"{self._organization}_{self._project}")

        return await self.async_step_confirm()

    async def async_step_confirm(self):
        """Handle final configuration step."""
        if not self._reauth:
            await self.async_set_unique_id(f"{self._organization}_{self._project}")
            self._abort_if_unique_id_configured()

        errors = {}

        client = DevOpsClient()

        try:
            if self._pat is not None:
                await client.authorize(self._pat, self._organization)
                if not client.authorized:
                    errors["base"] = "authorization_error"
                    return await self._show_setup_form(errors)
            project_info = await client.get_project(self._organization, self._project)
            if project_info is None:
                errors["base"] = "authorization_error"
                return await self._show_setup_form(errors)
        except aiohttp.ClientError:
            errors["base"] = "connection_error"
            return await self._show_setup_form(errors)

        return self.async_create_entry(
            title=f"{self._organization}/{self._project}",
            data={
                CONF_ORG: self._organization,
                CONF_PROJECT: self._project,
                CONF_PAT: self._pat,
            },
        )
