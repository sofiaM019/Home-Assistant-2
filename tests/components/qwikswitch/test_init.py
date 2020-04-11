"""Test qwikswitch sensors."""
import asyncio
import logging

import pytest
from yarl import URL

from homeassistant.components.qwikswitch import DOMAIN as QWIKSWITCH
from homeassistant.const import EVENT_HOMEASSISTANT_START
from homeassistant.setup import async_setup_component

from tests.test_util.aiohttp import AiohttpClientMockResponse, MockLongPollSideEffect

_LOGGER = logging.getLogger(__name__)


@pytest.fixture
def qs_devices():
    """Return a set of devices as a response."""
    return [
        {
            "id": "@a00001",
            "name": "Switch 1",
            "type": "rel",
            "val": "OFF",
            "time": "1522777506",
            "rssi": "51%",
        },
        {
            "id": "@a00002",
            "name": "Light 2",
            "type": "rel",
            "val": "ON",
            "time": "1522777507",
            "rssi": "45%",
        },
        {
            "id": "@a00003",
            "name": "Dim 3",
            "type": "dim",
            "val": "280c00",
            "time": "1522777544",
            "rssi": "62%",
        },
    ]


async def test_binary_sensor_device(hass, aioclient_mock, qs_devices):
    """Test a binary sensor device."""
    config = {
        "qwikswitch": {
            "sensors": {"name": "s1", "id": "@a00001", "channel": 1, "type": "imod"}
        }
    }
    aioclient_mock.get("http://127.0.0.1:2020/&device", json=qs_devices)
    listen_mock = MockLongPollSideEffect()
    aioclient_mock.get("http://127.0.0.1:2020/&listen", side_effect=listen_mock)
    await async_setup_component(hass, QWIKSWITCH, config)
    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    await hass.async_block_till_done()

    state_obj = hass.states.get("binary_sensor.s1")
    assert state_obj.state == "off"

    listen_mock.queue_response(
        json={"id": "@a00001", "cmd": "", "data": "4e0e1601", "rssi": "61%"}
    )
    await asyncio.sleep(0.01)
    await hass.async_block_till_done()
    state_obj = hass.states.get("binary_sensor.s1")
    assert state_obj.state == "on"

    listen_mock.queue_response(
        json={"id": "@a00001", "cmd": "", "data": "4e0e1701", "rssi": "61%"},
    )
    await asyncio.sleep(0.01)
    await hass.async_block_till_done()
    state_obj = hass.states.get("binary_sensor.s1")
    assert state_obj.state == "off"

    listen_mock.stop()


async def test_sensor_device(hass, aioclient_mock, qs_devices):
    """Test a sensor device."""
    config = {
        "qwikswitch": {
            "sensors": {
                "name": "ss1",
                "id": "@a00001",
                "channel": 1,
                "type": "qwikcord",
            }
        }
    }
    aioclient_mock.get("http://127.0.0.1:2020/&device", json=qs_devices)
    listen_mock = MockLongPollSideEffect()
    aioclient_mock.get("http://127.0.0.1:2020/&listen", side_effect=listen_mock)
    await async_setup_component(hass, QWIKSWITCH, config)
    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    await hass.async_block_till_done()

    state_obj = hass.states.get("sensor.ss1")
    assert state_obj.state == "None"

    listen_mock.queue_response(
        json={"id": "@a00001", "name": "ss1", "type": "rel", "val": "4733800001a00000"},
    )
    await asyncio.sleep(0.01)
    await hass.async_block_till_done()
    state_obj = hass.states.get("sensor.ss1")
    assert state_obj.state == "416"

    listen_mock.stop()


async def test_switch_device(hass, aioclient_mock, qs_devices):
    """Test a switch device."""

    async def get_devices_json(method, url, data):
        return AiohttpClientMockResponse(method=method, url=url, json=qs_devices)

    config = {"qwikswitch": {"switches": ["@a00001"]}}
    aioclient_mock.get("http://127.0.0.1:2020/&device", side_effect=get_devices_json)
    listen_mock = MockLongPollSideEffect()
    aioclient_mock.get("http://127.0.0.1:2020/&listen", side_effect=listen_mock)
    await async_setup_component(hass, QWIKSWITCH, config)
    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    await hass.async_block_till_done()

    state_obj = hass.states.get("switch.switch_1")
    assert state_obj.state == "off"

    aioclient_mock.mock_calls.clear()
    aioclient_mock.get("http://127.0.0.1:2020/@a00001=100")
    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": "switch.switch_1"}, blocking=True
    )
    await asyncio.sleep(0.01)
    assert (
        "GET",
        URL("http://127.0.0.1:2020/@a00001=100"),
        None,
        None,
    ) in aioclient_mock.mock_calls

    qs_devices[0]["val"] = "ON"
    state_obj = hass.states.get("switch.switch_1")
    assert state_obj.state == "off"
    listen_mock.queue_response(json={"id": "@a00001", "cmd": ""},)
    await hass.async_block_till_done()
    state_obj = hass.states.get("switch.switch_1")
    assert state_obj.state == "on"

    aioclient_mock.mock_calls.clear()
    aioclient_mock.get("http://127.0.0.1:2020/@a00001=0")
    await hass.services.async_call(
        "switch", "turn_off", {"entity_id": "switch.switch_1"}, blocking=True
    )
    assert (
        "GET",
        URL("http://127.0.0.1:2020/@a00001=0"),
        None,
        None,
    ) in aioclient_mock.mock_calls

    listen_mock.stop()
