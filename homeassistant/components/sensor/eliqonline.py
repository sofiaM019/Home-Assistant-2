"""
homeassistant.components.sensor.eliqonline
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
monitors home energy use for the eliq online service

api documentation:
  https://my.eliq.se/knowledge/sv-SE/49-eliq-online/299-eliq-online-api

access to api access token:
  https://my.eliq.se/user/settings/api

current energy use:
  https://my.eliq.se/api/datanow?accesstoken=<token>

history:
  https://my.eliq.se/api/data?startdate=2015-12-14&intervaltype=6min&accesstoken=<token>

"""

import logging
from datetime import timedelta
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle
from homeassistant.const import (STATE_UNKNOWN, CONF_ACCESS_TOKEN, CONF_NAME)

_LOGGER = logging.getLogger(__name__)

REQUIREMENTS = ['eliqonline==1.0.11']

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=30)

def setup_platform(hass, config, add_devices, discovery_info=None):
    import eliqonline

    access_token = config.get(CONF_ACCESS_TOKEN)
    name         = config.get(CONF_NAME)
    channel_id   = config.get("channel_id")

    if not access_token:
        _LOGGER.error(
            "Configuration Error"
            "Please make sure you have configured your access token which can be aquired from https://my.eliq.se/user/settings/api")
        return None

    api = eliqonline.API(access_token)
    add_devices([EliqSensor(api, channel_id, name)])
        

class EliqSensor(Entity):
    """ Implements a Eliq sensor. """

    def __init__(self, api, channel_id, name):
        self._name = "Energy Usage"
        if name:
            self._name = name + " " + self._name
        self._unit_of_measurement = "W"
        self._state = STATE_UNKNOWN
        
        self.api = api
        self.channel_id = channel_id
        self.update()


    @property
    def name(self):
        """ Returns the name. """
        return self._name


    @property
    def unit_of_measurement(self):
        """ Unit of measurement of this entity, if any. """
        return self._unit_of_measurement


    @property
    def state(self):
        """ Returns the state of the device. """
        return self._state


    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """ Gets the latest data """
        self._state = int(self.api.get_data_now(channelid=self.channel_id).power)
