"""The Meater Temperature Probe integration."""
from enum import Enum

from homeassistant.const import DEVICE_CLASS_TEMPERATURE, TEMP_CELSIUS
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Meater Temperature Probe sensor."""
    return True


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the entry."""
    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        "coordinator"
    ]

    @callback
    def async_update_data():
        """Handle updated data from the API endpoint."""
        if not coordinator.last_update_success:
            return

        # Populate the entities
        devices = coordinator.data

        entities = []

        for dev in devices:
            if dev.id not in hass.data[DOMAIN]["entities"]:
                entities.append(
                    MeaterProbeTemperature(
                        coordinator, dev.id, TemperatureMeasurement.Internal
                    )
                )
                entities.append(
                    MeaterProbeTemperature(
                        coordinator, dev.id, TemperatureMeasurement.Ambient
                    )
                )
                hass.data[DOMAIN]["entities"][dev.id] = None

        async_add_entities(entities)

        return devices

    # Add a subscriber to the coordinator to discover new temperature probes
    coordinator.async_add_listener(async_update_data)


class MeaterProbeTemperature(CoordinatorEntity):
    """Meater Temperature Sensor Entity."""

    _attr_device_class = DEVICE_CLASS_TEMPERATURE
    _attr_unit_of_measurement = TEMP_CELSIUS

    def __init__(self, coordinator, device_id, temperature_reading_type):
        """Initialise the sensor."""
        super().__init__(coordinator)
        self._attr_name = f"Meater Probe {temperature_reading_type.name}"
        self._attr_device_info = {
            "identifiers": {
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, device_id)
            },
            "manufacturer": "Apption Labs",
            "model": "Meater Probe",
            "name": f"Meater Probe {device_id}",
        }
        self._attr_unique_id = f"{device_id}-{temperature_reading_type}"

        self.device_id = device_id
        self.temperature_reading_type = temperature_reading_type

    @property
    def state(self):
        """Return the temperature of the probe."""
        # First find the right probe in the collection
        device = None

        for dev in self.coordinator.data:
            if dev.id == self.device_id:
                device = dev

        if device is None:
            return None

        if TemperatureMeasurement.Internal == self.temperature_reading_type:
            return device.internal_temperature

        # Not an internal temperature, must be ambient
        return device.ambient_temperature

    @property
    def available(self):
        """Return if entity is available."""
        # See if the device was returned from the API. If not, it's offline
        return self.coordinator.last_update_success and any(
            self.device_id == device.id for device in self.coordinator.data
        )


class TemperatureMeasurement(Enum):
    """Enumeration of possible temperature readings from the probe."""

    Internal = 1
    Ambient = 2
