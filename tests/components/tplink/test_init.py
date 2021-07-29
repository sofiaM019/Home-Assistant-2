"""Tests for the TP-Link component."""
from __future__ import annotations

from datetime import datetime
import time
from typing import Any
from unittest.mock import MagicMock, patch

from pyHS100 import SmartBulb, SmartDevice, SmartDeviceException, SmartPlug
from pyHS100.smartdevice import EmeterStatus
import pytest

from homeassistant import config_entries, data_entry_flow
from homeassistant.components import tplink
from homeassistant.components.sensor import ATTR_LAST_RESET
from homeassistant.components.switch import ATTR_CURRENT_POWER_W, ATTR_TODAY_ENERGY_KWH
from homeassistant.components.tplink.common import SmartDevices
from homeassistant.components.tplink.const import (
    ATTR_CURRENT_A,
    ATTR_TOTAL_ENERGY_KWH,
    CONF_DIMMER,
    CONF_DISCOVERY,
    CONF_EMETER_PARAMS,
    CONF_LIGHT,
    CONF_MODEL,
    CONF_SW_VERSION,
    CONF_SWITCH,
    COORDINATORS,
)
from homeassistant.const import (
    ATTR_VOLTAGE,
    CONF_ALIAS,
    CONF_DEVICE_ID,
    CONF_HOST,
    CONF_MAC,
)
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util.dt import utc_from_timestamp

from tests.common import MockConfigEntry, mock_coro
from tests.components.tplink.consts import SMARTPLUGSWITCH_DATA


