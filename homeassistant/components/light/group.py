"""
This component allows several lights to be grouped into one light.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/light.group/
"""
import asyncio
import logging
import itertools
from typing import List, Tuple, Optional, Iterator, Any
from collections import Counter
from copy import deepcopy

import voluptuous as vol

from homeassistant.core import State, callback
from homeassistant.components import light
from homeassistant.const import (STATE_OFF, STATE_ON, SERVICE_TURN_ON,
                                 SERVICE_TURN_OFF, ATTR_ENTITY_ID, CONF_NAME,
                                 CONF_ENTITIES, STATE_UNAVAILABLE,
                                 STATE_UNKNOWN, EVENT_HOMEASSISTANT_START)
from homeassistant.helpers.event import async_track_state_change
from homeassistant.helpers.typing import HomeAssistantType, ConfigType
from homeassistant.components.light import (
    SUPPORT_BRIGHTNESS, SUPPORT_RGB_COLOR, SUPPORT_COLOR_TEMP,
    SUPPORT_TRANSITION, SUPPORT_EFFECT, SUPPORT_FLASH, SUPPORT_XY_COLOR,
    SUPPORT_WHITE_VALUE, PLATFORM_SCHEMA)
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'group'

DEFAULT_NAME = 'Group Light'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Required(CONF_ENTITIES): cv.entity_ids,
})

SUPPORT_GROUP_LIGHT = (SUPPORT_BRIGHTNESS | SUPPORT_COLOR_TEMP | SUPPORT_EFFECT
                       | SUPPORT_FLASH | SUPPORT_RGB_COLOR | SUPPORT_TRANSITION
                       | SUPPORT_XY_COLOR | SUPPORT_WHITE_VALUE)


async def async_setup_platform(hass: HomeAssistantType, config: ConfigType,
                               async_add_devices, discovery_info=None) -> None:
    """Initialize light.group platform."""
    async_add_devices(
        [GroupLight(hass, config.get(CONF_NAME), config[CONF_ENTITIES])])


