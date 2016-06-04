"""
Support for the NetAtmo Weather Service.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.netatmo/
"""
import logging
from homeassistant.components import discovery
from homeassistant.const import (
    CONF_API_KEY, CONF_PASSWORD, CONF_USERNAME)
from homeassistant.helpers import validate_config

REQUIREMENTS = [
    'https://github.com/jabesq/netatmo-api-python/archive/'
    'v0.5.0.zip#lnetatmo==0.5.0']

_LOGGER = logging.getLogger(__name__)

CONF_SECRET_KEY = 'secret_key'

DOMAIN = "netatmo"
NETATMO_AUTH = None

_LOGGER = logging.getLogger(__name__)

DISCOVER_SENSORS = 'netatmo.sensors'
DISCOVER_CAMERAS = 'netatmo.cameras'


def setup(hass, config):
    """Setup the NetAtmo sensor."""
    if not validate_config(config,
                           {DOMAIN: [CONF_API_KEY,
                                     CONF_USERNAME,
                                     CONF_PASSWORD,
                                     CONF_SECRET_KEY]},
                           _LOGGER):
        return None

    import lnetatmo

    global NETATMO_AUTH
    NETATMO_AUTH = lnetatmo.ClientAuth(config[DOMAIN][CONF_API_KEY],
                                       config[DOMAIN][CONF_SECRET_KEY],
                                       config[DOMAIN][CONF_USERNAME],
                                       config[DOMAIN][CONF_PASSWORD],
                                       "read_station read_camera access_camera")

    if not NETATMO_AUTH:
        _LOGGER.error(
            "Connection error "
            "Please check your settings for NetAtmo API.")
        return False

    for component, discovery_service in (
            ('camera', DISCOVER_CAMERAS), ('sensor', DISCOVER_SENSORS)):
        discovery.discover(hass, discovery_service, component=component,
                           hass_config=config)

    return True
