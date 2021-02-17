"""Support for RESTful API sensors."""
import json
import logging
from xml.parsers.expat import ExpatError

from jsonpath import jsonpath
import voluptuous as vol
import xmltodict

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_DEVICE_CLASS,
    CONF_FORCE_UPDATE,
    CONF_NAME,
    CONF_RESOURCE,
    CONF_RESOURCE_TEMPLATE,
    CONF_UNIT_OF_MEASUREMENT,
    CONF_VALUE_TEMPLATE,
)
from homeassistant.exceptions import PlatformNotReady
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.reload import async_setup_reload_service

from . import (
    CONF_COORDINATOR,
    CONF_JSON_ATTRS,
    CONF_JSON_ATTRS_PATH,
    CONF_REST,
    DOMAIN,
    PLATFORMS,
    RESOURCE_SCHEMA,
    SENSOR_SCHEMA,
    RestEntity,
    create_rest_from_config,
)

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({**RESOURCE_SCHEMA, **SENSOR_SCHEMA})

PLATFORM_SCHEMA = vol.All(
    cv.has_at_least_one_key(CONF_RESOURCE, CONF_RESOURCE_TEMPLATE), PLATFORM_SCHEMA
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the RESTful sensor."""
    await async_setup_reload_service(hass, DOMAIN, PLATFORMS)
    conf = discovery_info or config

    name = conf.get(CONF_NAME)
    unit = conf.get(CONF_UNIT_OF_MEASUREMENT)
    device_class = conf.get(CONF_DEVICE_CLASS)
    json_attrs = conf.get(CONF_JSON_ATTRS)
    json_attrs_path = conf.get(CONF_JSON_ATTRS_PATH)
    value_template = conf.get(CONF_VALUE_TEMPLATE)
    force_update = conf.get(CONF_FORCE_UPDATE)
    resource_template = conf.get(CONF_RESOURCE_TEMPLATE)

    if value_template is not None:
        value_template.hass = hass

    rest = conf.get(CONF_REST)
    coordinator = conf.get(CONF_COORDINATOR)

    if coordinator:
        if rest.data is None:
            await coordinator.async_request_refresh()
    else:
        rest = create_rest_from_config(conf)
        await rest.async_update()

    if rest.data is None:
        raise PlatformNotReady

    # Must update the sensor now (including fetching the rest resource) to
    # ensure it's updating its state.
    async_add_entities(
        [
            RestSensor(
                coordinator,
                rest,
                name,
                unit,
                device_class,
                value_template,
                json_attrs,
                force_update,
                resource_template,
                json_attrs_path,
            )
        ],
    )


class RestSensor(RestEntity):
    """Implementation of a REST sensor."""

    def __init__(
        self,
        coordinator,
        rest,
        name,
        unit_of_measurement,
        device_class,
        value_template,
        json_attrs,
        force_update,
        resource_template,
        json_attrs_path,
    ):
        """Initialize the REST sensor."""
        super.__init__(coordinator, name, device_class, resource_template, force_update)
        self.rest = rest
        self._state = None
        self._unit_of_measurement = unit_of_measurement
        self._value_template = value_template
        self._json_attrs = json_attrs
        self._attributes = None
        self._json_attrs_path = json_attrs_path

    @property
    def unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        return self._unit_of_measurement

    @property
    def available(self):
        """Return if the sensor data are available."""
        if not super().available:
            return False
        return self.rest.data is not None

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    def _update_from_rest_data(self):
        """Update state from the rest data."""
        value = self.rest.data
        _LOGGER.debug("Data fetched from resource: %s", value)
        if self.rest.headers is not None:
            # If the http request failed, headers will be None
            content_type = self.rest.headers.get("content-type")

            if content_type and (
                content_type.startswith("text/xml")
                or content_type.startswith("application/xml")
                or content_type.startswith("application/xhtml+xml")
            ):
                try:
                    value = json.dumps(xmltodict.parse(value))
                    _LOGGER.debug("JSON converted from XML: %s", value)
                except ExpatError:
                    _LOGGER.warning(
                        "REST xml result could not be parsed and converted to JSON"
                    )
                    _LOGGER.debug("Erroneous XML: %s", value)

        if self._json_attrs:
            self._attributes = {}
            if value:
                try:
                    json_dict = json.loads(value)
                    if self._json_attrs_path is not None:
                        json_dict = jsonpath(json_dict, self._json_attrs_path)
                    # jsonpath will always store the result in json_dict[0]
                    # so the next line happens to work exactly as needed to
                    # find the result
                    if isinstance(json_dict, list):
                        json_dict = json_dict[0]
                    if isinstance(json_dict, dict):
                        attrs = {
                            k: json_dict[k] for k in self._json_attrs if k in json_dict
                        }
                        self._attributes = attrs
                    else:
                        _LOGGER.warning(
                            "JSON result was not a dictionary"
                            " or list with 0th element a dictionary"
                        )
                except ValueError:
                    _LOGGER.warning("REST result could not be parsed as JSON")
                    _LOGGER.debug("Erroneous JSON: %s", value)

            else:
                _LOGGER.warning("Empty reply found when expecting JSON data")

        if value is not None and self._value_template is not None:
            value = self._value_template.async_render_with_possible_json_value(
                value, None
            )

        self._state = value

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self._attributes
