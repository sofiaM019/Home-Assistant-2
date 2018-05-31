"""
Support for Waze travel time sensor.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.waze_travel_time/
"""
from datetime import timedelta
import logging

import requests
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import ATTR_ATTRIBUTION, CONF_NAME, CONF_REGION
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

REQUIREMENTS = ['WazeRouteCalculator==0.5']

_LOGGER = logging.getLogger(__name__)

ATTR_DISTANCE = 'distance'
ATTR_ROUTE = 'route'

CONF_ATTRIBUTION = "Data provided by the Waze.com"
CONF_DESTINATION = 'destination'
CONF_ORIGIN = 'origin'
CONF_INCL_FILTER = 'incl_filter'
CONF_EXCL_FILTER = 'excl_filter'

DEFAULT_NAME = 'Waze Travel Time'

ICON = 'mdi:car'

REGIONS = ['US', 'NA', 'EU', 'IL']

TRACKABLE_DOMAINS = ['sensor', 'input_text']

SCAN_INTERVAL = timedelta(minutes=5)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_ORIGIN): cv.string,
    vol.Required(CONF_DESTINATION): cv.string,
    vol.Required(CONF_REGION): vol.In(REGIONS),
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_INCL_FILTER): cv.string,
    vol.Optional(CONF_EXCL_FILTER): cv.string,
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the Waze travel time sensor platform."""
    destination = config.get(CONF_DESTINATION)
    name = config.get(CONF_NAME)
    origin = config.get(CONF_ORIGIN)
    region = config.get(CONF_REGION)
    incl_filter = config.get(CONF_INCL_FILTER)
    excl_filter = config.get(CONF_EXCL_FILTER)

    try:
        waze_data = WazeRouteData(
            hass, origin, destination, region, incl_filter, excl_filter)
    except requests.exceptions.HTTPError as error:
        _LOGGER.error("%s", error)
        return

    add_devices([WazeTravelTime(waze_data, name)], True)


class WazeTravelTime(Entity):
    """Representation of a Waze travel time sensor."""

    def __init__(self, waze_data, name):
        """Initialize the Waze travel time sensor."""
        self._name = name
        self._state = None
        self.waze_data = waze_data

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return round(self._state['duration'])

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return 'min'

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return ICON

    @property
    def device_state_attributes(self):
        """Return the state attributes of the last update."""
        return {
            ATTR_ATTRIBUTION: CONF_ATTRIBUTION,
            CONF_ORIGIN: self._state['origin'],
            CONF_DESTINATION: self._state['destination'],
            ATTR_DISTANCE: round(self._state['distance']),
            ATTR_ROUTE: self._state['route'],
        }

    def update(self):
        """Fetch new state data for the sensor."""
        try:
            self.waze_data.update()
            self._state = self.waze_data.data
        except KeyError:
            _LOGGER.error("Error retrieving data from server")


class WazeRouteData(object):
    """Get data from Waze."""

    def __init__(self, hass, origin, destination, region,
                 incl_filter, excl_filter):
        """Initialize the data object."""
        self._hass = hass
        self._region = region
        self._incl_filter = incl_filter
        self._excl_filter = excl_filter
        self.data = {}

        # Check if location is a trackable entity
        if origin.split('.', 1)[0] in TRACKABLE_DOMAINS:
            self._origin_entity_id = origin
        else:
            self._origin = origin

        if destination.split('.', 1)[0] in TRACKABLE_DOMAINS:
            self._destination_entity_id = destination
        else:
            self._destination = destination

    @Throttle(SCAN_INTERVAL)
    def update(self):
        """Check if origin/destination are entities, then get travel time."""

        if hasattr(self, '_origin_entity_id'):
            self._origin = self._hass.states.get(self._origin_entity_id).state

        if hasattr(self, '_destination_entity_id'):
            self._destination = \
                self._hass.states.get(self._destination_entity_id).state

        self.data['origin'] = self._origin
        self.data['destination'] = self._destination

        if (self._origin is None or self._origin == "" or
                self._destination is None or self._destination == ""):
            _LOGGER.debug("Origin or destination are not locations.")
            self.data['duration'] = 0
            self.data['distance'] = 0
            self.data['route'] = "No route"
        else:
            import WazeRouteCalculator
            _LOGGER.debug("Update in progress...")
            try:
                params = WazeRouteCalculator.WazeRouteCalculator(
                    self._origin, self._destination, self._region, None)
                results = params.calc_all_routes_info()
                if self._incl_filter is not None:
                    results = {k: v for k, v in results.items() if
                               self._incl_filter.lower() in k.lower()}
                if self._excl_filter is not None:
                    results = {k: v for k, v in results.items() if
                               self._excl_filter.lower() not in k.lower()}
                best_route = next(iter(results))
                (duration, distance) = results[best_route]
                best_route_str = \
                    bytes(best_route, 'ISO-8859-1').decode('UTF-8')
                self.data['duration'] = duration
                self.data['distance'] = distance
                self.data['route'] = best_route_str
            except WazeRouteCalculator.WRCError as exp:
                _LOGGER.error("Error on retrieving data: %s", exp)
                return
