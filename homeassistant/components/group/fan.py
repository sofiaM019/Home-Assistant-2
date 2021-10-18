"""This platform allows several fans to be grouped into one fan."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components.fan import (
    ATTR_DIRECTION,
    ATTR_OSCILLATING,
    ATTR_PERCENTAGE,
    ATTR_PERCENTAGE_STEP,
    DOMAIN,
    PLATFORM_SCHEMA,
    SERVICE_SET_SPEED,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    SUPPORT_DIRECTION,
    SUPPORT_OSCILLATE,
    SUPPORT_SET_SPEED,
    FanEntity,
)
from homeassistant.const import (
    ATTR_ASSUMED_STATE,
    ATTR_ENTITY_ID,
    ATTR_SUPPORTED_FEATURES,
    CONF_ENTITIES,
    CONF_NAME,
    CONF_UNIQUE_ID,
    STATE_ON,
)
from homeassistant.core import CoreState, Event, HomeAssistant, State
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.typing import ConfigType

from . import GroupEntity
from .util import (
    attribute_equal,
    most_frequent_attribute,
    reduce_attribute,
    states_equal,
)

SUPPORTED_FLAGS = {SUPPORT_SET_SPEED, SUPPORT_DIRECTION, SUPPORT_OSCILLATE}

DEFAULT_NAME = "Fan Group"


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_ENTITIES): cv.entities_domain(DOMAIN),
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_UNIQUE_ID): cv.string,
    }
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: dict[str, Any] | None = None,
) -> None:
    """Set up the Group Cover platform."""
    async_add_entities(
        [FanGroup(config.get(CONF_UNIQUE_ID), config[CONF_NAME], config[CONF_ENTITIES])]
    )


class FanGroup(GroupEntity, FanEntity):
    """Representation of a FanGroup."""

    _attr_assumed_state: bool = True

    def __init__(self, unique_id: str | None, name: str, entities: list[str]) -> None:
        """Initialize a FanGroup entity."""
        self._entities = entities
        self._fans: dict[int, set[str]] = {flag: set() for flag in SUPPORTED_FLAGS}
        self._percentage = None
        self._oscillating = None
        self._direction = None
        self._supported_features = 0
        self._speed_count = 100
        self._is_on = False
        self._attr_name = name
        self._attr_extra_state_attributes = {ATTR_ENTITY_ID: entities}
        self._attr_unique_id = unique_id

    @property
    def supported_features(self) -> int:
        """Flag supported features."""
        return self._supported_features

    @property
    def speed_count(self) -> int:
        """Return the number of speeds the fan supports."""
        return self._speed_count

    @property
    def is_on(self) -> bool:
        """Return true if the entity is on."""
        return self._is_on

    @property
    def percentage(self) -> int | None:
        """Return the current speed as a percentage."""
        return self._percentage

    @property
    def current_direction(self) -> str | None:
        """Return the current direction of the fan."""
        return self._direction

    @property
    def oscillating(self) -> bool | None:
        """Return whether or not the fan is currently oscillating."""
        return self._oscillating

    async def _update_supported_features_event(self, event: Event) -> None:
        self.async_set_context(event.context)
        if (entity := event.data.get("entity_id")) is not None:
            await self.async_update_supported_features(
                entity, event.data.get("new_state")
            )

    async def async_update_supported_features(
        self,
        entity_id: str,
        new_state: State | None,
        update_state: bool = True,
    ) -> None:
        """Update dictionaries with supported features."""
        if not new_state:
            for values in self._fans.values():
                values.discard(entity_id)
            if update_state:
                await self.async_defer_or_update_ha_state()
            return

        features = new_state.attributes.get(ATTR_SUPPORTED_FEATURES, 0)

        for feature in SUPPORTED_FLAGS:
            if features & feature:
                self._fans[feature].add(entity_id)
            else:
                self._fans[feature].discard(entity_id)

        if update_state:
            await self.async_defer_or_update_ha_state()

    async def async_added_to_hass(self) -> None:
        """Register listeners."""
        for entity_id in self._entities:
            if (new_state := self.hass.states.get(entity_id)) is None:
                continue
            await self.async_update_supported_features(
                entity_id, new_state, update_state=False
            )
        self.async_on_remove(
            async_track_state_change_event(
                self.hass, self._entities, self._update_supported_features_event
            )
        )

        if self.hass.state == CoreState.running:
            await self.async_update()
            return
        await super().async_added_to_hass()

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed of the fan, as a percentage."""
        if percentage == 0:
            await self.async_turn_off()
        await self._async_call_supported_entities(SERVICE_SET_SPEED, SUPPORT_SET_SPEED)

    async def async_turn_on(
        self,
        speed: str | None = None,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn on the fan."""
        if percentage is not None:
            await self.async_set_percentage(percentage)
            return
        await self._async_call_all_entities(SERVICE_TURN_ON)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the fans off."""
        await self._async_call_all_entities(SERVICE_TURN_OFF)

    async def _async_call_supported_entities(
        self, service: str, support_flag: int
    ) -> None:
        """Call a service with all entities."""
        await self.hass.services.async_call(
            DOMAIN,
            service,
            {ATTR_ENTITY_ID: self._fans[support_flag]},
            blocking=True,
            context=self._context,
        )

    async def _async_call_all_entities(self, service: str) -> None:
        """Call a service with all entities."""
        await self.hass.services.async_call(
            DOMAIN,
            service,
            {ATTR_ENTITY_ID: self._entities},
            blocking=True,
            context=self._context,
        )

    async def async_update(self) -> None:
        """Update state and attributes."""
        self._attr_assumed_state = False

        all_on_states = [self.hass.states.get(x) for x in self._entities]
        on_states: list[State] = list(filter(None, all_on_states))
        self._is_on = any(state.state == STATE_ON for state in on_states)
        self._attr_assumed_state |= not states_equal(on_states)

        percentage_fans = self._fans[SUPPORT_SET_SPEED]
        all_percentage_states = [self.hass.states.get(x) for x in percentage_fans]
        percentage_states: list[State] = list(filter(None, all_percentage_states))
        self._percentage = reduce_attribute(percentage_states, ATTR_PERCENTAGE)
        self._attr_assumed_state |= not attribute_equal(
            percentage_states, ATTR_PERCENTAGE
        )
        if (
            percentage_states
            and attribute_equal(percentage_states, ATTR_PERCENTAGE_STEP)
            and percentage_states[0].attributes[ATTR_PERCENTAGE_STEP]
        ):
            self._speed_count = round(
                1 / percentage_states[0].attributes[ATTR_PERCENTAGE_STEP]
            )
        else:
            self._speed_count = 100

        oscillate_fans = self._fans[SUPPORT_OSCILLATE]
        all_oscillate_states = [self.hass.states.get(x) for x in oscillate_fans]
        oscillate_states: list[State] = list(filter(None, all_oscillate_states))
        self._oscillating = most_frequent_attribute(oscillate_states, ATTR_OSCILLATING)
        self._attr_assumed_state |= not attribute_equal(
            oscillate_states, ATTR_OSCILLATING
        )

        direction_fans = self._fans[SUPPORT_DIRECTION]
        all_direction_states = [self.hass.states.get(x) for x in direction_fans]
        direction_states: list[State] = list(filter(None, all_direction_states))
        self._direction = most_frequent_attribute(direction_states, ATTR_DIRECTION)
        self._attr_assumed_state |= not attribute_equal(
            direction_states, ATTR_DIRECTION
        )

        self._supported_features = 0
        for feature in SUPPORTED_FLAGS:
            if self._fans[feature]:
                self._supported_features |= feature

        if self._attr_assumed_state:
            return
        self._attr_assumed_state = any(
            state.attributes.get(ATTR_ASSUMED_STATE) for state in on_states
        )
