"""Sensor platform for Tessie integration."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_ACCESS_TOKEN,
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfLength,
    UnitOfPower,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import DOMAIN, TessieGroup
from .coordinator import TessieDataUpdateCoordinator
from .entity import TessieEntity

PARALLEL_UPDATES = 0


DESCRIPTIONS: dict[TessieGroup, tuple[SensorEntityDescription, ...]] = {
    TessieGroup.CHARGE_STATE: (
        SensorEntityDescription(
            key="usable_battery_level",
            translation_key="battery_level",
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=PERCENTAGE,
            device_class=SensorDeviceClass.BATTERY,
        ),
        SensorEntityDescription(
            key="charge_energy_added",
            translation_key="charge_energy_added",
            state_class=SensorStateClass.TOTAL_INCREASING,
            native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
            device_class=SensorDeviceClass.ENERGY,
        ),
        SensorEntityDescription(
            key="charger_power",
            translation_key="charger_power",
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfPower.KILO_WATT,
            device_class=SensorDeviceClass.POWER,
        ),
        SensorEntityDescription(
            key="charger_voltage",
            translation_key="charger_voltage",
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfElectricPotential.VOLT,
            device_class=SensorDeviceClass.VOLTAGE,
        ),
        SensorEntityDescription(
            key="charger_actual_current",
            translation_key="charger_current",
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
            device_class=SensorDeviceClass.CURRENT,
        ),
        SensorEntityDescription(
            key="charge_rate",
            translation_key="charge_rate",
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfSpeed.MILES_PER_HOUR,
            device_class=SensorDeviceClass.SPEED,
        ),
        SensorEntityDescription(
            key="battery_range",
            translation_key="battery_range",
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfLength.MILES,
            device_class=SensorDeviceClass.DISTANCE,
        ),
    ),
    TessieGroup.DRIVE_STATE: (
        SensorEntityDescription(
            key="speed",
            translation_key="speed",
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfSpeed.MILES_PER_HOUR,
            device_class=SensorDeviceClass.SPEED,
        ),
        SensorEntityDescription(
            key="power",
            translation_key="power",
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfPower.KILO_WATT,
            device_class=SensorDeviceClass.POWER,
        ),
        SensorEntityDescription(
            key="shift_state",
            translation_key="shift_state",
            icon="mdi:car-shift-pattern",
            options=["P", "D", "R", "N"],
            device_class=SensorDeviceClass.ENUM,
        ),
    ),
    TessieGroup.VEHICLE_STATE: (
        SensorEntityDescription(
            key="odometer",
            translation_key="odometer",
            state_class=SensorStateClass.TOTAL_INCREASING,
            native_unit_of_measurement=UnitOfLength.MILES,
            device_class=SensorDeviceClass.DISTANCE,
        ),
        SensorEntityDescription(
            key="tpms_pressure_fl",
            translation_key="tpms_pressure_fl",
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfPressure.BAR,
            suggested_unit_of_measurement=UnitOfPressure.PSI,
            device_class=SensorDeviceClass.PRESSURE,
        ),
        SensorEntityDescription(
            key="tpms_pressure_fr",
            translation_key="tpms_pressure_fr",
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfPressure.BAR,
            suggested_unit_of_measurement=UnitOfPressure.PSI,
            device_class=SensorDeviceClass.PRESSURE,
        ),
        SensorEntityDescription(
            key="tpms_pressure_rl",
            translation_key="tpms_pressure_rl",
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfPressure.BAR,
            suggested_unit_of_measurement=UnitOfPressure.PSI,
            device_class=SensorDeviceClass.PRESSURE,
        ),
        SensorEntityDescription(
            key="tpms_pressure_rr",
            translation_key="tpms_pressure_rr",
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfPressure.BAR,
            suggested_unit_of_measurement=UnitOfPressure.PSI,
            device_class=SensorDeviceClass.PRESSURE,
        ),
    ),
    TessieGroup.CLIMATE_STATE: (
        SensorEntityDescription(
            key="inside_temp",
            translation_key="inside_temp",
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            device_class=SensorDeviceClass.TEMPERATURE,
        ),
        SensorEntityDescription(
            key="outside_temp",
            translation_key="outside_temp",
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            device_class=SensorDeviceClass.TEMPERATURE,
        ),
        SensorEntityDescription(
            key="driver_temp_setting",
            translation_key="driver_temp_setting",
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            device_class=SensorDeviceClass.TEMPERATURE,
        ),
        SensorEntityDescription(
            key="passenger_temp_setting",
            translation_key="passenger_temp_setting",
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            device_class=SensorDeviceClass.TEMPERATURE,
        ),
    ),
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Tessie sensor platform from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    api_key = entry.data[CONF_ACCESS_TOKEN]

    async_add_entities(
        [
            TessieSensorEntity(api_key, coordinator, vin, category, description)
            for vin, vehicle in coordinator.data.items()
            for category, descriptions in DESCRIPTIONS.items()
            if category in vehicle
            for description in descriptions
            if description.key in vehicle[category]
        ]
    )


class TessieSensorEntity(TessieEntity, SensorEntity):
    """Base class for Tessie metric sensors."""

    entity_description: SensorEntityDescription

    def __init__(
        self,
        api_key: str,
        coordinator: TessieDataUpdateCoordinator,
        vin: str,
        category: str,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(api_key, coordinator, vin, category, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        return self.get()
