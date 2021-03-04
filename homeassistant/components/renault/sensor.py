"""Support for Renault sensors."""
from typing import List, Optional

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import LENGTH_KILOMETERS, VOLUME_LITERS
from homeassistant.helpers.typing import HomeAssistantType

from .const import DOMAIN
from .renault_entities import RenaultCockpitDataEntity, RenaultDataEntity
from .renault_hub import RenaultHub
from .renault_vehicle import RenaultVehicleProxy


async def async_setup_entry(
    hass: HomeAssistantType,
    config_entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up the Renault entities from config entry."""
    proxy: RenaultHub = hass.data[DOMAIN][config_entry.unique_id]
    entities = await get_entities(proxy)
    async_add_entities(entities)


async def get_entities(proxy: RenaultHub) -> List[RenaultDataEntity]:
    """Create Renault entities for all vehicles."""
    entities = []
    for vehicle in proxy.vehicles.values():
        entities.extend(await get_vehicle_entities(vehicle))
    return entities


async def get_vehicle_entities(vehicle: RenaultVehicleProxy) -> List[RenaultDataEntity]:
    """Create Renault entities for single vehicle."""
    entities = []
    if "cockpit" in vehicle.coordinators.keys():
        entities.append(RenaultMileageSensor(vehicle, "Mileage"))
        if vehicle.details.uses_fuel():
            entities.append(RenaultFuelAutonomySensor(vehicle, "Fuel Autonomy"))
            entities.append(RenaultFuelQuantitySensor(vehicle, "Fuel Quantity"))
    return entities


class RenaultFuelAutonomySensor(RenaultCockpitDataEntity):
    """Fuel autonomy sensor."""

    @property
    def state(self) -> Optional[int]:
        """Return the state of this entity."""
        if self.data.fuelAutonomy is None:
            return None
        return round(self.data.fuelAutonomy)

    @property
    def icon(self) -> str:
        """Icon handling."""
        return "mdi:gas-station"

    @property
    def unit_of_measurement(self) -> str:
        """Return the unit of measurement of this entity."""
        return LENGTH_KILOMETERS


class RenaultFuelQuantitySensor(RenaultCockpitDataEntity):
    """Fuel quantity sensor."""

    @property
    def state(self) -> Optional[int]:
        """Return the state of this entity."""
        if self.data.fuelQuantity is None:
            return None
        return round(self.data.fuelQuantity)

    @property
    def icon(self) -> str:
        """Icon handling."""
        return "mdi:fuel"

    @property
    def unit_of_measurement(self) -> str:
        """Return the unit of measurement of this entity."""
        return VOLUME_LITERS


class RenaultMileageSensor(RenaultCockpitDataEntity):
    """Mileage sensor."""

    @property
    def state(self) -> Optional[int]:
        """Return the state of this entity."""
        if self.data.totalMileage is None:
            return None
        return round(self.data.totalMileage)

    @property
    def icon(self) -> str:
        """Icon handling."""
        return "mdi:sign-direction"

    @property
    def unit_of_measurement(self) -> str:
        """Return the unit of measurement of this entity."""
        return LENGTH_KILOMETERS
