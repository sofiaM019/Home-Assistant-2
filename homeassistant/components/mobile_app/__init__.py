"""Integrates Native Apps to Home Assistant."""
import asyncio
import logging

import voluptuous as vol

from homeassistant.components import cloud
from homeassistant.components.http import HomeAssistantView
from homeassistant.components.webhook import (
    async_register as webhook_register,
    async_unregister as webhook_unregister,
)
from homeassistant.const import CONF_WEBHOOK_ID
from homeassistant.core import callback
from homeassistant.helpers import (
    config_validation as cv,
    device_registry as dr,
    discovery,
)
from homeassistant.helpers.typing import ConfigType, HomeAssistantType

from .const import (
    ATTR_BACKGROUND,
    ATTR_DEFAULT_BEHAVIOR,
    ATTR_DEVICE_ID,
    ATTR_DEVICE_NAME,
    ATTR_FOREGROUND,
    ATTR_MANUFACTURER,
    ATTR_MODEL,
    ATTR_OS_VERSION,
    ATTR_TEXT_INPUT_BEHAVIOR,
    CONF_CLOUDHOOK_URL,
    CONF_ECO_IOS,
    CONF_PUSH,
    CONF_PUSH_ACTIONS_ACTIVATION_MODE,
    CONF_PUSH_ACTIONS_AUTHENTICATION_REQUIRED,
    CONF_PUSH_ACTIONS_BEHAVIOR,
    CONF_PUSH_ACTIONS_DESTRUCTIVE,
    CONF_PUSH_ACTIONS_IDENTIFIER,
    CONF_PUSH_ACTIONS_TEXT_INPUT_BUTTON_TITLE,
    CONF_PUSH_ACTIONS_TEXT_INPUT_PLACEHOLDER,
    CONF_PUSH_ACTIONS_TITLE,
    CONF_PUSH_CATEGORIES,
    CONF_PUSH_CATEGORIES_ACTIONS,
    CONF_PUSH_CATEGORIES_IDENTIFIER,
    CONF_PUSH_CATEGORIES_NAME,
    DATA_BINARY_SENSOR,
    DATA_CONFIG_ENTRIES,
    DATA_DELETED_IDS,
    DATA_DEVICES,
    DATA_SENSOR,
    DATA_STORE,
    DOMAIN,
    STORAGE_KEY,
    STORAGE_VERSION,
)
from .helpers import savable_state
from .http_api import RegistrationsView
from .webhook import handle_webhook

PLATFORMS = "sensor", "binary_sensor", "device_tracker"

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistantType, config: ConfigType):
    """Set up the mobile app component."""
    store = hass.helpers.storage.Store(STORAGE_VERSION, STORAGE_KEY)
    app_config = await store.async_load()
    if app_config is None:
        app_config = {
            DATA_BINARY_SENSOR: {},
            DATA_CONFIG_ENTRIES: {},
            DATA_DELETED_IDS: [],
            DATA_SENSOR: {},
        }

    hass.data[DOMAIN] = {
        DATA_BINARY_SENSOR: app_config.get(DATA_BINARY_SENSOR, {}),
        DATA_CONFIG_ENTRIES: {},
        DATA_DELETED_IDS: app_config.get(DATA_DELETED_IDS, []),
        DATA_DEVICES: {},
        DATA_SENSOR: app_config.get(DATA_SENSOR, {}),
        DATA_STORE: store,
    }

    hass.http.register_view(RegistrationsView())

    for deleted_id in hass.data[DOMAIN][DATA_DELETED_IDS]:
        try:
            webhook_register(
                hass, DOMAIN, "Deleted Webhook", deleted_id, handle_webhook
            )
        except ValueError:
            pass

    hass.async_create_task(
        discovery.async_load_platform(hass, "notify", DOMAIN, {}, config)
    )

    conf = config.get(DOMAIN)

    if conf:
        if CONF_ECO_IOS in conf:
            hass.http.register_view(iOSPushConfigView(conf[CONF_ECO_IOS]))

    return True


