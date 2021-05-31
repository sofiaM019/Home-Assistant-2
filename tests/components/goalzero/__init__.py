"""Tests for the Goal Zero Yeti integration."""

from unittest.mock import AsyncMock, patch

from homeassistant.components.dhcp import HOSTNAME, IP_ADDRESS, MAC_ADDRESS
from homeassistant.components.goalzero.const import CONF_SCAN_INTERVAL, DEFAULT_NAME
from homeassistant.const import CONF_HOST, CONF_NAME

HOST = "1.2.3.4"

CONF_DATA = {CONF_HOST: HOST, CONF_NAME: DEFAULT_NAME}

CONF_CONFIG_FLOW = {CONF_HOST: HOST, CONF_NAME: DEFAULT_NAME}

CONF_DHCP_FLOW = {
    IP_ADDRESS: "1.1.1.1",
    MAC_ADDRESS: "AA:BB:CC:DD:EE:FF",
    HOSTNAME: "any",
}

CONF_OPTIONS_FLOW = {CONF_SCAN_INTERVAL: 30}


async def _create_mocked_yeti(raise_exception=False):
    mocked_yeti = AsyncMock()
    mocked_yeti.get_state = AsyncMock()
    return mocked_yeti


def _patch_init_yeti(mocked_yeti):
    return patch("homeassistant.components.goalzero.Yeti", return_value=mocked_yeti)


def _patch_config_flow_yeti(mocked_yeti):
    return patch(
        "homeassistant.components.goalzero.config_flow.Yeti",
        return_value=mocked_yeti,
    )
