"""
"""
import logging
from datetime import timedelta, datetime

import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_FRIENDLY_NAME
from homeassistant.helpers.entity import Entity
from homeassistant.const import (
    ATTR_ATTRIBUTION)
import homeassistant.helpers.config_validation as cv

REQUIREMENTS = ['https://github.com/eliseomartelli/pygtt/archive/master.zip#pygtt==1.1.1']

_LOGGER = logging.getLogger(__name__)

CONF_STOP = 'stop'
CONF_BUS_NAME = 'bus_name'

ICON = 'mdi:train'

SCAN_INTERVAL = timedelta(minutes=2)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_STOP): cv.string,
    vol.Optional(CONF_BUS_NAME): cv.string,
})

def setup_platform(hass, config, add_entities, discovery_info=None):
    stop = config.get(CONF_STOP)
    bus_name = config.get(CONF_BUS_NAME)

    add_entities([GttSensor(stop, bus_name)], True)

class GttSensor(Entity):
    def __init__(self, stop, bus_name):
        self.data = GttData(stop, bus_name)
        self._state = None
        self._name = 'stop_{}'.format(stop)

    @property
    def name(self):
        return self._name
    
    @property
    def icon(self):
        return ICON
    
    @property
    def state(self):
        return self._state
    
    def update(self):
        self.data.get_data()
        self._state = "{}: {}".format(self.data.state_bus['bus_name'], self.data.state_bus['time'][0]['run'])

class GttData:
    def __init__(self, stop, bus_name):
        from pygtt import PyGTT
        self._pygtt = PyGTT()
        self._stop = stop
        self._bus_name = bus_name
        self.bus_list = {}
        self.state_bus = {}
    
    def get_data(self):
        self.bus_list = self._pygtt.get_by_stop(self._stop)
        if self._bus_name is not None:
            self.get_bus_by_name()
        else:
            self.get_next_bus()

    def get_next_bus(self):
        prev = None
        for bus in self.bus_list:
            this_time = 0
            prev_time = 0
            if prev is not None:
                this_time = datetime.strptime(bus['time'][0]['run'], "%H:%M")
                prev_time = datetime.strptime(prev['time'][0]['run'], "%H:%M")
            if this_time <= prev_time:
                prev = bus
        self.state_bus = prev

    def get_bus_by_name(self):
        for bus in self.bus_list:
            if bus['bus_name'] == self._bus_name:
                self.state_bus = bus
                return       

