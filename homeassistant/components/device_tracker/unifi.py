"""
Support for Unifi WAP controllers.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/device_tracker.unifi/
"""
import logging
from datetime import timedelta
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.device_tracker import (
    DOMAIN, PLATFORM_SCHEMA, DeviceScanner)
from homeassistant.const import CONF_HOST, CONF_USERNAME, CONF_PASSWORD
from homeassistant.const import CONF_VERIFY_SSL
import homeassistant.util.dt as dt_util

REQUIREMENTS = ['pyunifi==2.13']

_LOGGER = logging.getLogger(__name__)
CONF_PORT = 'port'
CONF_SITE_ID = 'site_id'
CONF_DETECTION_TIME = 'detection_time'

DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 8443
DEFAULT_VERIFY_SSL = True
DEFAULT_DETECTION_TIME = timedelta(seconds=300)

NOTIFICATION_ID = 'unifi_notification'
NOTIFICATION_TITLE = 'Unifi Device Tracker Setup'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_HOST, default=DEFAULT_HOST): cv.string,
    vol.Optional(CONF_SITE_ID, default='default'): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PORT, default=DEFAULT_PORT): cv.port,
    vol.Optional(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL): vol.Any(
        cv.boolean, cv.isfile),
    vol.Optional(CONF_DETECTION_TIME, default=DEFAULT_DETECTION_TIME): vol.All(
        cv.time_period, cv.positive_timedelta)
})


def get_scanner(hass, config):
    """Set up the Unifi device_tracker."""
    from pyunifi.controller import Controller, APIError

    host = config[DOMAIN].get(CONF_HOST)
    username = config[DOMAIN].get(CONF_USERNAME)
    password = config[DOMAIN].get(CONF_PASSWORD)
    site_id = config[DOMAIN].get(CONF_SITE_ID)
    port = config[DOMAIN].get(CONF_PORT)
    verify_ssl = config[DOMAIN].get(CONF_VERIFY_SSL)
    detection_time = config[DOMAIN].get(CONF_DETECTION_TIME)

    try:
        ctrl = Controller(host, username, password, port, version='v4',
                          site_id=site_id, ssl_verify=verify_ssl)
    except APIError as ex:
        _LOGGER.error("Failed to connect to Unifi: %s", ex)
        hass.components.persistent_notification.create(
            'Failed to connect to Unifi. '
            'Error: {}<br />'
            'You will need to restart hass after fixing.'
            ''.format(ex),
            title=NOTIFICATION_TITLE,
            notification_id=NOTIFICATION_ID)
        return False

    return UnifiScanner(ctrl, detection_time)


class UnifiScanner(DeviceScanner):
    """Provide device_tracker support from Unifi WAP client data."""

    def __init__(self, controller, detection_time: timedelta):
        """Initialize the scanner."""
        self._detection_time = detection_time
        self._controller = controller
        self._update()

    def _update(self):
        """Get the clients from the device."""
        from pyunifi.controller import APIError
        try:
            clients = self._controller.get_clients()
        except APIError as ex:
            _LOGGER.error("Failed to scan clients: %s", ex)
            clients = []

        new_enough = dt_util.utcnow() - self._detection_time
        self._clients = {c['mac']: c for c in clients
                         if c['last_seen'] > new_enough}

    def scan_devices(self):
        """Scan for devices."""
        self._update()
        return self._clients.keys()

    def get_device_name(self, mac):
        """Return the name (if known) of the device.

        If a name has been set in Unifi, then return that, else
        return the hostname if it has been detected.
        """
        client = self._clients.get(mac, {})
        name = client.get('name') or client.get('hostname')
        _LOGGER.debug("Device %s name %s", mac, name)
        return name
