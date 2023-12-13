"""Switch platform for La Marzocco espresso machines."""
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import LaMarzoccoEntity
from .lm_client import LaMarzoccoClient


@dataclass(kw_only=True)
class LaMarzoccoSwitchEntityDescription(
    SwitchEntityDescription,
):
    """Description of an La Marzocco Switch."""

    control_fn: Callable[[LaMarzoccoClient, bool], Coroutine[Any, Any, bool]]
    is_on_fn: Callable[[LaMarzoccoClient], bool]


ENTITIES: tuple[LaMarzoccoSwitchEntityDescription, ...] = (
    LaMarzoccoSwitchEntityDescription(
        key="main",
        translation_key="main",
        icon="mdi:power",
        control_fn=lambda client, state: client.set_power(state),
        is_on_fn=lambda client: client.current_status["power"],
    ),
    LaMarzoccoSwitchEntityDescription(
        key="auto_on_off",
        translation_key="auto_on_off",
        icon="mdi:alarm",
        control_fn=lambda client, state: client.set_auto_on_off_global(state),
        is_on_fn=lambda client: client.current_status["global_auto"] == "Enabled",
        entity_category=EntityCategory.CONFIG,
    ),
    LaMarzoccoSwitchEntityDescription(
        key="prebrew",
        translation_key="prebrew",
        icon="mdi:water",
        control_fn=lambda client, state: client.set_prebrew(state),
        is_on_fn=lambda client: client.current_status["enable_prebrewing"],
        entity_category=EntityCategory.CONFIG,
    ),
    LaMarzoccoSwitchEntityDescription(
        key="preinfusion",
        translation_key="preinfusion",
        icon="mdi:water",
        control_fn=lambda client, state: client.set_preinfusion(state),
        is_on_fn=lambda client: client.current_status["enable_preinfusion"],
        entity_category=EntityCategory.CONFIG,
    ),
    LaMarzoccoSwitchEntityDescription(
        key="steam_boiler_enable",
        translation_key="steam_boiler",
        icon="mdi:water-boiler",
        control_fn=lambda client, state: client.set_steam_boiler_enable(state),
        is_on_fn=lambda client: client.current_status["steam_boiler_enable"],
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up switch entities and services."""

    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities(
        LaMarzoccoSwitchEntity(coordinator, description) for description in ENTITIES
    )


class LaMarzoccoSwitchEntity(LaMarzoccoEntity, SwitchEntity):
    """Switches representing espresso machine power, prebrew, and auto on/off."""

    entity_description: LaMarzoccoSwitchEntityDescription

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn device on."""
        await self.entity_description.control_fn(self._lm_client, True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn device off."""
        await self.entity_description.control_fn(self._lm_client, False)
        self.async_write_ha_state()

    @property
    def is_on(self) -> bool:
        """Return true if device is on."""
        return self.entity_description.is_on_fn(self._lm_client)