class GroupLight(light.Light):
    """Representation of a group light."""

    def __init__(self, hass: HomeAssistantType, name: str,
                 entity_ids: List[str]) -> None:
        """Initialize a group light."""
        self.hass = hass  # type: HomeAssistantType
        self._name = name  # type: str
        self._entity_ids = entity_ids  # type: List[str]
        self._state = STATE_UNAVAILABLE  # type: str
        self._brightness = None  # type: Optional[int]
        self._xy_color = None  # type: Optional[Tuple[float, float]]
        self._rgb_color = None  # type: Optional[Tuple[int, int, int]]
        self._color_temp = None  # type: Optional[int]
        self._min_mireds = 154  # type: Optional[int]
        self._max_mireds = 500  # type: Optional[int]
        self._white_value = None  # type: Optional[int]
        self._effect_list = None  # type: Optional[List[str]]
        self._effect = None  # type: Optional[str]
        self._supported_features = 0  # type: int

    async def async_added_to_hass(self) -> None:
        """Register callbacks"""

        @callback
        def async_state_changed_listener(self, entity_id: str,
                                         old_state: State, new_state: State):
            """Handle child updates."""
            self.async_schedule_update_ha_state(True)

        @callback
        def async_homeassistant_start(event):
            """Track child state changes on startup."""
            async_track_state_change(self.hass, self._entity_ids,
                                     async_state_changed_listener)

            self.async_schedule_update_ha_state(True)

        self.hass.bus.async_listen_once(EVENT_HOMEASSISTANT_START,
                                        async_homeassistant_start)

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name

    @property
    def state(self) -> str:
        """Return the state."""
        return self._state

    @property
    def is_on(self) -> bool:
        """Return True if entity is on."""
        return self._state == STATE_ON

    @property
    def brightness(self) -> Optional[int]:
        """Return the brightness of this light between 0..255."""
        return self._brightness

    @property
    def xy_color(self) -> Optional[Tuple[float, float]]:
        """Return the XY color value [float, float]."""
        return self._xy_color

    @property
    def rgb_color(self) -> Optional[Tuple[int, int, int]]:
        """Return the RGB color value [int, int, int]."""
        return self._rgb_color

    @property
    def color_temp(self) -> Optional[int]:
        """Return the CT color value in mireds."""
        return self._color_temp

    @property
    def min_mireds(self) -> Optional[int]:
        """Return the coldest color_temp that this light supports."""
        return self._min_mireds

    @property
    def max_mireds(self) -> Optional[int]:
        """Return the warmest color_temp that this light supports."""
        return self._max_mireds

    @property
    def white_value(self) -> Optional[int]:
        """Return the white value of this light between 0..255."""
        return self._white_value

    @property
    def effect_list(self) -> Optional[List[str]]:
        """Return the list of supported effects."""
        return self._effect_list

    @property
    def effect(self) -> Optional[str]:
        """Return the current effect."""
        return self._effect

    @property
    def supported_features(self) -> int:
        """Flag supported features."""
        return self._supported_features

    @property
    def should_poll(self) -> bool:
        """No polling needed for a group light."""
        return False

    async def _async_send_message(self, service, **kwargs):
        """Send a message to all entities in the group."""
        tasks = []
        for entity_id in self._entity_ids:
            payload = deepcopy(kwargs)
            payload[ATTR_ENTITY_ID] = entity_id
            tasks.append(self.hass.services.async_call(
                'light', SERVICE_TURN_OFF, payload, blocking=True))

        if tasks:
            await asyncio.wait(tasks, loop=self.hass.loop)

    async def async_turn_on(self, **kwargs):
        """Forward the turn_on command to all lights in the group."""
        await self._async_send_message(SERVICE_TURN_ON, **kwargs)

    async def async_turn_off(self, **kwargs):
        """Forward the turn_off command to all lights in the group."""
        await self._async_send_message(SERVICE_TURN_OFF, **kwargs)

    async def async_update(self):
        """Query all members and determine the group state."""
        states = self._child_states()

        self._state = _determine_on_off_state(states)
        self._brightness = _reduce_attribute(states, 'brightness')
        self._xy_color = _reduce_attribute(states, 'xy_color')
        self._rgb_color = _reduce_attribute(states, 'rgb_color')
        self._color_temp = _reduce_attribute(states, 'color_temp')
        self._min_mireds = _reduce_attribute(
            states, 'min_mireds', default=154, force_on=False)
        self._max_mireds = _reduce_attribute(
            states, 'max_mireds', default=500, force_on=False)
        self._white_value = _reduce_attribute(states, 'white_value')

        all_effect_lists = list(
            _find_state_attributes(states, 'effect_list', force_on=False))
        self._effect_list = None
        if all_effect_lists:
            # Merge all effects from all effect_lists with a union merge.
            self._effect_list = list(set().union(*all_effect_lists))

        all_effects = list(_find_state_attributes(states, 'effect'))
        self._effect = None
        if all_effects:
            flat_effects = list(itertools.chain(*all_effect_lists))
            # Report the most common effect.
            effects_count = Counter(flat_effects)
            self._effect = effects_count.most_common(1)[0][0]

        self._supported_features = 0
        for support in _find_state_attributes(
                states, 'supported_features', force_on=False):
            # Merge supported features by emulating support for every feature
            # we find.
            self._supported_features |= support
        # Bitwise-and the supported features with the GroupedLight's features
        # so that we don't break in the future when a new feature is added.
        self._supported_features &= SUPPORT_GROUP_LIGHT

    def _child_states(self) -> List[State]:
        """The states that the group is tracking."""
        states = [self.hass.states.get(x) for x in self._entity_ids]
        return list(filter(None, states))


def _find_state_attributes(states: List[State],
                           key: str,
                           force_on: bool = True) -> Iterator[Any]:
    """Find attributes with matching key from states.

    Only return attributes of enabled lights when force_on is True.
    """
    for state in states:
        assume_on = (not force_on) or state.state == STATE_ON
        if assume_on and key in state.attributes:
            yield state.attributes.get(key)


def _reduce_attribute(states: List[State],
                      key: str,
                      default: Optional[Any] = None,
                      force_on: bool = True) -> Any:
    """Find the first attribute matching key from states.

    If none are found, return default.
    """
    return next(_find_state_attributes(states, key, force_on), default)


def _determine_on_off_state(states: List[State]) -> str:
    """Helper method to determine the ON/OFF/... state of a light."""
    s_states = [state.state for state in states]

    if not s_states or all(state == STATE_UNAVAILABLE for state in s_states):
        return STATE_UNAVAILABLE
    elif any(state == STATE_ON for state in s_states):
        return STATE_ON
    elif all(state == STATE_UNKNOWN for state in s_states):
        return STATE_UNKNOWN
    return STATE_OFF
