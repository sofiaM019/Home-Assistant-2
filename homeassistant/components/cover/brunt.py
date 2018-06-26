"""
Support for Brunt Blind Engine covers.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/cover/brunt
"""
import logging
import voluptuous as vol

from homeassistant.exceptions import HomeAssistantError
from homeassistant.const import (
    CONF_NAME, CONF_USERNAME, CONF_PASSWORD)
from homeassistant.components.cover import (
    CoverDevice, SUPPORT_OPEN, SUPPORT_CLOSE, SUPPORT_SET_POSITION,
    ATTR_POSITION, PLATFORM_SCHEMA,
    STATE_OPEN, STATE_CLOSED)
import homeassistant.helpers.config_validation as cv

REQUIREMENTS = ['brunt==0.1.2']

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'brunt'
ATTRIBUTION = 'Based on an unofficial Brunt SDK.'

COVER_FEATURES = SUPPORT_OPEN | SUPPORT_CLOSE | SUPPORT_SET_POSITION

ATTR_COVER_STATE = 'cover_state'
ATTR_CURRENT_POSITION = 'current_position'
ATTR_REQUEST_POSITION = 'request_position'
DEFAULT_NAME = 'brunt blind engine'
NOTIFICATION_ID = 'brunt_notification'
NOTIFICATION_TITLE = 'Brunt Cover Setup'

CLOSED_POSITION = 0
OPEN_POSITION = 100

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the brunt platform."""
    # pylint: disable=no-name-in-module
    from brunt import BruntAPI
    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)

    bapi = BruntAPI(username=username, password=password)
    try:
        things = bapi.getThings()['things']
        if not things:
            raise HomeAssistantError

        add_devices(BruntDevice(
            hass, bapi, thing['NAME'],
            thing['thingUri']) for thing in things)
    except (TypeError, KeyError, NameError, ValueError) as ex:
        _LOGGER.error("%s", ex)
        hass.components.persistent_notification.create(
            'Error: {}<br />'
            'You will need to restart hass after fixing.'
            ''.format(ex),
            title=NOTIFICATION_TITLE,
            notification_id=NOTIFICATION_ID)


class BruntDevice(CoverDevice):
    """Representation of a Brunt cover device.

    Contains the common logic for all Brunt devices.
    """

    def __init__(self, hass, bapi, name, thing_uri):
        """Init the Brunt device."""
        self._bapi = bapi
        self._name = name
        self._thing_uri = thing_uri

        self._state = None
        self._available = None
        self.update()

    @property
    def name(self):
        """Return the name of the device as reported by tellcore."""
        return self._name

    @property
    def available(self):
        """Could the device be accessed during the last update call."""
        return self._available

    @property
    def device_state_attributes(self):
        """Return the device state attributes."""
        data = {}
        if self._state['moveState'] == 1:
            data[ATTR_COVER_STATE] = 'OPENING'
        elif self._state['moveState'] == 2:
            data[ATTR_COVER_STATE] = 'CLOSING'
        elif int(self._state['currentPosition']) == CLOSED_POSITION:
            data[ATTR_COVER_STATE] = 'CLOSED'
        elif int(self._state['currentPosition']) == OPEN_POSITION:
            data[ATTR_COVER_STATE] = 'OPENED'
        else:
            data[ATTR_COVER_STATE] = 'PARTIALLY OPENED'
        data[ATTR_CURRENT_POSITION] = int(self._state['currentPosition'])
        data[ATTR_REQUEST_POSITION] = int(self._state['requestPosition'])
        return data

    @property
    def state(self):
        """Return the state of the cover."""
        return STATE_CLOSED if int(
            self._state['currentPosition']) == CLOSED_POSITION else STATE_OPEN

    @property
    def current_cover_position(self):
        """
        Return current position of cover.
        None is unknown, 0 is closed, 100 is fully open.
        """
        return int(self._state['currentPosition'])

    @property
    def device_class(self):
        """Return the class of this device, from component DEVICE_CLASSES."""
        return 'window'

    @property
    def supported_features(self):
        """Flag supported features."""
        return COVER_FEATURES

    @property
    def is_closed(self):
        """"Return true if cover is closed, else False."""
        return int(self._state['currentPosition']) == CLOSED_POSITION

    def update(self):
        """Poll the current state of the device."""
        try:
            self._state = self._bapi.getState(
                thingUri=self._thing_uri)['thing']
            self._available = True
        except (TypeError, KeyError, NameError, ValueError) as ex:
            _LOGGER.error("%s", ex)
            self._available = False

    def open_cover(self, **kwargs):
        """ set the cover to the open position. """
        self._bapi.changeRequestPosition(
            OPEN_POSITION, thingUri=self._thing_uri)

    def close_cover(self, **kwargs):
        """ set the cover to the closed position. """
        self._bapi.changeRequestPosition(
            CLOSED_POSITION, thingUri=self._thing_uri)

    def set_cover_position(self, **kwargs):
        """ set the cover to a specific position. """
        if ATTR_POSITION in kwargs:
            self._bapi.changeRequestPosition(
                int(kwargs[ATTR_POSITION]), thingUri=self._thing_uri)
