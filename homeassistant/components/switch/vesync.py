"""
Support for Etekcity VeSync switches.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/switch.vesync/
"""
import logging
import voluptuous as vol
from homeassistant.components.switch import (SwitchDevice, PLATFORM_SCHEMA)
from homeassistant.const import (CONF_USERNAME, CONF_PASSWORD)
import homeassistant.helpers.config_validation as cv


REQUIREMENTS = ['pyvesync==0.1.1']

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the VeSync switch platform."""
    from pyvesync.vesync import VeSync

    switches = []

    try:
        manager = VeSync(config.get(CONF_USERNAME), config.get(CONF_PASSWORD))
    except ValueError:
        _LOGGER.error("Unable to setup VeSync platform")
    else:
        if manager.login():
            manager.update()

            if manager.devices is not None and manager.devices:

                if len(manager.devices) == 1:
                    count_string = 'switch'
                else:
                    count_string = 'switches'

                _LOGGER.info("Discovered %d VeSync %s",
                             len(manager.devices), count_string)

                for switch in manager.devices:
                    switches.append(VeSyncSwitchHA(switch))
                    _LOGGER.info("Added a VeSync switch named '%s'",
                                 switch.device_name)
            else:
                _LOGGER.info("No VeSync devices found")
        else:
            _LOGGER.info("Unable to login to VeSync")

    add_devices(switches)


class VeSyncSwitchHA(SwitchDevice):
    """Representation of a VeSync switch."""

    def __init__(self, plug):
        """Initialize the VeSync switch device."""
        self.smartplug = plug

    @property
    def unique_id(self):
        """Return the ID of this switch."""
        return self.smartplug.cid

    @property
    def name(self):
        """Return the name of the switch."""
        return self.smartplug.device_name

    @property
    def current_power_w(self):
        """Return the current power usage in W."""
        return self.smartplug.get_power()

    @property
    def today_energy_kwh(self):
        """Return the today total energy usage in kWh."""
        return self.smartplug.get_kwh_today()

    @property
    def available(self) -> bool:
        """Return True if switch is available."""
        return bool(self.smartplug.connection_status == "online")

    @property
    def is_on(self):
        """Return True if switch is on."""
        return bool(self.smartplug.device_status == "on")

    def turn_on(self, **kwargs):
        """Turn the switch on."""
        self.smartplug.turn_on()

    def turn_off(self, **kwargs):
        """Turn the switch off."""
        self.smartplug.turn_off()

    def update(self):
        """Handle data changes for node values."""
        self.smartplug.update()
