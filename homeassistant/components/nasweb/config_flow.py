"""Config flow for NASweb integration."""
from __future__ import annotations

import logging
from typing import Any, Optional

import voluptuous as vol
from webio_api import WebioAPI
from webio_api.api_client import AuthError

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .commons import get_hass_address_from_entry, initialize_notification_coordinator
from .const import CONF_HA_ADDRESS, DOMAIN, NASWEB_SCHEMA_IMG_URL, NOTIFY_COORDINATOR
from .coordinator import NASwebCoordinator, NotificationCoordinator

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(CONF_HA_ADDRESS): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate user-provided data."""
    webio_api = WebioAPI(data[CONF_HOST], data[CONF_USERNAME], data[CONF_PASSWORD])
    if not await webio_api.check_connection():
        raise CannotConnect
    try:
        await webio_api.refresh_device_info()
    except AuthError as e:
        raise InvalidAuth from e

    hass.data.setdefault(DOMAIN, {})
    notifi_coordinator: Optional[NotificationCoordinator] = hass.data[DOMAIN].get(
        NOTIFY_COORDINATOR
    )
    if notifi_coordinator is None:
        notifi_coordinator = initialize_notification_coordinator(hass)
        if notifi_coordinator is None:
            raise RuntimeError("Cannot initialize coordinator")
        hass.data[DOMAIN][NOTIFY_COORDINATOR] = notifi_coordinator

    webio_serial = webio_api.get_serial_number()
    if webio_serial is None:
        raise MissingNASwebData("Device serial number is not available")
    coordinator = NASwebCoordinator(hass, webio_api)

    hass_address = get_hass_address_from_entry(hass, data)
    if hass_address is None:
        raise MissingNASwebData(
            "Cannot determine home assistant address. Try filling 'Home Assistant Address'"
        )

    notifi_coordinator.add_coordinator(webio_serial, coordinator)
    subscription = await webio_api.status_subscription(hass_address, True)
    if not subscription:
        notifi_coordinator.remove_coordinator(webio_serial)
        raise MissingNASwebData("Failed to subscribe for status updates from device")

    result = await notifi_coordinator.check_connection(webio_serial)
    notifi_coordinator.remove_coordinator(webio_serial)
    if not result:
        if subscription:
            await webio_api.status_subscription(hass_address, False)
        raise MissingNASwebData("Did not receive status from device")

    name = webio_api.get_name()
    return {"title": name}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for NASweb."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        filled_schema = None
        if user_input is not None:
            filled_schema = vol.Schema(
                {
                    vol.Required(CONF_HOST, default=user_input.get(CONF_HOST, "")): str,
                    vol.Required(
                        CONF_USERNAME, default=user_input.get(CONF_USERNAME, "")
                    ): str,
                    vol.Required(
                        CONF_PASSWORD, default=user_input.get(CONF_PASSWORD, "")
                    ): str,
                    vol.Optional(
                        CONF_HA_ADDRESS, default=user_input.get(CONF_HA_ADDRESS, "")
                    ): str,
                }
            )
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except MissingNASwebData:
                errors["base"] = "missing_nasweb_data"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=(
                STEP_USER_DATA_SCHEMA if filled_schema is None else filled_schema
            ),
            errors=errors,
            description_placeholders={
                "nasweb_schema_img": '<img src="' + NASWEB_SCHEMA_IMG_URL + '"/><br>',
            },
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""


class MissingNASwebData(HomeAssistantError):
    """Error to indicate missing information from NASweb."""