async def test_creating_entry_tries_discover(hass):
    """Test setting up does discovery."""
    with patch(
        "homeassistant.components.tplink.async_setup_entry",
        return_value=mock_coro(True),
    ) as mock_setup, patch(
        "homeassistant.components.tplink.common.Discover.discover",
        return_value={"host": 1234},
    ):
        result = await hass.config_entries.flow.async_init(
            tplink.DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        # Confirmation form
        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM

        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY

        await hass.async_block_till_done()

    assert len(mock_setup.mock_calls) == 1


async def test_configuring_tplink_causes_discovery(hass):
    """Test that specifying empty config does discovery."""
    with patch("homeassistant.components.tplink.common.Discover.discover") as discover:
        discover.return_value = {"host": 1234}
        await async_setup_component(hass, tplink.DOMAIN, {tplink.DOMAIN: {}})
        await hass.async_block_till_done()

    assert len(discover.mock_calls) == 1


@pytest.mark.parametrize(
    "name,cls,platform",
    [
        ("pyHS100.SmartPlug", SmartPlug, "switch"),
        ("pyHS100.SmartBulb", SmartBulb, "light"),
    ],
)
@pytest.mark.parametrize("count", [1, 2, 3])
async def test_configuring_device_types(hass, name, cls, platform, count):
    """Test that light or switch platform list is filled correctly."""
    with patch(
        "homeassistant.components.tplink.common.Discover.discover"
    ) as discover, patch(
        "homeassistant.components.tplink.common.SmartDevice._query_helper"
    ), patch(
        "homeassistant.components.tplink.light.async_setup_entry",
        return_value=True,
    ):
        discovery_data = {
            f"123.123.123.{c}": cls("123.123.123.123") for c in range(count)
        }
        discover.return_value = discovery_data
        await async_setup_component(hass, tplink.DOMAIN, {tplink.DOMAIN: {}})
        await hass.async_block_till_done()

    assert len(discover.mock_calls) == 1
    assert len(hass.data[tplink.DOMAIN][platform]) == count


class UnknownSmartDevice(SmartDevice):
    """Dummy class for testing."""

    @property
    def has_emeter(self) -> bool:
        """Do nothing."""

    def turn_off(self) -> None:
        """Do nothing."""

    def turn_on(self) -> None:
        """Do nothing."""

    @property
    def is_on(self) -> bool:
        """Do nothing."""

    @property
    def state_information(self) -> dict[str, Any]:
        """Do nothing."""


async def test_configuring_devices_from_multiple_sources(hass):
    """Test static and discover devices are not duplicated."""
    with patch(
        "homeassistant.components.tplink.common.Discover.discover"
    ) as discover, patch(
        "homeassistant.components.tplink.common.SmartDevice._query_helper"
    ), patch(
        "homeassistant.config_entries.ConfigEntries.async_forward_entry_setup"
    ):
        discover_device_fail = SmartPlug("123.123.123.123")
        discover_device_fail.get_sysinfo = MagicMock(side_effect=SmartDeviceException())

        discover.return_value = {
            "123.123.123.1": SmartBulb("123.123.123.1"),
            "123.123.123.2": SmartPlug("123.123.123.2"),
            "123.123.123.3": SmartBulb("123.123.123.3"),
            "123.123.123.4": SmartPlug("123.123.123.4"),
            "123.123.123.123": discover_device_fail,
            "123.123.123.124": UnknownSmartDevice("123.123.123.124"),
        }

        await async_setup_component(
            hass,
            tplink.DOMAIN,
            {
                tplink.DOMAIN: {
                    CONF_LIGHT: [{CONF_HOST: "123.123.123.1"}],
                    CONF_SWITCH: [{CONF_HOST: "123.123.123.2"}],
                    CONF_DIMMER: [{CONF_HOST: "123.123.123.22"}],
                }
            },
        )
        await hass.async_block_till_done()

        assert len(discover.mock_calls) == 1
        assert len(hass.data[tplink.DOMAIN][CONF_LIGHT]) == 3
        assert len(hass.data[tplink.DOMAIN][CONF_SWITCH]) == 2


async def test_is_dimmable(hass):
    """Test that is_dimmable switches are correctly added as lights."""
    with patch(
        "homeassistant.components.tplink.common.Discover.discover"
    ) as discover, patch(
        "homeassistant.components.tplink.light.async_setup_entry",
        return_value=mock_coro(True),
    ) as setup, patch(
        "homeassistant.components.tplink.common.SmartDevice._query_helper"
    ), patch(
        "homeassistant.components.tplink.common.SmartPlug.is_dimmable", True
    ):
        dimmable_switch = SmartPlug("123.123.123.123")
        discover.return_value = {"host": dimmable_switch}

        await async_setup_component(hass, tplink.DOMAIN, {tplink.DOMAIN: {}})
        await hass.async_block_till_done()

    assert len(discover.mock_calls) == 1
    assert len(setup.mock_calls) == 1
    assert len(hass.data[tplink.DOMAIN][CONF_LIGHT]) == 1
    assert not hass.data[tplink.DOMAIN][CONF_SWITCH]


async def test_configuring_discovery_disabled(hass):
    """Test that discover does not get called when disabled."""
    with patch(
        "homeassistant.components.tplink.async_setup_entry",
        return_value=mock_coro(True),
    ) as mock_setup, patch(
        "homeassistant.components.tplink.common.Discover.discover", return_value=[]
    ) as discover:
        await async_setup_component(
            hass, tplink.DOMAIN, {tplink.DOMAIN: {tplink.CONF_DISCOVERY: False}}
        )
        await hass.async_block_till_done()

    assert discover.call_count == 0
    assert mock_setup.call_count == 1


async def test_platforms_are_initialized(hass: HomeAssistant):
    """Test that platforms are initialized per configuration array."""
    config = {
        tplink.DOMAIN: {
            CONF_DISCOVERY: False,
            CONF_LIGHT: [{CONF_HOST: "123.123.123.123"}],
            CONF_SWITCH: [{CONF_HOST: "321.321.321.321"}],
        }
    }

    with patch(
        "homeassistant.components.tplink.common.Discover.discover"
    ) as discover, patch(
        "homeassistant.components.tplink.get_static_devices"
    ) as get_static_devices, patch(
        "homeassistant.components.tplink.common.SmartDevice._query_helper"
    ), patch(
        "homeassistant.components.tplink.light.async_setup_entry",
        return_value=mock_coro(True),
    ) as light_setup, patch(
        "homeassistant.components.tplink.switch.async_setup_entry",
        return_value=mock_coro(True),
    ) as switch_setup, patch(
        "homeassistant.components.tplink.common.SmartPlug.is_dimmable", False
    ):

        light = SmartBulb("123.123.123.123")
        switch = SmartPlug("321.321.321.321")
        switch.get_sysinfo = MagicMock(return_value=SMARTPLUGSWITCH_DATA["sysinfo"])
        switch.get_emeter_realtime = MagicMock(
            return_value=EmeterStatus(SMARTPLUGSWITCH_DATA["realtime"])
        )
        switch.get_emeter_daily = MagicMock(
            return_value={int(time.strftime("%e")): 1.123}
        )
        get_static_devices.return_value = SmartDevices([light], [switch])

        # patching is_dimmable is necessray to avoid misdetection as light.
        await async_setup_component(hass, tplink.DOMAIN, config)
        await hass.async_block_till_done()

        assert hass.data.get(tplink.DOMAIN)
        assert hass.data[tplink.DOMAIN].get(COORDINATORS)
        assert hass.data[tplink.DOMAIN][COORDINATORS].get(switch.mac)
        assert isinstance(
            hass.data[tplink.DOMAIN][COORDINATORS][switch.mac],
            tplink.SmartPlugDataUpdateCoordinator,
        )
        data = hass.data[tplink.DOMAIN][COORDINATORS][switch.mac].data
        assert data[CONF_HOST] == switch.host
        assert data[CONF_MAC] == switch.sys_info["mac"]
        assert data[CONF_MODEL] == switch.sys_info["model"]
        assert data[CONF_SW_VERSION] == switch.sys_info["sw_ver"]
        assert data[CONF_ALIAS] == switch.sys_info["alias"]
        assert data[CONF_DEVICE_ID] == switch.sys_info["mac"]

        emeter_readings = switch.get_emeter_realtime()
        assert data[CONF_EMETER_PARAMS][ATTR_VOLTAGE] == round(
            float(emeter_readings["voltage"]), 1
        )
        assert data[CONF_EMETER_PARAMS][ATTR_CURRENT_A] == round(
            float(emeter_readings["current"]), 2
        )
        assert data[CONF_EMETER_PARAMS][ATTR_CURRENT_POWER_W] == round(
            float(emeter_readings["power"]), 2
        )
        assert data[CONF_EMETER_PARAMS][ATTR_TOTAL_ENERGY_KWH] == round(
            float(emeter_readings["total"]), 3
        )
        assert data[CONF_EMETER_PARAMS][ATTR_LAST_RESET][
            ATTR_TOTAL_ENERGY_KWH
        ] == utc_from_timestamp(0)

        assert data[CONF_EMETER_PARAMS][ATTR_TODAY_ENERGY_KWH] == 1.123
        assert data[CONF_EMETER_PARAMS][ATTR_LAST_RESET][
            ATTR_TODAY_ENERGY_KWH
        ] == datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        assert discover.call_count == 0
        assert get_static_devices.call_count == 1
        assert light_setup.call_count == 1
        assert switch_setup.call_count == 1


async def test_smartplug_without_consumption_sensors(hass: HomeAssistant):
    """Test that platforms are initialized per configuration array."""
    config = {
        tplink.DOMAIN: {
            CONF_DISCOVERY: False,
            CONF_SWITCH: [{CONF_HOST: "321.321.321.321"}],
        }
    }

    with patch("homeassistant.components.tplink.common.Discover.discover"), patch(
        "homeassistant.components.tplink.get_static_devices"
    ) as get_static_devices, patch(
        "homeassistant.components.tplink.common.SmartDevice._query_helper"
    ), patch(
        "homeassistant.components.tplink.light.async_setup_entry",
        return_value=mock_coro(True),
    ), patch(
        "homeassistant.components.tplink.switch.async_setup_entry",
        return_value=mock_coro(True),
    ), patch(
        "homeassistant.components.tplink.sensor.SmartPlugSensor.__init__"
    ) as SmartPlugSensor, patch(
        "homeassistant.components.tplink.common.SmartPlug.is_dimmable", False
    ):

        switch = SmartPlug("321.321.321.321")
        switch.get_sysinfo = MagicMock(return_value=SMARTPLUGSWITCH_DATA["sysinfo"])
        get_static_devices.return_value = SmartDevices([], [switch])

        await async_setup_component(hass, tplink.DOMAIN, config)
        await hass.async_block_till_done()

        assert SmartPlugSensor.call_count == 0


async def test_no_config_creates_no_entry(hass):
    """Test for when there is no tplink in config."""
    with patch(
        "homeassistant.components.tplink.async_setup_entry",
        return_value=mock_coro(True),
    ) as mock_setup:
        await async_setup_component(hass, tplink.DOMAIN, {})
        await hass.async_block_till_done()

    assert mock_setup.call_count == 0


async def test_not_ready(hass: HomeAssistant):
    """Test for not ready when configured devices are not available."""
    config = {
        tplink.DOMAIN: {
            CONF_DISCOVERY: False,
            CONF_SWITCH: [{CONF_HOST: "321.321.321.321"}],
        }
    }

    with patch("homeassistant.components.tplink.common.Discover.discover"), patch(
        "homeassistant.components.tplink.get_static_devices"
    ) as get_static_devices, patch(
        "homeassistant.components.tplink.common.SmartDevice._query_helper"
    ), patch(
        "homeassistant.components.tplink.light.async_setup_entry",
        return_value=mock_coro(True),
    ), patch(
        "homeassistant.components.tplink.switch.async_setup_entry",
        return_value=mock_coro(True),
    ), patch(
        "homeassistant.components.tplink.common.SmartPlug.is_dimmable", False
    ):

        switch = SmartPlug("321.321.321.321")
        switch.get_sysinfo = MagicMock(side_effect=SmartDeviceException())
        get_static_devices.return_value = SmartDevices([], [switch])

        await async_setup_component(hass, tplink.DOMAIN, config)
        await hass.async_block_till_done()

        entries = hass.config_entries.async_entries(tplink.DOMAIN)

        assert len(entries) == 1
        assert entries[0].state is config_entries.ConfigEntryState.SETUP_RETRY


@pytest.mark.parametrize("platform", ["switch", "light"])
async def test_unload(hass, platform):
    """Test that the async_unload_entry works."""
    # As we have currently no configuration, we just to pass the domain here.
    entry = MockConfigEntry(domain=tplink.DOMAIN)
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.tplink.get_static_devices"
    ) as get_static_devices, patch(
        "homeassistant.components.tplink.common.SmartDevice._query_helper"
    ), patch(
        f"homeassistant.components.tplink.{platform}.async_setup_entry",
        return_value=mock_coro(True),
    ) as async_setup_entry:
        config = {
            tplink.DOMAIN: {
                platform: [{CONF_HOST: "123.123.123.123"}],
                CONF_DISCOVERY: False,
            }
        }

        light = SmartBulb("123.123.123.123")
        switch = SmartPlug("321.321.321.321")
        switch.get_sysinfo = MagicMock(return_value=SMARTPLUGSWITCH_DATA["sysinfo"])
        switch.get_emeter_realtime = MagicMock(
            return_value=EmeterStatus(SMARTPLUGSWITCH_DATA["realtime"])
        )
        if platform == "light":
            get_static_devices.return_value = SmartDevices([light], [])
        elif platform == "switch":
            get_static_devices.return_value = SmartDevices([], [switch])

        assert await async_setup_component(hass, tplink.DOMAIN, config)
        await hass.async_block_till_done()

        assert len(async_setup_entry.mock_calls) == 1
        assert tplink.DOMAIN in hass.data

    assert await tplink.async_unload_entry(hass, entry)
    assert not hass.data[tplink.DOMAIN]
