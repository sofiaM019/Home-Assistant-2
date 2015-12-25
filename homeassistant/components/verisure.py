"""
components.verisure
~~~~~~~~~~~~~~~~~~~
Provides support for verisure components.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/verisure/
"""
import logging
import time

from datetime import timedelta

from homeassistant import bootstrap
from homeassistant.loader import get_component

from homeassistant.helpers import validate_config
from homeassistant.util import Throttle
from homeassistant.const import (
    EVENT_PLATFORM_DISCOVERED,
    ATTR_SERVICE, ATTR_DISCOVERED,
    CONF_USERNAME, CONF_PASSWORD)


DOMAIN = "verisure"
DISCOVER_SENSORS = 'verisure.sensors'
DISCOVER_SWITCHES = 'verisure.switches'
DISCOVER_ALARMS = 'verisure.alarm_control_panel'

DEPENDENCIES = ['alarm_control_panel']
REQUIREMENTS = [
    'https://github.com/persandstrom/python-verisure/archive/'
    '0f53c1d6a9e370566a78e36093b02fbd5144b75d.zip#python-verisure==0.4.1'
    ]

_LOGGER = logging.getLogger(__name__)

MY_PAGES = None
ALARM_STATUS = {}
SMARTPLUG_STATUS = {}
CLIMATE_STATUS = {}

VERISURE_LOGIN_ERROR = None
VERISURE_ERROR = None

SHOW_THERMOMETERS = True
SHOW_HYGROMETERS = True
SHOW_ALARM = True
SHOW_SMARTPLUGS = True

# if wrong password was given don't try again
WRONG_PASSWORD_GIVEN = False

MIN_TIME_BETWEEN_REQUESTS = timedelta(seconds=1)


def setup(hass, config):
    """ Setup the Verisure component. """

    if not validate_config(config,
                           {DOMAIN: [CONF_USERNAME, CONF_PASSWORD]},
                           _LOGGER):
        return False

    from verisure import MyPages, LoginError, Error

    global SHOW_THERMOMETERS, SHOW_HYGROMETERS, SHOW_ALARM, SHOW_SMARTPLUGS
    SHOW_THERMOMETERS = int(config[DOMAIN].get('thermometers', '1'))
    SHOW_HYGROMETERS = int(config[DOMAIN].get('hygrometers', '1'))
    SHOW_ALARM = int(config[DOMAIN].get('alarm', '1'))
    SHOW_SMARTPLUGS = int(config[DOMAIN].get('smartplugs', '1'))

    global MY_PAGES
    MY_PAGES = MyPages(
        config[DOMAIN][CONF_USERNAME],
        config[DOMAIN][CONF_PASSWORD])
    global VERISURE_LOGIN_ERROR, VERISURE_ERROR
    VERISURE_LOGIN_ERROR = LoginError
    VERISURE_ERROR = Error

    try:
        MY_PAGES.login()
    except (ConnectionError, Error) as ex:
        _LOGGER.error('Could not log in to verisure mypages, %s', ex)
        return False

    update_alarm()
    update_climate()
    update_smartplug()

    # Load components for the devices in the ISY controller that we support
    for comp_name, discovery in ((('sensor', DISCOVER_SENSORS),
                                  ('switch', DISCOVER_SWITCHES),
                                  ('alarm_control_panel', DISCOVER_ALARMS))):
        component = get_component(comp_name)
        _LOGGER.info(config[DOMAIN])
        bootstrap.setup_component(hass, component.DOMAIN, config)

        hass.bus.fire(EVENT_PLATFORM_DISCOVERED,
                      {ATTR_SERVICE: discovery,
                       ATTR_DISCOVERED: {}})

    return True


def reconnect():
    """ Reconnect to verisure mypages. """
    try:
        time.sleep(1)
        MY_PAGES.login()
    except VERISURE_LOGIN_ERROR as ex:
        _LOGGER.error("Could not login to Verisure mypages, %s", ex)
        global WRONG_PASSWORD_GIVEN
        WRONG_PASSWORD_GIVEN = True
    except (ConnectionError, VERISURE_ERROR) as ex:
        _LOGGER.error("Could not login to Verisure mypages, %s", ex)


@Throttle(MIN_TIME_BETWEEN_REQUESTS)
def update_alarm():
    update_component(MY_PAGES.alarm.get, ALARM_STATUS)


@Throttle(MIN_TIME_BETWEEN_REQUESTS)
def update_climate():
    update_component(MY_PAGES.climate.get, CLIMATE_STATUS)


@Throttle(MIN_TIME_BETWEEN_REQUESTS)
def update_smartplug():
    update_component(MY_PAGES.smartplug.get, SMARTPLUG_STATUS)


def update_component(get_function, status):
    """ Updates the status of verisure components. """
    if WRONG_PASSWORD_GIVEN:
        _LOGGER.error('Wrong password')
        return
    try:
        for overview in get_function():
            status[overview.id] = overview
    except (ConnectionError, VERISURE_ERROR) as ex:
        _LOGGER.error('Caught connection error %s, tries to reconnect', ex)
        reconnect()
