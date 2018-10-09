"""Implement the auth feature from Hass.io for Add-ons."""
import logging
from ipaddress import ip_address
import os

from aiohttp import web
from aiohttp.web_exceptions import (
    HTTPForbidden, HTTPNotFound, HTTPUnauthorized)

from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.components.http import HomeAssistantView
from homeassistant.components.http.const import KEY_REAL_IP


_LOGGER = logging.getLogger(__name__)

ATTR_USERNAME = 'username'
ATTR_PASSWORD = 'password'


@callback
def async_setup_auth(hass):
    """Auth setup."""
    hassio_auth = HassIOAuth(hass)
    hass.http.register_view(hassio_auth)


class HassIOAuth(HomeAssistantView):
    """Hass.io view to handle base part."""

    name = "api:hassio_auth"
    url = "/api/hassio_auth"

    def __init__(self, hass):
        """Initialize WebView."""
        self.hass = hass

    async def post(self, request):
        """Handle new discovery requests."""
        hassio_ip = os.environ['HASSIO'].split(':')[0]
        if request[KEY_REAL_IP] != ip_address(hassio_ip):
            _LOGGER.error(
                "Invalid auth request from %s", request[KEY_REAL_IP])
            raise HTTPForbidden()

        data = await request.json()
        await self._check_login(data[ATTR_USERNAME], data[ATTR_PASSWORD])
        return web.Response(status=200)

    def _get_provider(self):
        """Return Homeassistant auth provider."""
        for prv in self.hass.auth.auth_providers:
            if prv.type == 'homeassistant':
                return prv

        _LOGGER.error("Can't find Home Assistant auth.")
        raise HTTPNotFound()

    async def _check_login(self, username, password):
        """Check User credentials."""
        provider = self._get_provider()

        try:
            await provider.async_validate_login(username, password)
        except HomeAssistantError:
            raise HTTPUnauthorized() from None
