"""Climate platform for homewizard_climate."""
import time

from homewizard_climate_websocket.model.climate_device_state import (
    HomeWizardClimateDeviceState,
)
from homewizard_climate_websocket.ws.hw_websocket import HomeWizardClimateWebSocket

from homeassistant.components.climate import (
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
    FAN_OFF,
    FAN_ON,
    SWING_HORIZONTAL,
    SWING_OFF,
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, TEMP_CELSIUS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Todo."""
    print(f"async_setup_entry: {hass.data[DOMAIN][entry.entry_id]}")
    websockets = hass.data[DOMAIN][entry.entry_id]["websockets"]
    entities = [HomeWizardClimateEntity(ws, hass) for ws in websockets]
    print(entities)
    async_add_entities(entities)


class HomeWizardClimateEntity(ClimateEntity):
    """Todo."""

    def __init__(
        self, device_web_socket: HomeWizardClimateWebSocket, hass: HomeAssistant
    ) -> None:
        """Todo."""
        self._device_web_socket = device_web_socket
        self._device_web_socket.set_on_state_change(self.on_device_state_change)
        self._hass = hass

    @property
    def unique_id(self) -> str:
        """Return unique ID for this device."""
        return f"{self._device_web_socket.device.type}_{self._device_web_socket.device.identifier}"

    @property
    def current_temperature(self) -> int:
        """Return the current temperature."""
        return self._device_web_socket.last_state.current_temperature

    @property
    def name(self) -> str:
        """Return the name of the climate device."""
        return self._device_web_socket.device.name

    @property
    def fan_mode(self):
        """Return fan mode of the AC this group belongs to."""
        return FAN_ON

    @property
    def fan_modes(self):
        """Return the list of available fan modes."""
        return [FAN_ON, FAN_OFF, FAN_LOW, FAN_MEDIUM, FAN_HIGH]

    @property
    def supported_features(self) -> ClimateEntityFeature:
        """Todo."""
        return (
            ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.FAN_MODE
            | ClimateEntityFeature.SWING_MODE
        )

    @property
    def swing_modes(self) -> list[str]:
        """Todo."""
        return [SWING_HORIZONTAL, SWING_OFF]

    @property
    def swing_mode(self) -> str:
        """Todo."""
        return (
            SWING_HORIZONTAL
            if self._device_web_socket.last_state.oscillate
            else SWING_OFF
        )

    @property
    def hvac_mode(self):
        """Return hvac target hvac state."""
        if self._device_web_socket.last_state.power_on:
            result = (
                HVACMode.HEAT
                if self._device_web_socket.last_state.heater
                else HVACMode.COOL
            )
        else:
            result = HVACMode.OFF

        print(f"Got HVAC: {result}")
        return result

    @property
    def hvac_modes(self):
        """Return the list of available operation modes."""
        return [HVACMode.HEAT, HVACMode.COOL, HVACMode.OFF]

    @property
    def temperature_unit(self):
        """Todo."""
        return TEMP_CELSIUS

    @property
    def target_temperature_step(self) -> float:
        """Todo."""
        return 1

    @property
    def target_temperature_high(self) -> float:
        """Todo."""
        return 30

    @property
    def target_temperature_low(self) -> float:
        """Todo."""
        return 14

    @property
    def min_temp(self) -> float:
        """Todo."""
        return self.target_temperature_low

    @property
    def max_temp(self) -> float:
        """Todo."""
        return self.target_temperature_high

    @property
    def target_temperature(self) -> float:
        """Todo."""
        return self._device_web_socket.last_state.target_temperature

    def set_temperature(self, **kwargs) -> None:
        """Todo."""
        print(kwargs)
        self._device_web_socket.set_target_temperature(
            int(kwargs.get(ATTR_TEMPERATURE, "0"))
        )

    def set_humidity(self, humidity: int) -> None:
        """Todo."""
        raise NotImplementedError()

    def set_fan_mode(self, fan_mode: str) -> None:
        """Todo."""
        if fan_mode == FAN_ON:
            self._device_web_socket.turn_on()
        elif fan_mode == FAN_OFF:
            self._device_web_socket.turn_off()
        elif fan_mode == FAN_LOW:
            self._device_web_socket.set_fan_speed(1)
        elif fan_mode == FAN_MEDIUM:
            speed = 4 if self.hvac_mode == HVACMode.COOL else 2
            self._device_web_socket.set_fan_speed(speed)
        elif fan_mode == FAN_HIGH:
            speed = 8 if self.hvac_mode == HVACMode.COOL else 4
            self._device_web_socket.set_fan_speed(speed)

    def set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Todo."""
        print(hvac_mode)
        if hvac_mode == HVACMode.HEAT:
            if not self._device_web_socket.last_state.power_on:
                self._device_web_socket.turn_on()
                time.sleep(1)
            if not self._device_web_socket.last_state.heater:
                self._device_web_socket.turn_on_heater()
        elif hvac_mode == HVACMode.OFF:
            self._device_web_socket.turn_off()
        else:
            if not self._device_web_socket.last_state.power_on:
                self._device_web_socket.turn_on()
                time.sleep(1)
            if self._device_web_socket.last_state.heater:
                self._device_web_socket.turn_on_cooler()

    def turn_on(self) -> None:
        """Todo."""
        self._device_web_socket.turn_on()

    def turn_off(self) -> None:
        """Todo."""
        self._device_web_socket.turn_off()

    def set_swing_mode(self, swing_mode: str) -> None:
        """Todo."""
        if swing_mode == SWING_HORIZONTAL:
            self._device_web_socket.turn_on_oscillation()
        else:
            self._device_web_socket.turn_off_oscillation()

    def set_preset_mode(self, preset_mode: str) -> None:
        """Todo."""

    def turn_aux_heat_on(self) -> None:
        """Todo."""

    def turn_aux_heat_off(self) -> None:
        """Todo."""

    def on_device_state_change(self, state: HomeWizardClimateDeviceState):
        """Todo."""
        print(f"State update to: {state}")
        self._hass.add_job(self.async_write_ha_state)
