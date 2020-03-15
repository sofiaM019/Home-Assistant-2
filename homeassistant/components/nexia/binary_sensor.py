"""Support for Nexia / Trane XL Thermostats."""

from homeassistant.components.binary_sensor import BinarySensorDevice
from homeassistant.const import ATTR_ATTRIBUTION

from .const import (
    ATTR_FIRMWARE,
    ATTR_MODEL,
    ATTR_THERMOSTAT_ID,
    ATTR_THERMOSTAT_NAME,
    ATTRIBUTION,
    DATA_NEXIA,
    NEXIA_DEVICE,
    UPDATE_COORDINATOR,
)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up sensors for a Nexia device."""

    nexia_data = hass.data[config_entry.entry_id][DATA_NEXIA]

    entities = await hass.async_add_executor_job(_generate_entities(nexia_data))

    async_add_entities(entities, True)


def _generate_entities(nexia_data):
    """Generate sensor for a Nexia device."""

    nexia_home = nexia_data[NEXIA_DEVICE]
    coordinator = nexia_data[UPDATE_COORDINATOR]

    entities = []
    for thermostat_id in nexia_home.get_thermostat_ids():
        thermostat = nexia_home.get_thermostat_by_id(thermostat_id)
        entities.append(
            NexiaBinarySensor(
                coordinator, thermostat, "is_blower_active", "Blower Active", None
            )
        )
        if thermostat.has_emergency_heat():
            entities.append(
                NexiaBinarySensor(
                    coordinator,
                    thermostat,
                    "is_emergency_heat_active",
                    "Emergency Heat Active",
                    None,
                )
            )

    return entities


class NexiaBinarySensor(BinarySensorDevice):
    """Provices Nexia BinarySensor support."""

    def __init__(self, coordinator, device, sensor_call, sensor_name, sensor_class):
        """Initialize the Ecobee sensor."""
        self._coordinator = coordinator
        self._device = device
        self._name = self._device.get_name() + " " + sensor_name
        self._call = sensor_call
        self._unique_id = f"{self._device.thermostat_id}_{sensor_call}"
        self._state = None
        self._device_class = sensor_class

    @property
    def unique_id(self):
        """Return the unique id of the binary sensor."""
        return self._unique_id

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def device_state_attributes(self):
        """Return the device specific state attributes."""
        return {
            ATTR_ATTRIBUTION: ATTRIBUTION,
            ATTR_MODEL: self._device.get_model(),
            ATTR_FIRMWARE: self._device.get_firmware(),
            ATTR_THERMOSTAT_NAME: self._device.get_name(),
            ATTR_THERMOSTAT_ID: self._device.thermostat_id,
        }

    @property
    def is_on(self):
        """Return the status of the sensor."""
        return getattr(self._device, self._call)()

    @property
    def device_class(self):
        """Return the class of this sensor, from DEVICE_CLASSES."""
        return self._device_class

    @property
    def should_poll(self):
        """Update are handled by the coordinator."""
        return False

    @property
    def available(self):
        """Return True if entity is available."""
        return self._coordinator.last_update_success

    async def async_added_to_hass(self):
        """Subscribe to updates."""
        self._coordinator.async_add_listener(self.async_write_ha_state)

    async def async_will_remove_from_hass(self):
        """Undo subscription."""
        self._coordinator.async_remove_listener(self.async_write_ha_state)
