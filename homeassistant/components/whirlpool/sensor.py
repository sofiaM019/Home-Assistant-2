"""The Washer/Dryer Sensor for Whirlpool Appliances."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging

from whirlpool.washerdryer import MachineState, WasherDryer

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from . import WhirlpoolData
from .const import (
    CYCLE_FUNC,
    DOMAIN,
    ICON_D,
    ICON_W,
    MACHINE_STATE,
    TANK_FILL,
    WASHER_STATE,
)

_LOGGER = logging.getLogger(__name__)


def washer_state(washer: WasherDryer) -> str | None:
    """Determine correct states for a washer."""

    machine_state = washer.get_machine_state()
    machine_cycle = None
    for count, func in zip(range(len(CYCLE_FUNC)), CYCLE_FUNC):
        if func(washer):
            machine_cycle = WASHER_STATE.get(count)
            break

    if washer.get_attribute("Cavity_OpStatusDoorOpen") == "1":
        machine_cycle = "Door open"
        return machine_cycle

    if machine_state == MachineState.RunningMainCycle and machine_cycle:
        return machine_cycle

    return MACHINE_STATE.get(machine_state)


@dataclass
class WhirlpoolSensorEntityDescriptionMixin:
    """Mixin for required keys."""

    value_fn: Callable


@dataclass
class WhirlpoolSensorEntityDescription(
    SensorEntityDescription, WhirlpoolSensorEntityDescriptionMixin
):
    """Describes Whirlpool Washer sensor entity."""


SENSORS: tuple[WhirlpoolSensorEntityDescription, ...] = (
    WhirlpoolSensorEntityDescription(
        key="state",
        name="state",
        entity_registry_enabled_default=True,
        icon=ICON_W,
        has_entity_name=True,
        value_fn=washer_state,
    ),
    WhirlpoolSensorEntityDescription(
        key="timeremaining",
        name="time remaining",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="s",
        entity_registry_enabled_default=True,
        icon=ICON_W,
        has_entity_name=True,
        value_fn=lambda WasherDryer: WasherDryer.get_attribute(
            "Cavity_TimeStatusEstTimeRemaining"
        ),
    ),
    WhirlpoolSensorEntityDescription(
        key="DispenseLevel",
        name="Dispense Level",
        device_class=SensorDeviceClass.VOLUME,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=True,
        icon=ICON_W,
        has_entity_name=True,
        value_fn=lambda WasherDryer: TANK_FILL[
            WasherDryer.get_attribute("WashCavity_OpStatusBulkDispense1Level")
        ],
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Config flow entry for Whrilpool Laundry."""
    whirlpool_data: WhirlpoolData = hass.data[DOMAIN][config_entry.entry_id]
    for appliance in whirlpool_data.appliances_manager.washer_dryers:
        _wd = WasherDryer(
            whirlpool_data.backend_selector,
            whirlpool_data.auth,
            appliance["SAID"],
        )
        await _wd.connect()
        entities = [
            WasherDryerClass(
                appliance["SAID"],
                appliance["NAME"],
                description,
                _wd,
            )
            for description in SENSORS
        ]

        async_add_entities(entities)


class WasherDryerClass(SensorEntity):
    """A class for the whirlpool/maytag washer account."""

    _attr_should_poll = False

    def __init__(
        self,
        said: str,
        name: str,
        description: WhirlpoolSensorEntityDescription,
        washdry: WasherDryer,
    ) -> None:
        """Initialize the washer sensor."""
        self._name = name
        self._said = said

        self._wd: WasherDryer = washdry
        self._wd.register_attr_callback(self.async_write_ha_state)

        if self._name == "dryer":
            self._attr_icon = ICON_D
        self.entity_description: WhirlpoolSensorEntityDescription = description
        self._attr_unique_id = f"{said}-{description.key}"

    @property
    def device_info(self) -> DeviceInfo:
        """Device information for Whirlpool washer sensors."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._said)},
            name=self._name,
            manufacturer="Whirlpool",
        )

    async def async_will_remove_from_hass(self) -> None:
        """Close Whrilpool Appliance sockets before removing."""
        await self._wd.disconnect()

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._wd.get_online()

    @property
    def native_value(self) -> StateType | str:
        """Return native value of sensor."""
        return self.entity_description.value_fn(self._wd)
