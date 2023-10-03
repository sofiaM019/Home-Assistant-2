"""Code to handle a Livisi shutters."""
from __future__ import annotations

from typing import Any
import uuid

from homeassistant.components.cover import CoverEntity, CoverEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, LIVISI_STATE_CHANGE, LOGGER, SHUTTER_DEVICE_TYPE
from .coordinator import LivisiDataUpdateCoordinator
from .entity import LivisiEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up switch device."""
    coordinator: LivisiDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    @callback
    def handle_coordinator_update() -> None:
        """Add cover."""
        shc_devices: list[dict[str, Any]] = coordinator.data
        entities: list[CoverEntity] = []
        for device in shc_devices:
            if (
                device["type"] == SHUTTER_DEVICE_TYPE
                and device["id"] not in coordinator.devices
            ):
                livisi_shutter: CoverEntity = LivisiShutter(
                    config_entry, coordinator, device
                )
                LOGGER.debug("Include device type: %s", device["type"])
                coordinator.devices.add(device["id"])
                entities.append(livisi_shutter)
        async_add_entities(entities)

    config_entry.async_on_unload(
        coordinator.async_add_listener(handle_coordinator_update)
    )


class LivisiShutter(LivisiEntity, CoverEntity):
    """Represents the Livisi Switch."""

    def __init__(
        self,
        config_entry: ConfigEntry,
        coordinator: LivisiDataUpdateCoordinator,
        device: dict[str, Any],
    ) -> None:
        """Initialize the Livisi switch."""
        super().__init__(config_entry, coordinator, device)
        self._attr_supported_features = (
            CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP
        )
        self._capability_id = self.capabilities["RollerShutterActuator"]

    async def send_livisi_shutter_command(self, commandtype, params) -> dict:
        """Send a generic command to the Livisi API."""
        set_state_payload: dict[str, Any] = {
            "id": uuid.uuid4().hex,
            "type": commandtype,
            "namespace": "CosipDevices.RWE",
            "target": self._capability_id,
            "params": params,
        }
        return await self.aio_livisi.async_send_authorized_request(
            "post", "action", payload=set_state_payload
        )

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the shutter."""
        open_cover_params: dict[str, Any] = {
            "rampDirection": {"type": "Constant", "value": "RampUp"}
        }
        response = await self.send_livisi_shutter_command(
            "StartRamp", open_cover_params
        )
        if response is None:
            self._attr_available = False
            raise HomeAssistantError(f"Failed to open shutter {self._attr_name}")

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the shutter."""
        close_cover_params: dict[str, Any] = {
            "rampDirection": {"type": "Constant", "value": "RampDown"}
        }
        response = await self.send_livisi_shutter_command(
            "StartRamp", close_cover_params
        )
        if response is None:
            self._attr_available = False
            raise HomeAssistantError(f"Failed to close shutter {self._attr_name}")

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop the shutter."""
        response = await self.send_livisi_shutter_command("StopRamp", {})
        if response is None:
            self._attr_available = False
            raise HomeAssistantError(f"Failed to close shutter {self._attr_name}")

    @property
    def is_closed(self) -> bool | None:
        """Return if the cover is closed."""
        # if self._ads_var is not None:
        #     return self._state_dict[STATE_KEY_STATE]
        # if self._ads_var_position is not None:
        #     return self._state_dict[STATE_KEY_POSITION] == 0
        return None

    async def async_added_to_hass(self) -> None:
        """Register callbacks."""
        await super().async_added_to_hass()

        response = await self.coordinator.async_get_device_state(
            self._capability_id, "onState"
        )
        if response is None:
            # self._attr_is_on = False
            self._attr_available = False
        else:
            pass
            # self._attr_is_on = response
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{LIVISI_STATE_CHANGE}_{self._capability_id}",
                self.update_states,
            )
        )

    @callback
    def update_states(self, state: Any) -> None:
        """Update the state of the switch device."""
        # self._attr_is_on = state
        LOGGER.info("Cover update %s", state)
        self._attr_is_closed = True
        self.async_write_ha_state()
