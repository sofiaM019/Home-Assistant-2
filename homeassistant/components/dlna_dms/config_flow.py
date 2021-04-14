"""Config flow for DLNA DMS."""
from __future__ import annotations

import logging
from pprint import pformat
from typing import Any, cast
from urllib.parse import urlparse

from async_upnp_client.profiles.dlna import DmsDevice
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import ssdp
from homeassistant.const import CONF_DEVICE_ID, CONF_ENTITY_ID, CONF_HOST, CONF_URL
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import IntegrationError
from homeassistant.util import slugify

from .const import DEFAULT_NAME, DOMAIN

LOGGER = logging.getLogger(__name__)


class ConnectError(IntegrationError):
    """Error occurred when trying to connect to a device."""


class DlnaDmsFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a DLNA DMS config flow.

    The Unique Service Name (USN) of the DMS device is used as the unique_id for
    config entries and for entities. This USN may differ from the root USN if
    the DMS is an embedded device.
    """

    VERSION = 1

    def __init__(self) -> None:
        """Initialize flow."""
        self._discoveries: dict[str, ssdp.SsdpServiceInfo] = {}
        self._location: str | None = None
        self._usn: str | None = None
        self._name: str | None = None

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Define the config flow to handle options."""
        return DlnaDmsOptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initialized by the user by listing unconfigured devices."""
        LOGGER.debug("async_step_user: user_input: %s", user_input)

        if user_input is not None and (host := user_input.get(CONF_HOST)):
            # User has chosen a device, ask for confirmation
            discovery = self._discoveries[host]
            await self._async_set_info_from_discovery(discovery)
            return self._create_entry()

        if not (discoveries := await self._async_get_discoveries()):
            # Nothing found, abort configuration
            return self.async_abort(reason="no_devices_found")

        self._discoveries = {
            discovery.upnp.get(ssdp.ATTR_UPNP_FRIENDLY_NAME)
            or cast(str, urlparse(discovery.ssdp_location).hostname): discovery
            for discovery in discoveries
        }

        data_schema = vol.Schema(
            {vol.Optional(CONF_HOST): vol.In(self._discoveries.keys())}
        )
        return self.async_show_form(step_id="user", data_schema=data_schema)

    async def async_step_ssdp(self, discovery_info: ssdp.SsdpServiceInfo) -> FlowResult:
        """Handle a flow initialized by SSDP discovery."""
        LOGGER.debug("async_step_ssdp: discovery_info %s", pformat(discovery_info))

        await self._async_set_info_from_discovery(discovery_info)

        # Abort if the device doesn't support all services required for a DmsDevice.
        # Use the discovery_info instead of DmsDevice.is_profile_device to avoid
        # contacting the device again.
        discovery_service_list = discovery_info.upnp.get(ssdp.ATTR_UPNP_SERVICE_LIST)
        if not discovery_service_list:
            return self.async_abort(reason="not_dms")
        discovery_service_ids = {
            service.get("serviceId")
            for service in discovery_service_list.get("service") or []
        }
        if not DmsDevice.SERVICE_IDS.issubset(discovery_service_ids):
            return self.async_abort(reason="not_dms")

        # Abort if another config entry has the same location, in case the
        # device doesn't have a static and unique UDN (breaking the UPnP spec).
        self._async_abort_entries_match({CONF_URL: self._location})

        self.context["title_placeholders"] = {"name": self._name}

        return await self.async_step_confirm()

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Allow the user to confirm adding the device."""
        LOGGER.debug("async_step_confirm: %s", user_input)

        if user_input is not None:
            return self._create_entry()

        self._set_confirm_only()
        return self.async_show_form(step_id="confirm")

    def _create_entry(self) -> FlowResult:
        """Create a config entry, assuming all required information is now known."""
        LOGGER.debug(
            "_async_create_entry: location: %s, USN: %s", self._location, self._usn
        )
        assert self._name
        assert self._location
        assert self._usn

        source_id = self._generate_source_id()

        data = {CONF_URL: self._location, CONF_DEVICE_ID: self._usn}
        options = {CONF_ENTITY_ID: source_id}
        return self.async_create_entry(title=self._name, data=data, options=options)

    async def _async_set_info_from_discovery(
        self, discovery_info: ssdp.SsdpServiceInfo
    ) -> None:
        """Set information required for a config entry from the SSDP discovery."""
        LOGGER.debug(
            "_async_set_info_from_discovery: location: %s, USN: %s",
            discovery_info.ssdp_location,
            discovery_info.ssdp_usn,
        )

        if not self._location:
            self._location = discovery_info.ssdp_location
            assert isinstance(self._location, str)

        self._usn = discovery_info.ssdp_usn
        await self.async_set_unique_id(self._usn)

        # Abort if already configured, but update the last-known location
        self._abort_if_unique_id_configured(
            updates={CONF_URL: self._location}, reload_on_update=False
        )

        self._name = (
            discovery_info.upnp.get(ssdp.ATTR_UPNP_FRIENDLY_NAME)
            or urlparse(self._location).hostname
            or DEFAULT_NAME
        )

    async def _async_get_discoveries(self) -> list[ssdp.SsdpServiceInfo]:
        """Get list of unconfigured DLNA devices discovered by SSDP."""
        LOGGER.debug("_get_discoveries")

        # Get all compatible devices from ssdp's cache
        discoveries: list[ssdp.SsdpServiceInfo] = []
        for udn_st in DmsDevice.DEVICE_TYPES:
            st_discoveries = await ssdp.async_get_discovery_info_by_st(
                self.hass, udn_st
            )
            discoveries.extend(st_discoveries)

        # Filter out devices already configured
        current_unique_ids = {
            entry.unique_id
            for entry in self._async_current_entries(include_ignore=False)
        }
        discoveries = [
            disc for disc in discoveries if disc.ssdp_udn not in current_unique_ids
        ]

        return discoveries

    def _generate_source_id(self) -> str:
        """Generate a unique source ID."""
        assert self._name
        # Get list of other source_ids
        source_ids = {
            entry.options.get(CONF_ENTITY_ID)
            for entry in self._async_current_entries(include_ignore=True)
        }
        source_id_base = slugify(self._name)
        if source_id_base not in source_ids:
            return source_id_base

        tries = 1
        while (suggested_source_id := f"{source_id_base}_{tries}") in source_ids:
            tries += 1

        return suggested_source_id


class DlnaDmsOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle a DLNA DMS options flow."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        # Don't modify existing (read-only) options -- copy and update instead
        options = dict(self.config_entry.options)

        if user_input is not None:
            LOGGER.debug("user_input: %s", user_input)
            source_id = user_input[CONF_ENTITY_ID]
            # NOTE: source_id is not checked for uniqueness because we don't
            # have access from here to the other config entries to check (no
            # hass object reference).
            options[CONF_ENTITY_ID] = source_id

            # Save updated options
            return self.async_create_entry(title="", data=options)

        fields = {vol.Required(CONF_ENTITY_ID, default=options[CONF_ENTITY_ID]): str}

        return self.async_show_form(step_id="init", data_schema=vol.Schema(fields))
