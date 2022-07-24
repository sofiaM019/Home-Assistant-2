"""Shark IQ Wrapper."""
from __future__ import annotations

from collections.abc import Iterable

from sharkiq import OperatingModes, PowerModes, Properties, SharkIqVacuum
import voluptuous as vol

from homeassistant import exceptions
from homeassistant.components.vacuum import (
    STATE_CLEANING,
    STATE_DOCKED,
    STATE_IDLE,
    STATE_PAUSED,
    STATE_RETURNING,
    StateVacuumEntity,
    VacuumEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, LOGGER, SHARK
from .update_coordinator import SharkIqUpdateCoordinator

SERVICE_CLEAN_ROOM = "clean_room"

OPERATING_STATE_MAP = {
    OperatingModes.PAUSE: STATE_PAUSED,
    OperatingModes.START: STATE_CLEANING,
    OperatingModes.STOP: STATE_IDLE,
    OperatingModes.RETURN: STATE_RETURNING,
}

FAN_SPEEDS_MAP = {
    "Eco": PowerModes.ECO,
    "Normal": PowerModes.NORMAL,
    "Max": PowerModes.MAX,
}

STATE_RECHARGING_TO_RESUME = "recharging_to_resume"

# Attributes to expose
ATTR_ERROR_CODE = "last_error_code"
ATTR_ERROR_MSG = "last_error_message"
ATTR_LOW_LIGHT = "low_light"
ATTR_RECHARGE_RESUME = "recharge_and_resume"
ATTR_AVAILABLE_ROOMS = "available_rooms"
ATTR_RSSI = "rssi"
ATTR_ROOMS = "rooms"


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Shark IQ vacuum cleaner."""
    coordinator: SharkIqUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    devices: Iterable[SharkIqVacuum] = coordinator.shark_vacs.values()
    device_names = [d.name for d in devices]
    LOGGER.debug(
        "Found %d Shark IQ device(s): %s",
        len(device_names),
        ", ".join([d.name for d in devices]),
    )
    async_add_entities([SharkVacuumEntity(d, coordinator) for d in devices])

    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        SERVICE_CLEAN_ROOM,
        {
            vol.Required("rooms"): list,
        },
        "async_clean_room",
    )

    # hass.services.register(DOMAIN, "clean_room", SharkVacuumEntity.async_clean_room)


class SharkVacuumEntity(CoordinatorEntity[SharkIqUpdateCoordinator], StateVacuumEntity):
    """Shark IQ vacuum entity."""

    _attr_fan_speed_list = list(FAN_SPEEDS_MAP)
    _attr_supported_features = (
        VacuumEntityFeature.BATTERY
        | VacuumEntityFeature.FAN_SPEED
        | VacuumEntityFeature.PAUSE
        | VacuumEntityFeature.RETURN_HOME
        | VacuumEntityFeature.START
        | VacuumEntityFeature.STATE
        | VacuumEntityFeature.STATUS
        | VacuumEntityFeature.STOP
        | VacuumEntityFeature.LOCATE
    )

    def __init__(
        self, sharkiq: SharkIqVacuum, coordinator: SharkIqUpdateCoordinator
    ) -> None:
        """Create a new SharkVacuumEntity."""
        super().__init__(coordinator)
        self.sharkiq = sharkiq
        self._attr_name = sharkiq.name
        self._attr_unique_id = sharkiq.serial_number
        self._serial_number = sharkiq.serial_number

    class InvalidRoomSelection(exceptions.HomeAssistantError):
        """Error to indicate an invalid room was included in the selection."""

    def send_command(self, command, params=None, **kwargs):
        """Send a command to the vacuum. Not yet implemented."""
        raise NotImplementedError()

    def clean_spot(self, **kwargs):
        """Spot clean an area. Not yet implemented."""
        raise NotImplementedError()

    @property
    def is_online(self) -> bool:
        """Tell us if the device is online."""
        return self.coordinator.device_is_online(self._serial_number)

    @property
    def model(self) -> str:
        """Vacuum model number."""
        if self.sharkiq.vac_model_number:
            return self.sharkiq.vac_model_number
        return self.sharkiq.oem_model_number

    @property
    def device_info(self) -> DeviceInfo:
        """Device info dictionary."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._serial_number)},
            manufacturer=SHARK,
            model=self.model,
            name=self.name,
            sw_version=self.sharkiq.get_property_value(
                Properties.ROBOT_FIRMWARE_VERSION
            ),
        )

    @property
    def error_code(self) -> int | None:
        """Return the last observed error code (or None)."""
        return self.sharkiq.error_code

    @property
    def error_message(self) -> str | None:
        """Return the last observed error message (or None)."""
        if not self.error_code:
            return None
        return self.sharkiq.error_text

    @property
    def operating_mode(self) -> str | None:
        """Operating mode."""
        op_mode = self.sharkiq.get_property_value(Properties.OPERATING_MODE)
        return OPERATING_STATE_MAP.get(op_mode)

    @property
    def recharging_to_resume(self) -> int | None:
        """Return True if vacuum set to recharge and resume cleaning."""
        return self.sharkiq.get_property_value(Properties.RECHARGING_TO_RESUME)

    @property
    def state(self):
        """
        Get the current vacuum state.

        NB: Currently, we do not return an error state because they can be very, very stale.
        In the app, these are (usually) handled by showing the robot as stopped and sending the
        user a notification.
        """
        if self.sharkiq.get_property_value(Properties.CHARGING_STATUS):
            return STATE_DOCKED
        return self.operating_mode

    @property
    def available(self) -> bool:
        """Determine if the sensor is available based on API results."""
        # If the last update was successful...
        return self.coordinator.last_update_success and self.is_online

    @property
    def battery_level(self) -> int | None:
        """Get the current battery level."""
        return self.sharkiq.get_property_value(Properties.BATTERY_CAPACITY)

    async def async_return_to_base(self, **kwargs):
        """Have the device return to base."""
        await self.sharkiq.async_set_operating_mode(OperatingModes.RETURN)
        await self.coordinator.async_refresh()

    async def async_pause(self):
        """Pause the cleaning task."""
        await self.sharkiq.async_set_operating_mode(OperatingModes.PAUSE)
        await self.coordinator.async_refresh()

    async def async_start(self):
        """Start the device."""
        await self.sharkiq.async_set_operating_mode(OperatingModes.START)
        await self.coordinator.async_refresh()

    async def async_stop(self, **kwargs):
        """Stop the device."""
        await self.sharkiq.async_set_operating_mode(OperatingModes.STOP)
        await self.coordinator.async_refresh()

    async def async_locate(self, **kwargs):
        """Cause the device to generate a loud chirp."""
        await self.sharkiq.async_find_device()

    async def async_clean_room(self, **kwargs):
        """Clean a specific room."""
        if ATTR_ROOMS in kwargs:
            all_rooms_reachable = True
            for room in kwargs.get(ATTR_ROOMS):
                if room not in self.available_rooms:
                    all_rooms_reachable = False
                    LOGGER.error("Room not reachable: %s", room)
            if all_rooms_reachable:
                LOGGER.info("Cleaning room: %s", kwargs.get(ATTR_ROOMS))
                await self.sharkiq.async_clean_rooms(kwargs.get(ATTR_ROOMS))
            else:
                LOGGER.error("Invalid room selection - service not run")
                raise self.InvalidRoomSelection(
                    "One or more of the rooms listed is not available to your vacuum.  Make sure all rooms match the Shark App including capitalization."
                )

        else:
            LOGGER.error("No target specified")
            raise self.InvalidRoomSelection

        await self.coordinator.async_refresh()

    @property
    def fan_speed(self) -> str | None:
        """Return the current fan speed."""
        fan_speed = None
        speed_level = self.sharkiq.get_property_value(Properties.POWER_MODE)
        for k, val in FAN_SPEEDS_MAP.items():
            if val == speed_level:
                fan_speed = k
        return fan_speed

    async def async_set_fan_speed(self, fan_speed: str, **kwargs):
        """Set the fan speed."""
        await self.sharkiq.async_set_property_value(
            Properties.POWER_MODE, FAN_SPEEDS_MAP.get(fan_speed.capitalize())
        )
        await self.coordinator.async_refresh()

    # Various attributes we want to expose
    @property
    def recharge_resume(self) -> bool | None:
        """Recharge and resume mode active."""
        return self.sharkiq.get_property_value(Properties.RECHARGE_RESUME)

    @property
    def rssi(self) -> int | None:
        """Get the WiFi RSSI."""
        return self.sharkiq.get_property_value(Properties.RSSI)

    @property
    def low_light(self):
        """Let us know if the robot is operating in low-light mode."""
        return self.sharkiq.get_property_value(Properties.LOW_LIGHT_MISSION)

    @property
    def available_rooms(self) -> list | None:
        """Return a list of rooms available to clean."""
        return self.sharkiq.get_room_list()

    @property
    def extra_state_attributes(self) -> dict:
        """Return a dictionary of device state attributes specific to sharkiq."""
        data = {
            ATTR_ERROR_CODE: self.error_code,
            ATTR_ERROR_MSG: self.sharkiq.error_text,
            ATTR_LOW_LIGHT: self.low_light,
            ATTR_RECHARGE_RESUME: self.recharge_resume,
            ATTR_RSSI: self.rssi,
            ATTR_ROOMS: self.available_rooms,
        }
        return data
