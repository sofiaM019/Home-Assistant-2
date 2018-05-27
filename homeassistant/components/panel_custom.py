"""
Register a custom front end panel.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/panel_custom/
"""
import asyncio
import logging
import os

import voluptuous as vol

import homeassistant.helpers.config_validation as cv

DOMAIN = 'panel_custom'
DEPENDENCIES = ['frontend']

CONF_COMPONENT_NAME = 'name'
CONF_SIDEBAR_TITLE = 'sidebar_title'
CONF_SIDEBAR_ICON = 'sidebar_icon'
CONF_URL_PATH = 'url_path'
CONF_CONFIG = 'config'
CONF_WEBCOMPONENT_PATH = 'webcomponent_path'
CONF_JS_URL = 'js_url'

DEFAULT_ICON = 'mdi:bookmark'
LEGACY_URL = '/api/panel_custom/{}'

PANEL_DIR = 'panels'

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.All(cv.ensure_list, [{
        vol.Required(CONF_COMPONENT_NAME): cv.string,
        vol.Optional(CONF_SIDEBAR_TITLE): cv.string,
        vol.Optional(CONF_SIDEBAR_ICON, default=DEFAULT_ICON): cv.icon,
        vol.Optional(CONF_URL_PATH): cv.string,
        vol.Optional(CONF_CONFIG): cv.match_all,
        vol.Optional(CONF_WEBCOMPONENT_PATH): cv.isfile,
        vol.Optional(CONF_JS_URL): cv.string,
    }])
}, extra=vol.ALLOW_EXTRA)

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass, config):
    """Initialize custom panel."""
    success = False

    for panel in config.get(DOMAIN):
        name = panel.get(CONF_COMPONENT_NAME)
        panel_path = panel.get(CONF_WEBCOMPONENT_PATH)

        if panel_path is None:
            panel_path = hass.config.path(PANEL_DIR, '{}.html'.format(name))

        config = {
            'name': name,
            'config': panel.get(CONF_CONFIG),
        }

        if CONF_JS_URL in panel:
            config['js_url'] = panel[CONF_JS_URL]

        elif not os.path.isfile(panel_path):
            _LOGGER.error('Unable to find webcomponent for %s: %s',
                          name, panel_path)
            continue

        else:
            url = LEGACY_URL.format(name)
            hass.http.register_static_path(url, panel_path)
            config['html_url'] = LEGACY_URL.format(name)

        await hass.components.frontend.async_register_built_in_panel(
            component_name='custom',
            sidebar_title=panel.get(CONF_SIDEBAR_TITLE),
            sidebar_icon=panel.get(CONF_SIDEBAR_ICON),
            frontend_url_path=panel.get(CONF_URL_PATH),
            config=config
        )

        success = True

    return success
