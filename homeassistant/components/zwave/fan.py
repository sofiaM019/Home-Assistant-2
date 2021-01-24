"""Support for Z-Wave fans."""
import math

from homeassistant.components.fan import (
    DOMAIN,
    SPEED_HIGH,
    SPEED_LOW,
    SPEED_MEDIUM,
    SPEED_OFF,
    SUPPORT_SET_SPEED,
    FanEntity,
    fan_compat,
)
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from . import ZWaveDeviceEntity

SPEED_LIST = [SPEED_OFF, SPEED_LOW, SPEED_MEDIUM, SPEED_HIGH]

SUPPORTED_FEATURES = SUPPORT_SET_SPEED

# Value will first be divided to an integer
VALUE_TO_SPEED = {0: SPEED_OFF, 1: SPEED_LOW, 2: SPEED_MEDIUM, 3: SPEED_HIGH}

SPEED_TO_VALUE = {SPEED_OFF: 0, SPEED_LOW: 1, SPEED_MEDIUM: 50, SPEED_HIGH: 99}


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Z-Wave Fan from Config Entry."""

    @callback
    def async_add_fan(fan):
        """Add Z-Wave Fan."""
        async_add_entities([fan])

    async_dispatcher_connect(hass, "zwave_new_fan", async_add_fan)


def get_device(values, **kwargs):
    """Create Z-Wave entity device."""
    return ZwaveFan(values)


class ZwaveFan(ZWaveDeviceEntity, FanEntity):
    """Representation of a Z-Wave fan."""

    def __init__(self, values):
        """Initialize the Z-Wave fan device."""
        ZWaveDeviceEntity.__init__(self, values, DOMAIN)
        self.update_properties()

    def update_properties(self):
        """Handle data changes for node values."""
        value = math.ceil(self.values.primary.data * 3 / 100)
        self._state = VALUE_TO_SPEED[value]

    def set_speed(self, speed):
        """Set the speed of the fan."""
        self.node.set_dimmer(self.values.primary.value_id, SPEED_TO_VALUE[speed])

    #
    # The fan entity model has changed to use percentages and preset_modes
    # instead of speeds.
    #
    # The @fan_compat decorator provides backwards compatibility
    # by setting the preset_mode or percentage when speed is passed in,
    # and forward compatibility by setting speed when preset_mode or
    # percentage is passed in.
    #
    # When the deprecation of the old model is completed and this
    # entity has been updated to implement `set_percentage`
    # `percentage`, `set_preset_mode`, `preset_modes`, and `preset_mode`,
    # remove the @fan_compat decorator.
    #
    @fan_compat
    def turn_on(self, speed=None, percentage=None, preset_mode=None, **kwargs):
        """Turn the device on."""
        if speed is None:
            # Value 255 tells device to return to previous value
            self.node.set_dimmer(self.values.primary.value_id, 255)
        else:
            self.set_speed(speed)

    def turn_off(self, **kwargs):
        """Turn the device off."""
        self.node.set_dimmer(self.values.primary.value_id, 0)

    @property
    def speed(self):
        """Return the current speed."""
        return self._state

    @property
    def speed_list(self):
        """Get the list of available speeds."""
        return SPEED_LIST

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORTED_FEATURES
