"""This component encapsulates the NVR/camera API and subscription."""
from __future__ import annotations

import logging
import ssl

import aiohttp
from reolink_ip.api import Host

from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.device_registry import format_mac

from .const import CONF_PROTOCOL, CONF_USE_HTTPS, DEFAULT_PROTOCOL, DEFAULT_TIMEOUT

_LOGGER = logging.getLogger(__name__)


class ReolinkHost:
    """The implementation of the Reolink Host class."""

    def __init__(
        self,
        hass: HomeAssistant,
        config: dict,
        options: dict,
    ) -> None:
        """Initialize Reolink Host. Could be either NVR, or Camera."""
        self._hass: HomeAssistant = hass

        self._clientsession: aiohttp.ClientSession | None = None
        self._unique_id: str | None = None

        cur_protocol = (
            DEFAULT_PROTOCOL if CONF_PROTOCOL not in options else options[CONF_PROTOCOL]
        )

        self._api = Host(
            config[CONF_HOST],
            config[CONF_USERNAME],
            config[CONF_PASSWORD],
            port=config.get(CONF_PORT),
            use_https=config.get(CONF_USE_HTTPS),
            protocol=cur_protocol,
            timeout=DEFAULT_TIMEOUT,
            aiohttp_get_session_callback=self.get_iohttp_session,
        )

    @property
    def unique_id(self):
        """Create the unique ID, base for all entities."""
        return self._unique_id

    @property
    def api(self):
        """Return the API object."""
        return self._api

    async def async_init(self) -> bool:
        """Connect to Reolink host."""
        self._api.expire_session()

        if not await self._api.get_host_data():
            return False

        if self._api.mac_address is None:
            return False

        enable_onvif = None
        enable_rtmp = None
        enable_rtsp = None

        if not self._api.onvif_enabled:
            _LOGGER.info(
                "ONVIF is disabled on %s, trying to enable it", self._api.nvr_name
            )
            enable_onvif = True

        if not self._api.rtmp_enabled and self._api.protocol == "rtmp":
            _LOGGER.info(
                "RTMP is disabled on %s, trying to enable it", self._api.nvr_name
            )
            enable_rtmp = True
        elif not self._api.rtsp_enabled and self._api.protocol == "rtsp":
            _LOGGER.info(
                "RTSP is disabled on %s, trying to enable it", self._api.nvr_name
            )
            enable_rtsp = True

        if enable_onvif or enable_rtmp or enable_rtsp:
            if not await self._api.set_net_port(
                enable_onvif=enable_onvif,
                enable_rtmp=enable_rtmp,
                enable_rtsp=enable_rtsp,
            ):
                if enable_onvif:
                    _LOGGER.error(
                        "Unable to switch on ONVIF on %s. You need it to be ON to receive notifications",
                        self._api.nvr_name,
                    )

                if enable_rtmp:
                    _LOGGER.error(
                        "Unable to switch on RTMP on %s. You need it to be ON",
                        self._api.nvr_name,
                    )
                elif enable_rtsp:
                    _LOGGER.error(
                        "Unable to switch on RTSP on %s. You need it to be ON",
                        self._api.nvr_name,
                    )

        if self._unique_id is None:
            self._unique_id = format_mac(self._api.mac_address)

        return True

    async def update_states(self) -> bool:
        """Call the API of the camera device to update the states."""
        return await self._api.get_states()

    async def disconnect(self):
        """Disconnect from the API, so the connection will be released."""
        try:
            await self._api.unsubscribe_all()
        except Exception as error:  # pylint: disable=broad-except
            err = str(error)
            if err:
                _LOGGER.error(
                    "Error while unsubscribing ONVIF events for %s: %s",
                    self._api.nvr_name,
                    err,
                )
            else:
                _LOGGER.error(
                    "Unknown error while unsubscribing ONVIF events for %s",
                    self._api.nvr_name,
                )

        try:
            await self._api.logout()
        except Exception as error:  # pylint: disable=broad-except
            err = str(error)
            if err:
                _LOGGER.error(
                    "Error while logging out of %s: %s", self._api.nvr_name, err
                )
            else:
                _LOGGER.error(
                    "Unknown error while logging out of %s", self._api.nvr_name
                )

    async def stop(self, event=None):
        """Disconnect the API."""
        await self.disconnect()

    def get_iohttp_session(self) -> aiohttp.ClientSession | None:
        """Return the iohttp session."""
        if self._clientsession is None or self._clientsession.closed:
            context = ssl.create_default_context()
            context.set_ciphers("DEFAULT")
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            self._clientsession = async_create_clientsession(
                self._hass, verify_ssl=False
            )

            # If ssl context is not overwritten this error occurs:
            # [[SSL: SSLV3_ALERT_HANDSHAKE_FAILURE] sslv3 alert handshake failure (_ssl.c:992)]
            self._clientsession.connector._ssl = (  # type: ignore[union-attr] # pylint: disable=protected-access
                context
            )

        return self._clientsession
