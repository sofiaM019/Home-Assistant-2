"""Config flow for YouTube integration."""
from __future__ import annotations

import logging
from typing import Any

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import HttpRequest
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_TOKEN
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
)

from .const import CONF_CHANNELS, DEFAULT_ACCESS, DOMAIN


class OAuth2FlowHandler(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN
):
    """Config flow to handle Google OAuth2 authentication."""

    _data: dict[str, Any] = {}
    _own_channel: dict[str, Any] = {}

    DOMAIN = DOMAIN

    reauth_entry: ConfigEntry | None = None

    @property
    def logger(self) -> logging.Logger:
        """Return logger."""
        return logging.getLogger(__name__)

    @property
    def extra_authorize_data(self) -> dict[str, Any]:
        """Extra data that needs to be appended to the authorize url."""
        return {
            "scope": " ".join(DEFAULT_ACCESS),
            # Add params to ensure we get back a refresh token
            "access_type": "offline",
            "prompt": "consent",
        }

    async def async_oauth_create_entry(self, data: dict[str, Any]) -> FlowResult:
        """Create an entry for the flow, or update existing entry."""

        service = build(
            "youtube",
            "v3",
            credentials=Credentials(data[CONF_TOKEN][CONF_ACCESS_TOKEN]),
        )
        # pylint: disable=no-member
        own_channel_request: HttpRequest = service.channels().list(
            part="snippet", mine=True
        )
        response = await self.hass.async_add_executor_job(own_channel_request.execute)
        own_channel = response["items"][0]
        self._own_channel = own_channel
        self._data = data

        await self.async_set_unique_id(own_channel["id"])
        self._abort_if_unique_id_configured()

        return await self.async_step_channels()

    async def async_step_channels(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Select which channels to track."""
        service = build(
            "youtube",
            "v3",
            credentials=Credentials(self._data[CONF_TOKEN][CONF_ACCESS_TOKEN]),
        )
        if user_input:
            return self.async_create_entry(
                title=self._own_channel["snippet"]["title"],
                data=self._data,
                options=user_input,
            )
        # pylint: disable=no-member
        subscription_request: HttpRequest = service.subscriptions().list(
            part="snippet", mine=True, maxResults=50
        )
        response = await self.hass.async_add_executor_job(subscription_request.execute)
        selectable_channels = [
            SelectOptionDict(
                value=subscription["snippet"]["resourceId"]["channelId"],
                label=subscription["snippet"]["title"],
            )
            for subscription in response["items"]
        ]
        return self.async_show_form(
            step_id="channels",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CHANNELS): SelectSelector(
                        SelectSelectorConfig(options=selectable_channels, multiple=True)
                    ),
                }
            ),
        )
