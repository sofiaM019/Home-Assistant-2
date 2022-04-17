"""The Compensation integration."""
import logging

from numpy.polynomial import Polynomial
import voluptuous as vol

from homeassistant.components.sensor import (
    DEVICE_CLASSES_SCHEMA,
    DOMAIN as SENSOR_DOMAIN,
)
from homeassistant.const import (
    CONF_ATTRIBUTE,
    CONF_DEVICE_CLASS,
    CONF_NAME,
    CONF_SOURCE,
    CONF_UNIQUE_ID,
    CONF_UNIT_OF_MEASUREMENT,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_COMPENSATION,
    CONF_DATAPOINTS,
    CONF_DEGREE,
    CONF_POLYNOMIAL,
    CONF_PRECISION,
    DATA_COMPENSATION,
    DEFAULT_DEGREE,
    DEFAULT_PRECISION,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


def datapoints_greater_than_degree(value: dict) -> dict:
    """Validate data point list is greater than polynomial degrees."""
    if len(value[CONF_DATAPOINTS]) <= value[CONF_DEGREE]:
        raise vol.Invalid(
            f"{CONF_DATAPOINTS} must have at least {value[CONF_DEGREE]+1} {CONF_DATAPOINTS}"
        )

    return value


COMPENSATION_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_SOURCE): cv.entity_id,
        vol.Required(CONF_DATAPOINTS): [
            vol.ExactSequence([vol.Coerce(float), vol.Coerce(float)])
        ],
        vol.Optional(CONF_UNIQUE_ID): cv.string,
        vol.Optional(CONF_ATTRIBUTE): cv.string,
        vol.Optional(CONF_PRECISION, default=DEFAULT_PRECISION): cv.positive_int,
        vol.Optional(CONF_DEGREE, default=DEFAULT_DEGREE): vol.All(
            vol.Coerce(int),
            vol.Range(min=1, max=7),
        ),
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional(CONF_DEVICE_CLASS): DEVICE_CLASSES_SCHEMA,
        vol.Optional(CONF_UNIT_OF_MEASUREMENT): cv.string,
    }
)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {cv.slug: vol.All(COMPENSATION_SCHEMA, datapoints_greater_than_degree)}
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Compensation sensor."""
    hass.data[DATA_COMPENSATION] = {}

    for compensation, conf in config[DOMAIN].items():
        _LOGGER.debug("Setup %s.%s", DOMAIN, compensation)

        degree = conf[CONF_DEGREE]

        # get x values and y values from the x,y point pairs
        x_values, y_values = zip(*conf[CONF_DATAPOINTS])

        # try to get valid coefficients for a polynomial
        polynomial = Polynomial.fit(x_values, y_values, degree, domain=[])

        if polynomial is not None:
            data = {
                k: v for k, v in conf.items() if k not in [CONF_DEGREE, CONF_DATAPOINTS]
            }
            data[CONF_POLYNOMIAL] = polynomial

            hass.data[DATA_COMPENSATION][compensation] = data

            hass.async_create_task(
                async_load_platform(
                    hass,
                    SENSOR_DOMAIN,
                    DOMAIN,
                    {CONF_COMPENSATION: compensation},
                    config,
                )
            )

    return True
