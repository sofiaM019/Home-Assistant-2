"""The tests for Radarr binary sensor platform."""
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.const import ATTR_DEVICE_CLASS
from homeassistant.core import HomeAssistant

from . import setup_integration

from tests.test_util.aiohttp import AiohttpClientMocker


async def test_binary_sensors(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker):
    """Test for binary sensor values."""
    await setup_integration(hass, aioclient_mock)

    state = hass.states.get("binary_sensor.radarr_health")
    assert state.state == "on"
    assert state.attributes.get(ATTR_DEVICE_CLASS) == BinarySensorDeviceClass.PROBLEM