async def async_setup_entry(hass, entry):
    """Set up a mobile_app entry."""
    registration = entry.data

    webhook_id = registration[CONF_WEBHOOK_ID]

    hass.data[DOMAIN][DATA_CONFIG_ENTRIES][webhook_id] = entry

    device_registry = await dr.async_get_registry(hass)

    device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, registration[ATTR_DEVICE_ID])},
        manufacturer=registration[ATTR_MANUFACTURER],
        model=registration[ATTR_MODEL],
        name=registration[ATTR_DEVICE_NAME],
        sw_version=registration[ATTR_OS_VERSION],
    )

    hass.data[DOMAIN][DATA_DEVICES][webhook_id] = device

    registration_name = f"Mobile App: {registration[ATTR_DEVICE_NAME]}"
    webhook_register(hass, DOMAIN, registration_name, webhook_id, handle_webhook)

    for domain in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, domain)
        )

    return True


async def async_unload_entry(hass, entry):
    """Unload a mobile app entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )
    if not unload_ok:
        return False

    webhook_unregister(hass, entry.data[CONF_WEBHOOK_ID])

    return True


async def async_remove_entry(hass, entry):
    """Cleanup when entry is removed."""
    hass.data[DOMAIN][DATA_DELETED_IDS].append(entry.data[CONF_WEBHOOK_ID])
    store = hass.data[DOMAIN][DATA_STORE]
    await store.async_save(savable_state(hass))

    if CONF_CLOUDHOOK_URL in entry.data:
        try:
            await cloud.async_delete_cloudhook(hass, entry.data[CONF_WEBHOOK_ID])
        except cloud.CloudNotAvailable:
            pass


class iOSPushConfigView(HomeAssistantView):
    """A view that provides the iOOS push categories configuration."""

    url = "/api/mobile_app/ios"
    name = "api:mobile_app:ios"

    def __init__(self, push_config):
        """Init the view."""
        self.push_config = push_config

    @callback
    def get(self, request):
        """Handle the GET request for the push configuration."""
        return self.json(self.push_config)


BEHAVIORS = [ATTR_DEFAULT_BEHAVIOR, ATTR_TEXT_INPUT_BEHAVIOR]

ACTIVATION_MODES = [ATTR_FOREGROUND, ATTR_BACKGROUND]

PUSH_ACTION_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_PUSH_ACTIONS_IDENTIFIER): vol.Upper,
        vol.Required(CONF_PUSH_ACTIONS_TITLE): cv.string,
        vol.Optional(
            CONF_PUSH_ACTIONS_ACTIVATION_MODE, default=ATTR_BACKGROUND
        ): vol.In(ACTIVATION_MODES),
        vol.Optional(
            CONF_PUSH_ACTIONS_AUTHENTICATION_REQUIRED, default=False
        ): cv.boolean,
        vol.Optional(CONF_PUSH_ACTIONS_DESTRUCTIVE, default=False): cv.boolean,
        vol.Optional(CONF_PUSH_ACTIONS_BEHAVIOR, default=ATTR_DEFAULT_BEHAVIOR): vol.In(
            BEHAVIORS
        ),
        vol.Optional(CONF_PUSH_ACTIONS_TEXT_INPUT_BUTTON_TITLE): cv.string,
        vol.Optional(CONF_PUSH_ACTIONS_TEXT_INPUT_PLACEHOLDER): cv.string,
    },
    extra=vol.ALLOW_EXTRA,
)

PUSH_ACTION_SCHEMA_LIST = vol.All(cv.ensure_list, [PUSH_ACTION_SCHEMA])

ACTION_SCHEMA = vol.Schema(
    {
        vol.Required("name"): cv.string,
        vol.Required("text"): vol.All(
            {vol.Required("label"): cv.string, vol.Required("color"): cv.string}
        ),
        vol.Required("icon"): vol.All(
            {vol.Required("icon"): cv.string, vol.Required("color"): cv.string}
        ),
    },
    extra=vol.ALLOW_EXTRA,
)

ACTION_SCHEMA_LIST = vol.All(cv.ensure_list, [ACTION_SCHEMA])

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: {
            CONF_ECO_IOS: {
                CONF_PUSH: {
                    CONF_PUSH_CATEGORIES: vol.All(
                        cv.ensure_list,
                        [
                            {
                                vol.Required(CONF_PUSH_CATEGORIES_NAME): cv.string,
                                vol.Required(
                                    CONF_PUSH_CATEGORIES_IDENTIFIER
                                ): vol.Lower,
                                vol.Required(
                                    CONF_PUSH_CATEGORIES_ACTIONS
                                ): PUSH_ACTION_SCHEMA_LIST,
                            }
                        ],
                    )
                },
                vol.Optional("actions"): ACTION_SCHEMA_LIST,
            }
        }
    },
    extra=vol.ALLOW_EXTRA,
)
