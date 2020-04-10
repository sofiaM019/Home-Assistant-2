"""Config flow to configure the Azure DevOps integration."""
import logging

from azure.devops.connection import Connection
from azure.devops.exceptions import AzureDevOpsServiceError
from msrest.authentication import BasicAuthentication
from msrest.exceptions import ClientRequestError
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.azure_devops.const import (
    CONF_ORG,
    CONF_PAT,
    CONF_PROJECT,
    DOMAIN,
)
from homeassistant.config_entries import ConfigFlow

_LOGGER = logging.getLogger(__name__)


@config_entries.HANDLERS.register(DOMAIN)
class AzureDevOpsFlowHandler(ConfigFlow):
    """Handle a Azure DevOps config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize Azure DevOps flow."""

    async def _show_setup_form(self, errors=None):
        """Show the setup form to the user."""
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ORG): str,
                    vol.Required(CONF_PROJECT): str,
                    vol.Optional(CONF_PAT): str,
                }
            ),
            errors=errors or {},
        )

    async def async_step_user(self, user_input=None):
        """Handle a flow initiated by the user."""
        if user_input is None:
            return await self._show_setup_form(user_input)

        errors = {}

        connection = Connection(
            base_url=f"https://dev.azure.com/{user_input.get(CONF_ORG)}"
        )
        if user_input.get(CONF_PAT) is not None:
            connection.creds = BasicAuthentication("", user_input.get(CONF_PAT))

        try:
            core_client = connection.clients.get_core_client()
            project = core_client.get_project(user_input.get(CONF_PROJECT))
            if not project:
                errors["base"] = "project_error"
                return await self._show_setup_form(errors)
        except AzureDevOpsServiceError as exception:
            _LOGGER.warning(exception)
            errors["base"] = "authorization_error"
            return await self._show_setup_form(errors)
        except ClientRequestError as exception:
            _LOGGER.warning(exception)
            errors["base"] = "connection_error"
            return await self._show_setup_form(errors)

        return self.async_create_entry(
            title=f"{user_input.get(CONF_ORG)}/{user_input.get(CONF_PROJECT)}",
            data={
                CONF_ORG: user_input.get(CONF_ORG),
                CONF_PROJECT: user_input.get(CONF_PROJECT),
                CONF_PAT: user_input.get(CONF_PAT),
            },
        )
