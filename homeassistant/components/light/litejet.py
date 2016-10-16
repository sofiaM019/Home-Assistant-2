"""A single LiteJet light."""
import logging

import homeassistant.components.litejet as litejet
from homeassistant.components.light import ATTR_BRIGHTNESS, Light

DEPENDENCIES = ['litejet']

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup lights for the LiteJet platform."""
    litejet_ = litejet.CONNECTION

    add_devices(LiteJetLight(hass, litejet_, i) for i in litejet_.loads())
    # add_devices(LiteJetScene(litejet_, i) for i in litejet_.scenes())


class LiteJetLight(Light):
    """Represents a single LiteJet light."""

    def __init__(self, hass, lj, i):
        """Initialize a LiteJet light."""
        self._hass = hass
        self._lj = lj
        self._index = i
        self._brightness = 0

        self._name = lj.get_load_name(i)

        lj.on_load_activated(i, self._on_load_changed)
        lj.on_load_deactivated(i, self._on_load_changed)

        self.update()

    def _on_load_changed(self):
        """Called on a LiteJet thread when a load's state changes."""
        _LOGGER.info("Updating due to notification for %s", self._name)
        self._hass.loop.create_task(self.async_update_ha_state(True))

    @property
    def name(self):
        """The light's name."""
        return self._name

    @property
    def brightness(self):
        """The light's brightness."""
        return self._brightness

    @property
    def is_on(self):
        """Is the light on?"""
        return self._brightness != 0

    @property
    def should_poll(self):
        """LiteJet lights do not require polling."""
        return False

    def turn_on(self, **kwargs):
        """Turn on the light."""
        # device_brightness = kwargs.get(ATTR_BRIGHTNESS, 255) / 255 * 99
        # device_rate = 5
        self._lj.activate_load(self._index)

    def turn_off(self, **kwargs):
        """Turn off the light."""
        self._lj.deactivate_load(self._index)

    def update(self):
        """Retrieve the light's brightness from the LiteJet system."""
        self._brightness = self._lj.get_load_level(self._index) / 99 * 255


class LiteJetScene(Light):
    """Represents a single LiteJet scene."""

    def __init__(self, lj, i):
        self._lj = lj
        self._index = i
        self._on = False

        self._name = "LiteJet "+str(i)+" "+lj.get_scene_name(i)

    @property
    def name(self):
        return self._name

    @property
    def is_on(self):
        return self._on

    @property
    def should_poll(self):
        return False

    def turn_on(self, **kwargs):
        self._lj.activate_scene(self._index)
        self._on = True

    def turn_off(self, **kwargs):
        self._lj.deactivate_scene(self._index)
        self._on = False

    def update(self):
        # do nothing
        return
