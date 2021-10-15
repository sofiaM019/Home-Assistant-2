"""Support for reading vehicle status from BMW connected drive portal."""
from __future__ import annotations

from dataclasses import dataclass
import logging

from bimmer_connected.const import SERVICE_ALL_TRIPS, SERVICE_LAST_TRIP, SERVICE_STATUS
from bimmer_connected.state import ChargingState

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.const import (
    CONF_UNIT_SYSTEM_IMPERIAL,
    DEVICE_CLASS_TIMESTAMP,
    ENERGY_KILO_WATT_HOUR,
    ENERGY_WATT_HOUR,
    LENGTH_KILOMETERS,
    LENGTH_MILES,
    MASS_KILOGRAMS,
    PERCENTAGE,
    TIME_HOURS,
    TIME_MINUTES,
    VOLUME_GALLONS,
    VOLUME_LITERS,
)
from homeassistant.helpers.icon import icon_for_battery_level
import homeassistant.util.dt as dt_util

from . import DOMAIN as BMW_DOMAIN, BMWConnectedDriveBaseEntity
from .const import CONF_ACCOUNT, DATA_ENTRIES

_LOGGER = logging.getLogger(__name__)


@dataclass
class BMWSensorEntityDescription(SensorEntityDescription):
    """Describes BMW sensor entity."""

    unit_metric: str | None = None
    unit_imperial: str | None = None


