"""
Support for IOTA wallets.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/iota/
"""
import logging
from datetime import timedelta

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.discovery import load_platform
from homeassistant.helpers.entity import Entity

DOMAIN = 'iota'

REQUIREMENTS = ['pyota==2.0.3']

IOTA_PLATFORMS = ['sensor']

SCAN_INTERVAL = timedelta(minutes=10)

CONF_IRI = 'iri'
CONF_TESTNET = 'testnet'
CONF_WALLETS = 'wallets'
CONF_WALLET_NAME = 'name'
CONF_WALLET_SEED = 'seed'

WALLET_CONFIG = vol.Schema({
    vol.Required(CONF_WALLET_NAME): cv.string,
    vol.Required(CONF_WALLET_SEED): cv.string,
})

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_IRI): vol.All(str),
        vol.Optional(CONF_TESTNET, default=False): cv.boolean,
        vol.Required(CONF_WALLETS): vol.All(cv.ensure_list, [WALLET_CONFIG])
    })
}, extra=vol.ALLOW_EXTRA)

_LOGGER = logging.getLogger(__name__)


def setup(hass, config):
    """Setup IOTA component"""

    # Set domain sepecific data
    iota_config = config[DOMAIN]
    hass.data[DOMAIN] = {
        'iri': iota_config[CONF_IRI],
        'is_testnet': iota_config[CONF_TESTNET],
        'wallets': iota_config[CONF_WALLETS]
    }

    # Set states of IRI config
    hass.states.set('iota.iri', hass.data[DOMAIN]['iri'])
    hass.states.set('iota.is_testnet', hass.data[DOMAIN]['is_testnet'])

    # Load platforms
    for platform in IOTA_PLATFORMS:
        load_platform(hass, platform, DOMAIN, {}, iota_config)

    return True


class IotaDevice(Entity):
    """Representation of a IOTA device."""

    def __init__(self, name, seed, iri, is_testnet=False):
        """Initialisation of the IOTA device."""
        self._name = name
        self._seed = seed
        self.iri = iri
        self.is_testnet = is_testnet

    @property
    def name(self):
        """Return the default name of the device."""
        return self._name

    @property
    def should_poll(self):
        """Get polling requirement from IOTA device."""
        return True

    @property
    def device_state_attributes(self):
        """Return the state attributes of the device."""
        attr = {CONF_WALLET_NAME: self._name}
        return attr

    @property
    def api(self):
        """ Constructs API object for interaction with the IRI node"""
        from iota import Iota
        return Iota(adapter=self.iri, seed=self._seed)
