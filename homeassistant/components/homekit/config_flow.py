"""Config flow for HomeKit integration."""
import random
import string

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import SOURCE_IMPORT
from homeassistant.const import (
    ATTR_FRIENDLY_NAME,
    CONF_DOMAINS,
    CONF_ENTITIES,
    CONF_ENTITY_ID,
    CONF_NAME,
    CONF_PORT,
)
from homeassistant.core import callback, split_entity_id
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entityfilter import (
    CONF_EXCLUDE_DOMAINS,
    CONF_EXCLUDE_ENTITIES,
    CONF_INCLUDE_DOMAINS,
    CONF_INCLUDE_ENTITIES,
)

from .const import (
    CONF_AUTO_START,
    CONF_ENTITY_CONFIG,
    CONF_FILTER,
    CONF_HOMEKIT_MODE,
    CONF_VIDEO_CODEC,
    DEFAULT_AUTO_START,
    DEFAULT_CONFIG_FLOW_PORT,
    DEFAULT_HOMEKIT_MODE,
    HOMEKIT_MODE_ACCESSORY,
    HOMEKIT_MODES,
    SHORT_BRIDGE_NAME,
    VIDEO_CODEC_COPY,
)
from .const import DOMAIN  # pylint:disable=unused-import
from .util import find_next_available_port

CONF_CAMERA_COPY = "camera_copy"
CONF_INCLUDE_EXCLUDE_MODE = "include_exclude_mode"

MODE_INCLUDE = "include"
MODE_EXCLUDE = "exclude"

INCLUDE_EXCLUDE_MODES = [MODE_EXCLUDE, MODE_INCLUDE]

SUPPORTED_DOMAINS = [
    "alarm_control_panel",
    "automation",
    "binary_sensor",
    "camera",
    "climate",
    "cover",
    "demo",
    "device_tracker",
    "fan",
    "humidifier",
    "input_boolean",
    "light",
    "lock",
    "media_player",
    "person",
    "remote",
    "scene",
    "script",
    "sensor",
    "switch",
    "vacuum",
    "water_heater",
]

DEFAULT_DOMAINS = [
    "alarm_control_panel",
    "climate",
    "cover",
    "humidifier",
    "fan",
    "light",
    "lock",
    "media_player",
    "switch",
    "vacuum",
    "water_heater",
]

CAMERA_ENTITY_PREFIX = "camera."