SENSOR_TYPES: dict[str, BMWSensorEntityDescription] = {
    # --- Generic ---
    "charging_time_remaining": BMWSensorEntityDescription(
        key="charging_time_remaining",
        icon="mdi:update",
        device_class=None,
        unit_metric=TIME_HOURS,
        unit_imperial=TIME_HOURS,
        entity_registry_enabled_default=True,
    ),
    "charging_status": BMWSensorEntityDescription(
        key="charging_status",
        icon="mdi:battery-charging",
        device_class=None,
        unit_metric=None,
        unit_imperial=None,
        entity_registry_enabled_default=True,
    ),
    # No icon as this is dealt with directly as a special case in icon()
    "charging_level_hv": BMWSensorEntityDescription(
        key="charging_level_hv",
        icon=None,
        device_class=None,
        unit_metric=PERCENTAGE,
        unit_imperial=PERCENTAGE,
        entity_registry_enabled_default=True,
    ),
    # LastTrip attributes
    "date_utc": BMWSensorEntityDescription(
        key="date_utc",
        icon=None,
        device_class=DEVICE_CLASS_TIMESTAMP,
        unit_metric=None,
        unit_imperial=None,
        entity_registry_enabled_default=True,
    ),
    "duration": BMWSensorEntityDescription(
        key="duration",
        icon="mdi:timer-outline",
        device_class=None,
        unit_metric=TIME_MINUTES,
        unit_imperial=TIME_MINUTES,
        entity_registry_enabled_default=True,
    ),
    "electric_distance_ratio": BMWSensorEntityDescription(
        key="electric_distance_ratio",
        icon="mdi:percent-outline",
        device_class=None,
        unit_metric=PERCENTAGE,
        unit_imperial=PERCENTAGE,
        entity_registry_enabled_default=False,
    ),
    # AllTrips attributes
    "battery_size_max": BMWSensorEntityDescription(
        key="battery_size_max",
        icon="mdi:battery-charging-high",
        device_class=None,
        unit_metric=ENERGY_WATT_HOUR,
        unit_imperial=ENERGY_WATT_HOUR,
        entity_registry_enabled_default=False,
    ),
    "reset_date_utc": BMWSensorEntityDescription(
        key="reset_date_utc",
        icon=None,
        device_class=DEVICE_CLASS_TIMESTAMP,
        unit_metric=None,
        unit_imperial=None,
        entity_registry_enabled_default=False,
    ),
    "saved_co2": BMWSensorEntityDescription(
        key="saved_co2",
        icon="mdi:tree-outline",
        device_class=None,
        unit_metric=MASS_KILOGRAMS,
        unit_imperial=MASS_KILOGRAMS,
        entity_registry_enabled_default=False,
    ),
    "saved_co2_green_energy": BMWSensorEntityDescription(
        key="saved_co2_green_energy",
        icon="mdi:tree-outline",
        device_class=None,
        unit_metric=MASS_KILOGRAMS,
        unit_imperial=MASS_KILOGRAMS,
        entity_registry_enabled_default=False,
    ),
    # --- Specific ---
    "mileage": BMWSensorEntityDescription(
        key="mileage",
        icon="mdi:speedometer",
        device_class=None,
        unit_metric=LENGTH_KILOMETERS,
        unit_imperial=LENGTH_MILES,
        entity_registry_enabled_default=True,
    ),
    "remaining_range_total": BMWSensorEntityDescription(
        key="remaining_range_total",
        icon="mdi:map-marker-distance",
        device_class=None,
        unit_metric=LENGTH_KILOMETERS,
        unit_imperial=LENGTH_MILES,
        entity_registry_enabled_default=True,
    ),
    "remaining_range_electric": BMWSensorEntityDescription(
        key="remaining_range_electric",
        icon="mdi:map-marker-distance",
        device_class=None,
        unit_metric=LENGTH_KILOMETERS,
        unit_imperial=LENGTH_MILES,
        entity_registry_enabled_default=True,
    ),
    "remaining_range_fuel": BMWSensorEntityDescription(
        key="remaining_range_fuel",
        icon="mdi:map-marker-distance",
        device_class=None,
        unit_metric=LENGTH_KILOMETERS,
        unit_imperial=LENGTH_MILES,
        entity_registry_enabled_default=True,
    ),
    "max_range_electric": BMWSensorEntityDescription(
        key="max_range_electric",
        icon="mdi:map-marker-distance",
        device_class=None,
        unit_metric=LENGTH_KILOMETERS,
        unit_imperial=LENGTH_MILES,
        entity_registry_enabled_default=True,
    ),
    "remaining_fuel": BMWSensorEntityDescription(
        key="remaining_fuel",
        icon="mdi:gas-station",
        device_class=None,
        unit_metric=VOLUME_LITERS,
        unit_imperial=VOLUME_GALLONS,
        entity_registry_enabled_default=True,
    ),
    # LastTrip attributes
    "average_combined_consumption": BMWSensorEntityDescription(
        key="average_combined_consumption",
        icon="mdi:flash",
        device_class=None,
        unit_metric=f"{ENERGY_KILO_WATT_HOUR}/100{LENGTH_KILOMETERS}",
        unit_imperial=f"{ENERGY_KILO_WATT_HOUR}/100{LENGTH_MILES}",
        entity_registry_enabled_default=True,
    ),
    "average_electric_consumption": BMWSensorEntityDescription(
        key="average_electric_consumption",
        icon="mdi:power-plug-outline",
        device_class=None,
        unit_metric=f"{ENERGY_KILO_WATT_HOUR}/100{LENGTH_KILOMETERS}",
        unit_imperial=f"{ENERGY_KILO_WATT_HOUR}/100{LENGTH_MILES}",
        entity_registry_enabled_default=True,
    ),
    "average_recuperation": BMWSensorEntityDescription(
        key="average_recuperation",
        icon="mdi:recycle-variant",
        device_class=None,
        unit_metric=f"{ENERGY_KILO_WATT_HOUR}/100{LENGTH_KILOMETERS}",
        unit_imperial=f"{ENERGY_KILO_WATT_HOUR}/100{LENGTH_MILES}",
        entity_registry_enabled_default=True,
    ),
    "electric_distance": BMWSensorEntityDescription(
        key="electric_distance",
        icon="mdi:map-marker-distance",
        device_class=None,
        unit_metric=LENGTH_KILOMETERS,
        unit_imperial=LENGTH_MILES,
        entity_registry_enabled_default=True,
    ),
    "saved_fuel": BMWSensorEntityDescription(
        key="saved_fuel",
        icon="mdi:fuel",
        device_class=None,
        unit_metric=VOLUME_LITERS,
        unit_imperial=VOLUME_GALLONS,
        entity_registry_enabled_default=False,
    ),
    "total_distance": BMWSensorEntityDescription(
        key="total_distance",
        icon="mdi:map-marker-distance",
        device_class=None,
        unit_metric=LENGTH_KILOMETERS,
        unit_imperial=LENGTH_MILES,
        entity_registry_enabled_default=True,
    ),
    # AllTrips attributes
    "average_combined_consumption_community_average": BMWSensorEntityDescription(
        key="average_combined_consumption_community_average",
        icon="mdi:flash",
        device_class=None,
        unit_metric=f"{ENERGY_KILO_WATT_HOUR}/100{LENGTH_KILOMETERS}",
        unit_imperial=f"{ENERGY_KILO_WATT_HOUR}/100{LENGTH_MILES}",
        entity_registry_enabled_default=False,
    ),
    "average_combined_consumption_community_high": BMWSensorEntityDescription(
        key="average_combined_consumption_community_high",
        icon="mdi:flash",
        device_class=None,
        unit_metric=f"{ENERGY_KILO_WATT_HOUR}/100{LENGTH_KILOMETERS}",
        unit_imperial=f"{ENERGY_KILO_WATT_HOUR}/100{LENGTH_MILES}",
        entity_registry_enabled_default=False,
    ),
    "average_combined_consumption_community_low": BMWSensorEntityDescription(
        key="average_combined_consumption_community_low",
        icon="mdi:flash",
        device_class=None,
        unit_metric=f"{ENERGY_KILO_WATT_HOUR}/100{LENGTH_KILOMETERS}",
        unit_imperial=f"{ENERGY_KILO_WATT_HOUR}/100{LENGTH_MILES}",
        entity_registry_enabled_default=False,
    ),
    "average_combined_consumption_user_average": BMWSensorEntityDescription(
        key="average_combined_consumption_user_average",
        icon="mdi:flash",
        device_class=None,
        unit_metric=f"{ENERGY_KILO_WATT_HOUR}/100{LENGTH_KILOMETERS}",
        unit_imperial=f"{ENERGY_KILO_WATT_HOUR}/100{LENGTH_MILES}",
        entity_registry_enabled_default=True,
    ),
    "average_electric_consumption_community_average": BMWSensorEntityDescription(
        key="average_electric_consumption_community_average",
        icon="mdi:power-plug-outline",
        device_class=None,
        unit_metric=f"{ENERGY_KILO_WATT_HOUR}/100{LENGTH_KILOMETERS}",
        unit_imperial=f"{ENERGY_KILO_WATT_HOUR}/100{LENGTH_MILES}",
        entity_registry_enabled_default=False,
    ),
    "average_electric_consumption_community_high": BMWSensorEntityDescription(
        key="average_electric_consumption_community_high",
        icon="mdi:power-plug-outline",
        device_class=None,
        unit_metric=f"{ENERGY_KILO_WATT_HOUR}/100{LENGTH_KILOMETERS}",
        unit_imperial=f"{ENERGY_KILO_WATT_HOUR}/100{LENGTH_MILES}",
        entity_registry_enabled_default=False,
    ),
    "average_electric_consumption_community_low": BMWSensorEntityDescription(
        key="average_electric_consumption_community_low",
        icon="mdi:power-plug-outline",
        device_class=None,
        unit_metric=f"{ENERGY_KILO_WATT_HOUR}/100{LENGTH_KILOMETERS}",
        unit_imperial=f"{ENERGY_KILO_WATT_HOUR}/100{LENGTH_MILES}",
        entity_registry_enabled_default=False,
    ),
    "average_electric_consumption_user_average": BMWSensorEntityDescription(
        key="average_electric_consumption_user_average",
        icon="mdi:power-plug-outline",
        device_class=None,
        unit_metric=f"{ENERGY_KILO_WATT_HOUR}/100{LENGTH_KILOMETERS}",
        unit_imperial=f"{ENERGY_KILO_WATT_HOUR}/100{LENGTH_MILES}",
        entity_registry_enabled_default=True,
    ),
    "average_recuperation_community_average": BMWSensorEntityDescription(
        key="average_recuperation_community_average",
        icon="mdi:recycle-variant",
        device_class=None,
        unit_metric=f"{ENERGY_KILO_WATT_HOUR}/100{LENGTH_KILOMETERS}",
        unit_imperial=f"{ENERGY_KILO_WATT_HOUR}/100{LENGTH_MILES}",
        entity_registry_enabled_default=False,
    ),
    "average_recuperation_community_high": BMWSensorEntityDescription(
        key="average_recuperation_community_high",
        icon="mdi:recycle-variant",
        device_class=None,
        unit_metric=f"{ENERGY_KILO_WATT_HOUR}/100{LENGTH_KILOMETERS}",
        unit_imperial=f"{ENERGY_KILO_WATT_HOUR}/100{LENGTH_MILES}",
        entity_registry_enabled_default=False,
    ),
    "average_recuperation_community_low": BMWSensorEntityDescription(
        key="average_recuperation_community_low",
        icon="mdi:recycle-variant",
        device_class=None,
        unit_metric=f"{ENERGY_KILO_WATT_HOUR}/100{LENGTH_KILOMETERS}",
        unit_imperial=f"{ENERGY_KILO_WATT_HOUR}/100{LENGTH_MILES}",
        entity_registry_enabled_default=False,
    ),
    "average_recuperation_user_average": BMWSensorEntityDescription(
        key="average_recuperation_user_average",
        icon="mdi:recycle-variant",
        device_class=None,
        unit_metric=f"{ENERGY_KILO_WATT_HOUR}/100{LENGTH_KILOMETERS}",
        unit_imperial=f"{ENERGY_KILO_WATT_HOUR}/100{LENGTH_MILES}",
        entity_registry_enabled_default=True,
    ),
    "chargecycle_range_community_average": BMWSensorEntityDescription(
        key="chargecycle_range_community_average",
        icon="mdi:map-marker-distance",
        device_class=None,
        unit_metric=LENGTH_KILOMETERS,
        unit_imperial=LENGTH_MILES,
        entity_registry_enabled_default=False,
    ),
    "chargecycle_range_community_high": BMWSensorEntityDescription(
        key="chargecycle_range_community_high",
        icon="mdi:map-marker-distance",
        device_class=None,
        unit_metric=LENGTH_KILOMETERS,
        unit_imperial=LENGTH_MILES,
        entity_registry_enabled_default=False,
    ),
    "chargecycle_range_community_low": BMWSensorEntityDescription(
        key="chargecycle_range_community_low",
        icon="mdi:map-marker-distance",
        device_class=None,
        unit_metric=LENGTH_KILOMETERS,
        unit_imperial=LENGTH_MILES,
        entity_registry_enabled_default=False,
    ),
    "chargecycle_range_user_average": BMWSensorEntityDescription(
        key="chargecycle_range_user_average",
        icon="mdi:map-marker-distance",
        device_class=None,
        unit_metric=LENGTH_KILOMETERS,
        unit_imperial=LENGTH_MILES,
        entity_registry_enabled_default=True,
    ),
    "chargecycle_range_user_current_charge_cycle": BMWSensorEntityDescription(
        key="chargecycle_range_user_current_charge_cycle",
        icon="mdi:map-marker-distance",
        device_class=None,
        unit_metric=LENGTH_KILOMETERS,
        unit_imperial=LENGTH_MILES,
        entity_registry_enabled_default=True,
    ),
    "chargecycle_range_user_high": BMWSensorEntityDescription(
        key="chargecycle_range_user_high",
        icon="mdi:map-marker-distance",
        device_class=None,
        unit_metric=LENGTH_KILOMETERS,
        unit_imperial=LENGTH_MILES,
        entity_registry_enabled_default=True,
    ),
    "total_electric_distance_community_average": BMWSensorEntityDescription(
        key="total_electric_distance_community_average",
        icon="mdi:map-marker-distance",
        device_class=None,
        unit_metric=LENGTH_KILOMETERS,
        unit_imperial=LENGTH_MILES,
        entity_registry_enabled_default=False,
    ),
    "total_electric_distance_community_high": BMWSensorEntityDescription(
        key="total_electric_distance_community_high",
        icon="mdi:map-marker-distance",
        device_class=None,
        unit_metric=LENGTH_KILOMETERS,
        unit_imperial=LENGTH_MILES,
        entity_registry_enabled_default=False,
    ),
    "total_electric_distance_community_low": BMWSensorEntityDescription(
        key="total_electric_distance_community_low",
        icon="mdi:map-marker-distance",
        device_class=None,
        unit_metric=LENGTH_KILOMETERS,
        unit_imperial=LENGTH_MILES,
        entity_registry_enabled_default=False,
    ),
    "total_electric_distance_user_average": BMWSensorEntityDescription(
        key="total_electric_distance_user_average",
        icon="mdi:map-marker-distance",
        device_class=None,
        unit_metric=LENGTH_KILOMETERS,
        unit_imperial=LENGTH_MILES,
        entity_registry_enabled_default=False,
    ),
    "total_electric_distance_user_total": BMWSensorEntityDescription(
        key="total_electric_distance_user_total",
        icon="mdi:map-marker-distance",
        device_class=None,
        unit_metric=LENGTH_KILOMETERS,
        unit_imperial=LENGTH_MILES,
        entity_registry_enabled_default=False,
    ),
    "total_saved_fuel": BMWSensorEntityDescription(
        key="total_saved_fuel",
        icon="mdi:fuel",
        device_class=None,
        unit_metric=VOLUME_LITERS,
        unit_imperial=VOLUME_GALLONS,
        entity_registry_enabled_default=False,
    ),
}


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the BMW ConnectedDrive sensors from config entry."""
    # pylint: disable=too-many-nested-blocks
    account = hass.data[BMW_DOMAIN][DATA_ENTRIES][config_entry.entry_id][CONF_ACCOUNT]
    entities = []

    for vehicle in account.account.vehicles:
        for service in vehicle.available_state_services:
            if service == SERVICE_STATUS:
                entities.extend(
                    [
                        BMWConnectedDriveSensor(hass, account, vehicle, description)
                        for attribute_name in vehicle.drive_train_attributes
                        if attribute_name in vehicle.available_attributes
                        if (description := SENSOR_TYPES.get(attribute_name))
                    ]
                )
            if service == SERVICE_LAST_TRIP:
                entities.extend(
                    [
                        BMWConnectedDriveSensor(
                            hass, account, vehicle, description, service
                        )
                        for attribute_name in vehicle.state.last_trip.available_attributes
                        if attribute_name != "date"
                        if (description := SENSOR_TYPES.get(attribute_name))
                    ]
                )
                if "date" in vehicle.state.last_trip.available_attributes:
                    entities.append(
                        BMWConnectedDriveSensor(
                            hass, account, vehicle, SENSOR_TYPES["date_utc"], service
                        )
                    )
            if service == SERVICE_ALL_TRIPS:
                for attribute_name in vehicle.state.all_trips.available_attributes:
                    if attribute_name == "reset_date":
                        entities.append(
                            BMWConnectedDriveSensor(
                                hass,
                                account,
                                vehicle,
                                SENSOR_TYPES["reset_date_utc"],
                                service,
                            )
                        )
                    elif attribute_name in (
                        "average_combined_consumption",
                        "average_electric_consumption",
                        "average_recuperation",
                        "chargecycle_range",
                        "total_electric_distance",
                    ):
                        entities.extend(
                            [
                                BMWConnectedDriveSensor(
                                    hass,
                                    account,
                                    vehicle,
                                    SENSOR_TYPES[f"{attribute_name}_{attr}"],
                                    service,
                                )
                                for attr in (
                                    "community_average",
                                    "community_high",
                                    "community_low",
                                    "user_average",
                                )
                            ]
                        )
                        if attribute_name == "chargecycle_range":
                            entities.extend(
                                BMWConnectedDriveSensor(
                                    hass,
                                    account,
                                    vehicle,
                                    SENSOR_TYPES[f"{attribute_name}_{attr}"],
                                    service,
                                )
                                for attr in ("user_current_charge_cycle", "user_high")
                            )
                        elif attribute_name == "total_electric_distance":
                            entities.extend(
                                [
                                    BMWConnectedDriveSensor(
                                        hass,
                                        account,
                                        vehicle,
                                        SENSOR_TYPES[f"{attribute_name}_{attr}"],
                                        service,
                                    )
                                    for attr in ("user_total",)
                                ]
                            )
                    elif description := SENSOR_TYPES.get(attribute_name):
                        entities.append(
                            BMWConnectedDriveSensor(
                                hass,
                                account,
                                vehicle,
                                description,
                                service,
                            )
                        )

    async_add_entities(entities, True)


class BMWConnectedDriveSensor(BMWConnectedDriveBaseEntity, SensorEntity):
    """Representation of a BMW vehicle sensor."""

    entity_description: BMWSensorEntityDescription

    def __init__(
        self,
        hass,
        account,
        vehicle,
        description: BMWSensorEntityDescription,
        service=None,
    ):
        """Initialize BMW vehicle sensor."""
        super().__init__(account, vehicle)
        self.entity_description = description

        self._service = service
        if service:
            self._attr_name = f"{vehicle.name} {service.lower()}_{description.key}"
            self._attr_unique_id = f"{vehicle.vin}-{service.lower()}-{description.key}"
        else:
            self._attr_name = f"{vehicle.name} {description.key}"
            self._attr_unique_id = f"{vehicle.vin}-{description.key}"

        if hass.config.units.name == CONF_UNIT_SYSTEM_IMPERIAL:
            self._attr_native_unit_of_measurement = description.unit_imperial
        else:
            self._attr_native_unit_of_measurement = description.unit_metric

    def update(self) -> None:
        """Read new state data from the library."""
        _LOGGER.debug("Updating %s", self._vehicle.name)
        vehicle_state = self._vehicle.state
        sensor_key = self.entity_description.key
        if sensor_key == "charging_status":
            self._attr_native_value = getattr(vehicle_state, sensor_key).value
        elif self.unit_of_measurement == VOLUME_GALLONS:
            value = getattr(vehicle_state, sensor_key)
            value_converted = self.hass.config.units.volume(value, VOLUME_LITERS)
            self._attr_native_value = round(value_converted)
        elif self.unit_of_measurement == LENGTH_MILES:
            value = getattr(vehicle_state, sensor_key)
            value_converted = self.hass.config.units.length(value, LENGTH_KILOMETERS)
            self._attr_native_value = round(value_converted)
        elif self._service is None:
            self._attr_native_value = getattr(vehicle_state, sensor_key)
        elif self._service == SERVICE_LAST_TRIP:
            vehicle_last_trip = self._vehicle.state.last_trip
            if sensor_key == "date_utc":
                date_str = getattr(vehicle_last_trip, "date")
                self._attr_native_value = dt_util.parse_datetime(date_str).isoformat()
            else:
                self._attr_native_value = getattr(vehicle_last_trip, sensor_key)
        elif self._service == SERVICE_ALL_TRIPS:
            vehicle_all_trips = self._vehicle.state.all_trips
            for attribute in (
                "average_combined_consumption",
                "average_electric_consumption",
                "average_recuperation",
                "chargecycle_range",
                "total_electric_distance",
            ):
                if sensor_key.startswith(f"{attribute}_"):
                    attr = getattr(vehicle_all_trips, attribute)
                    sub_attr = sensor_key.replace(f"{attribute}_", "")
                    self._attr_native_value = getattr(attr, sub_attr)
                    return
            if sensor_key == "reset_date_utc":
                date_str = getattr(vehicle_all_trips, "reset_date")
                self._attr_native_value = dt_util.parse_datetime(date_str).isoformat()
            else:
                self._attr_native_value = getattr(vehicle_all_trips, sensor_key)

        vehicle_state = self._vehicle.state
        charging_state = vehicle_state.charging_status in [ChargingState.CHARGING]

        if sensor_key == "charging_level_hv":
            self._attr_icon = icon_for_battery_level(
                battery_level=vehicle_state.charging_level_hv, charging=charging_state
            )
