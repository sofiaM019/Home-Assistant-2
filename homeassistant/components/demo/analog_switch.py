"""Demo platform that offers a fake analog switch."""
from homeassistant.components.analog_switch import AnalogSwitchEntity
from homeassistant.const import DEVICE_DEFAULT_NAME

from . import DOMAIN


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the demo analog switch."""
    async_add_entities(
        [
            DemoAnalogSwitch(
                "volume1",
                "volume",
                42.0,
                "mdi:volume-high",
                False,
                device_class="volume",
            ),
        ]
    )


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Demo config entry."""
    await async_setup_platform(hass, {}, async_add_entities)


class DemoAnalogSwitch(AnalogSwitchEntity):
    """Representation of a demo analog switch."""

    def __init__(self, unique_id, name, state, icon, assumed, device_class=None):
        """Initialize the Demo analog switch."""
        self._unique_id = unique_id
        self._name = name or DEVICE_DEFAULT_NAME
        self._state = state
        self._icon = icon
        self._assumed = assumed
        self._device_class = device_class

    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self.unique_id)
            },
            "name": self.name,
        }

    @property
    def unique_id(self):
        """Return the unique id."""
        return self._unique_id

    @property
    def should_poll(self):
        """No polling needed for a demo analog switch."""
        return False

    @property
    def name(self):
        """Return the name of the device if any."""
        return self._name

    @property
    def icon(self):
        """Return the icon to use for device if any."""
        return self._icon

    @property
    def assumed_state(self):
        """Return if the state is based on assumptions."""
        return self._assumed

    @property
    def state(self):
        """Return the current value."""
        return self._state

    @property
    def device_class(self):
        """Return device of entity."""
        return self._device_class

    async def async_set_value(self, value):
        """Update the current value."""
        self._state = value
        self.async_write_ha_state()