_EMPTY_ENTITY_FILTER = {
    CONF_INCLUDE_DOMAINS: [],
    CONF_EXCLUDE_DOMAINS: [],
    CONF_INCLUDE_ENTITIES: [],
    CONF_EXCLUDE_ENTITIES: [],
}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HomeKit."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    def __init__(self):
        """Initialize config flow."""
        self.homekit_data = {}
        self.entry_title = None

    async def async_step_accessory_mode(self, user_input=None):
        """Choose specific entity in accessory mode."""
        if user_input is not None:
            entity_id = user_input[CONF_ENTITY_ID]
            self.homekit_data[CONF_FILTER][CONF_INCLUDE_ENTITIES] = [entity_id]
            if entity_id.startswith(CAMERA_ENTITY_PREFIX):
                self.homekit_data[CONF_ENTITY_CONFIG] = {
                    entity_id: {CONF_VIDEO_CODEC: VIDEO_CODEC_COPY}
                }
            del self.homekit_data[CONF_INCLUDE_DOMAINS]
            return await self.async_step_pairing()

        all_supported_entities = _async_get_entities_matching_domains(
            self.hass,
            self.homekit_data[CONF_INCLUDE_DOMAINS],
        )
        return self.async_show_form(
            step_id="accessory_mode",
            data_schmea=vol.Schema(
                {vol.Optional(CONF_ENTITY_ID): vol.In(all_supported_entities)}
            ),
        )

    async def async_step_pairing(self, user_input=None):
        """Pairing instructions."""
        if user_input is not None:
            return self.async_create_entry(
                title=self.entry_title, data=self.homekit_data
            )
        return self.async_show_form(
            step_id="pairing",
            description_placeholders={CONF_NAME: self.homekit_data[CONF_NAME]},
        )

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            port = await self._async_available_port()
            name = self._async_available_name()
            self.entry_title = f"{name}:{port}"

            self.homekit_data = user_input.copy()
            entity_filter = _EMPTY_ENTITY_FILTER.copy()
            self.homekit_data.update(
                {
                    CONF_NAME: name,
                    CONF_PORT: port,
                    CONF_HOMEKIT_MODE: user_input[CONF_HOMEKIT_MODE],
                    CONF_FILTER: entity_filter,
                }
            )

            if user_input[CONF_HOMEKIT_MODE] == HOMEKIT_MODE_ACCESSORY:
                self.homekit_data[CONF_FILTER][CONF_INCLUDE_DOMAINS] = []
                return await self.async_step_accessory_mode()

            entity_filter[CONF_INCLUDE_DOMAINS] = self.homekit_data.pop(
                CONF_INCLUDE_DOMAINS
            )
            return await self.async_step_pairing()

        homekit_mode = self.homekit_data.get(CONF_HOMEKIT_MODE, DEFAULT_HOMEKIT_MODE)
        default_domains = [] if self._async_current_names() else DEFAULT_DOMAINS
        setup_schema = vol.Schema(
            {
                vol.Required(CONF_HOMEKIT_MODE, default=homekit_mode): vol.In(
                    HOMEKIT_MODES
                ),
                vol.Required(
                    CONF_INCLUDE_DOMAINS, default=default_domains
                ): cv.multi_select(SUPPORTED_DOMAINS),
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=setup_schema, errors=errors
        )

    async def async_step_import(self, user_input=None):
        """Handle import from yaml."""
        if not self._async_is_unique_name_port(user_input):
            return self.async_abort(reason="port_name_in_use")
        return self.async_create_entry(
            title=f"{user_input[CONF_NAME]}:{user_input[CONF_PORT]}", data=user_input
        )

    async def _async_available_port(self):
        """Return an available port the bridge."""
        return await self.hass.async_add_executor_job(
            find_next_available_port, DEFAULT_CONFIG_FLOW_PORT
        )

    @callback
    def _async_current_names(self):
        """Return a set of bridge names."""
        current_entries = self._async_current_entries()

        return {
            entry.data[CONF_NAME]
            for entry in current_entries
            if CONF_NAME in entry.data
        }

    @callback
    def _async_available_name(self):
        """Return an available for the bridge."""

        # We always pick a RANDOM name to avoid Zeroconf
        # name collisions.  If the name has been seen before
        # pairing will probably fail.
        acceptable_chars = string.ascii_uppercase + string.digits
        trailer = "".join(random.choices(acceptable_chars, k=4))
        all_names = self._async_current_names()
        suggested_name = f"{SHORT_BRIDGE_NAME} {trailer}"
        while suggested_name in all_names:
            trailer = "".join(random.choices(acceptable_chars, k=4))
            suggested_name = f"{SHORT_BRIDGE_NAME} {trailer}"

        return suggested_name

    @callback
    def _async_is_unique_name_port(self, user_input):
        """Determine is a name or port is already used."""
        name = user_input[CONF_NAME]
        port = user_input[CONF_PORT]
        for entry in self._async_current_entries():
            if entry.data[CONF_NAME] == name or entry.data[CONF_PORT] == port:
                return False
        return True

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle a option flow for tado."""

    def __init__(self, config_entry: config_entries.ConfigEntry):
        """Initialize options flow."""
        self.config_entry = config_entry
        self.homekit_options = {}
        self.included_cameras = set()

    async def async_step_yaml(self, user_input=None):
        """No options for yaml managed entries."""
        if user_input is not None:
            # Apparently not possible to abort an options flow
            # at the moment
            return self.async_create_entry(title="", data=self.config_entry.options)

        return self.async_show_form(step_id="yaml")

    async def async_step_advanced(self, user_input=None):
        """Choose advanced options."""
        if not self.show_advanced_options or user_input is not None:
            if user_input:
                self.homekit_options.update(user_input)

            self.homekit_options[CONF_AUTO_START] = self.homekit_options.get(
                CONF_AUTO_START, DEFAULT_AUTO_START
            )

            for key in (CONF_DOMAINS, CONF_ENTITIES):
                if key in self.homekit_options:
                    del self.homekit_options[key]

            return self.async_create_entry(title="", data=self.homekit_options)

        return self.async_show_form(
            step_id="advanced",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_AUTO_START,
                        default=self.homekit_options.get(
                            CONF_AUTO_START, DEFAULT_AUTO_START
                        ),
                    ): bool
                }
            ),
        )

    async def async_step_cameras(self, user_input=None):
        """Choose camera config."""
        if user_input is not None:
            entity_config = self.homekit_options[CONF_ENTITY_CONFIG]
            for entity_id in self.included_cameras:
                if entity_id in user_input[CONF_CAMERA_COPY]:
                    entity_config.setdefault(entity_id, {})[
                        CONF_VIDEO_CODEC
                    ] = VIDEO_CODEC_COPY
                elif (
                    entity_id in entity_config
                    and CONF_VIDEO_CODEC in entity_config[entity_id]
                ):
                    del entity_config[entity_id][CONF_VIDEO_CODEC]
            return await self.async_step_advanced()

        cameras_with_copy = []
        entity_config = self.homekit_options.setdefault(CONF_ENTITY_CONFIG, {})
        for entity in self.included_cameras:
            hk_entity_config = entity_config.get(entity, {})
            if hk_entity_config.get(CONF_VIDEO_CODEC) == VIDEO_CODEC_COPY:
                cameras_with_copy.append(entity)

        data_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_CAMERA_COPY,
                    default=cameras_with_copy,
                ): cv.multi_select(self.included_cameras),
            }
        )
        return self.async_show_form(step_id="cameras", data_schema=data_schema)

    async def async_step_include_exclude(self, user_input=None):
        """Choose entities to include or exclude from the domain."""
        if user_input is not None:
            entity_filter = _EMPTY_ENTITY_FILTER.copy()
            if isinstance(user_input[CONF_ENTITIES], list):
                entities = user_input[CONF_ENTITIES]
            else:
                entities = [user_input[CONF_ENTITIES]]

            if (
                self.homekit_options[CONF_HOMEKIT_MODE] == HOMEKIT_MODE_ACCESSORY
                or user_input[CONF_INCLUDE_EXCLUDE_MODE] == MODE_INCLUDE
            ):
                entity_filter[CONF_INCLUDE_ENTITIES] = entities
                # Include all of the domain if there are no entities
                # explicitly included as the user selected the domain
                domains_with_entities_selected = _domains_set_from_entities(entities)
                entity_filter[CONF_INCLUDE_DOMAINS] = [
                    domain
                    for domain in self.homekit_options[CONF_DOMAINS]
                    if domain not in domains_with_entities_selected
                ]

                for entity_id in list(self.included_cameras):
                    if entity_id not in entities:
                        self.included_cameras.remove(entity_id)
            else:
                entity_filter[CONF_INCLUDE_DOMAINS] = self.homekit_options[CONF_DOMAINS]
                entity_filter[CONF_EXCLUDE_ENTITIES] = entities
                for entity_id in entities:
                    if entity_id in self.included_cameras:
                        self.included_cameras.remove(entity_id)

            self.homekit_options[CONF_FILTER] = entity_filter

            if self.included_cameras:
                return await self.async_step_cameras()

            return await self.async_step_advanced()

        entity_filter = self.homekit_options.get(CONF_FILTER, {})
        all_supported_entities = _async_get_entities_matching_domains(
            self.hass,
            self.homekit_options[CONF_DOMAINS],
        )
        self.included_cameras = {
            entity_id
            for entity_id in all_supported_entities
            if entity_id.startswith(CAMERA_ENTITY_PREFIX)
        }

        data_schema = {}
        entities = entity_filter.get(CONF_INCLUDE_ENTITIES, [])
        if self.homekit_options[CONF_HOMEKIT_MODE] == HOMEKIT_MODE_ACCESSORY:
            entity_schema = vol.In
        else:
            if entities:
                include_exclude_mode = MODE_INCLUDE
            else:
                include_exclude_mode = MODE_EXCLUDE
                entities = entity_filter.get(CONF_EXCLUDE_ENTITIES, [])
            data_schema[
                vol.Required(CONF_INCLUDE_EXCLUDE_MODE, default=include_exclude_mode)
            ] = vol.In(INCLUDE_EXCLUDE_MODES)
            entity_schema = cv.multi_select

        data_schema[vol.Optional(CONF_ENTITIES, default=entities)] = entity_schema(
            all_supported_entities
        )

        return self.async_show_form(
            step_id="include_exclude", data_schema=vol.Schema(data_schema)
        )

    async def async_step_init(self, user_input=None):
        """Handle options flow."""
        if self.config_entry.source == SOURCE_IMPORT:
            return await self.async_step_yaml(user_input)

        if user_input is not None:
            self.homekit_options.update(user_input)
            return await self.async_step_include_exclude()

        homekit_options = dict(self.config_entry.options)
        entity_filter = homekit_options.get(CONF_FILTER, {})

        homekit_mode = homekit_options.get(CONF_HOMEKIT_MODE, DEFAULT_HOMEKIT_MODE)
        domains = entity_filter.get(CONF_INCLUDE_DOMAINS, [])
        include_entities = entity_filter.get(CONF_INCLUDE_ENTITIES)
        if include_entities:
            domains.extend(_domains_set_from_entities(include_entities))

        data_schema = vol.Schema(
            {
                vol.Required(CONF_HOMEKIT_MODE, default=homekit_mode): vol.In(
                    HOMEKIT_MODES
                ),
                vol.Optional(
                    CONF_DOMAINS,
                    default=domains,
                ): cv.multi_select(SUPPORTED_DOMAINS),
            }
        )
        return self.async_show_form(step_id="init", data_schema=data_schema)


def _async_get_entities_matching_domains(hass, domains):
    """List entities in the given domains."""
    entity_ids = {
        state.entity_id: f"{state.attributes.get(ATTR_FRIENDLY_NAME, state.entity_id)} ({state.entity_id})"
        for state in hass.states.async_all(set(domains))
    }
    entity_ids.sort()
    return entity_ids


def _domains_set_from_entities(entity_ids):
    """Build a set of domains for the given entity ids."""
    domains = set()
    for entity_id in entity_ids:
        domains.add(split_entity_id(entity_id)[0])
    return domains
