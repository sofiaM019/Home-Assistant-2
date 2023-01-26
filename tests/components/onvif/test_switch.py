"""Test button of ONVIF integration."""
from unittest.mock import AsyncMock

from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN, SwitchDeviceClass
from homeassistant.const import ATTR_DEVICE_CLASS, ATTR_ENTITY_ID, STATE_UNKNOWN
from homeassistant.helpers import entity_registry as er

from . import MAC, setup_onvif_integration


async def test_wiper_switch(hass):
    """Test states of the Wiper switch."""
    _config, _camera, device = await setup_onvif_integration(hass)
    device.profiles = device.async_get_profiles()

    state = hass.states.get("switch.testcamera_wiper")
    assert state
    assert state.state == STATE_UNKNOWN

    registry = er.async_get(hass)
    entry = registry.async_get("switch.testcamera_wiper")
    assert entry
    assert entry.unique_id == f"{MAC}_wiper"


async def test_turn_wiper_switch_on(hass):
    """Test Wiper switch turn on."""
    _, _camera, device = await setup_onvif_integration(hass)
    device.async_run_aux_command = AsyncMock(return_value=True)

    await hass.services.async_call(
        SWITCH_DOMAIN,
        "turn_on",
        {ATTR_ENTITY_ID: "switch.testcamera_wiper"},
        blocking=True,
    )
    await hass.async_block_till_done()

    device.async_run_aux_command.assert_called_once()


async def test_autofocus_switch(hass):
    """Test states of the autofocus switch."""
    _config, _camera, device = await setup_onvif_integration(hass)
    device.profiles = device.async_get_profiles()

    state = hass.states.get("switch.testcamera_autofocus")
    assert state
    assert state.state == STATE_UNKNOWN

    registry = er.async_get(hass)
    entry = registry.async_get("switch.testcamera_autofocus")
    assert entry
    assert entry.unique_id == f"{MAC}_autofocus"


async def test_turn_autofocus_switch_on(hass):
    """Test autofocus switch turn on."""
    _, _camera, device = await setup_onvif_integration(hass)
    device.async_set_imaging_settings = AsyncMock(return_value=True)

    await hass.services.async_call(
        SWITCH_DOMAIN,
        "turn_on",
        {ATTR_ENTITY_ID: "switch.testcamera_autofocus"},
        blocking=True,
    )
    await hass.async_block_till_done()

    device.async_set_imaging_settings.assert_called_once()
