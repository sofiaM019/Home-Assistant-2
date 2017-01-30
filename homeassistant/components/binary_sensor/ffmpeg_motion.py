"""
Provides a binary sensor which is a collection of ffmpeg tools.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/binary_sensor.ffmpeg_motion/
"""
import asyncio
import logging
import os

import voluptuous as vol

from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv
from homeassistant.components.binary_sensor import (
    BinarySensorDevice, PLATFORM_SCHEMA)
from homeassistant.components.ffmpeg import (
    FFmpegBase, DATA_FFMPEG, CONF_INPUT, CONF_EXTRA_ARGUMENTS,
    CONF_INITIAL_STATE)
from homeassistant.const import CONF_NAME

DEPENDENCIES = ['ffmpeg']

_LOGGER = logging.getLogger(__name__)

CONF_RESET = 'reset'
CONF_CHANGES = 'changes'
CONF_REPEAT = 'repeat'
CONF_REPEAT_TIME = 'repeat_time'

DEFAULT_NAME = 'FFmpeg Motion'
DEFAULT_INIT_STATE = True

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_INPUT): cv.string,
    vol.Optional(CONF_INITIAL_STATE, default=DEFAULT_INIT_STATE): cv.boolean,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_EXTRA_ARGUMENTS): cv.string,
    vol.Optional(CONF_RESET, default=10):
        vol.All(vol.Coerce(int), vol.Range(min=1)),
    vol.Optional(CONF_CHANGES, default=10):
        vol.All(vol.Coerce(float), vol.Range(min=0, max=99)),
    vol.Inclusive(CONF_REPEAT, 'repeat'):
        vol.All(vol.Coerce(int), vol.Range(min=1)),
    vol.Inclusive(CONF_REPEAT_TIME, 'repeat'):
        vol.All(vol.Coerce(int), vol.Range(min=1)),
})


@asyncio.coroutine
def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    """Create the binary sensor."""
    manager = hass.data[DATA_FFMPEG]

    # check source
    if not manager.async_run_test(config.get(CONF_INPUT)):
        return

    # generate sensor object
    entity = FFmpegMotion(hass, manager, config)

    # add to system
    manager.async_register_device(entity)
    yield from async_add_devices([entity])


class FFmpegBinarySensor(FFmpegBase, BinarySensorDevice):
    """A binary sensor which use ffmpeg for noise detection."""

    def __init__(self, hass, config):
        """Constructor for binary sensor noise detection."""
        self._state = False
        self._config = config
        self._name = config.get(CONF_NAME)
        self.initial_state = config.get(CONF_INITIAL_STATE)

    @callback
    def _async_callback(self, state):
        """HA-FFmpeg callback for noise detection."""
        self._state = state
        self.hass.async_add_job(self.async_update_ha_state())

    @property
    def is_on(self):
        """True if the binary sensor is on."""
        return self._state

    @property
    def name(self):
        """Return the name of the entity."""
        return self._name


class FFmpegMotion(FFmpegBinarySensor):
    """A binary sensor which use ffmpeg for noise detection."""

    def __init__(self, hass, manager, config):
        """Initialize ffmpeg motion binary sensor."""
        from haffmpeg import SensorMotion

        super().__init__(hass, config)
        self.ffmpeg = SensorMotion(
            manager.binary, hass.loop, self._async_callback)

    def async_start_ffmpeg(self):
        """Start a FFmpeg instance.

        This method must be run in the event loop and returns a coroutine.
        """
        # init config
        self.ffmpeg.set_options(
            time_reset=self._config.get(CONF_RESET),
            time_repeat=self._config.get(CONF_REPEAT_TIME, 0),
            repeat=self._config.get(CONF_REPEAT, 0),
            changes=self._config.get(CONF_CHANGES),
        )

        # run
        return self.ffmpeg.open_sensor(
            input_source=self._config.get(CONF_INPUT),
            extra_cmd=self._config.get(CONF_EXTRA_ARGUMENTS),
        )

    @property
    def sensor_class(self):
        """Return the class of this sensor, from SENSOR_CLASSES."""
        return "motion"
