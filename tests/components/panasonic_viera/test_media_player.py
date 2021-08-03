"""Test the Panasonic Viera media player entity."""

from datetime import timedelta
from unittest.mock import Mock
from urllib.error import HTTPError, URLError

from homeassistant.const import STATE_OFF, STATE_ON, STATE_UNAVAILABLE
from homeassistant.util.dt import utcnow

from tests.common import async_fire_time_changed


async def test_media_player_handle_URLerror(hass, init_integration, mock_remote):
    """Test remote handle URLError as Unavailable."""

    state_tv = hass.states.get("media_player.panasonic_viera_tv")
    assert state_tv.state == STATE_ON

    # simulate timeout error
    mock_remote.get_mute = Mock(side_effect=URLError(None, None))

    async_fire_time_changed(hass, utcnow() + timedelta(minutes=2))
    await hass.async_block_till_done()

    state_tv = hass.states.get("media_player.panasonic_viera_tv")
    assert state_tv.state == STATE_UNAVAILABLE


async def test_media_player_handle_HTTPError(hass, init_integration, mock_remote):
    """Test remote handle HTTPError as Off."""

    state_tv = hass.states.get("media_player.panasonic_viera_tv")
    assert state_tv.state == STATE_ON

    # simulate http badrequest
    mock_remote.get_mute = Mock(side_effect=HTTPError(None, 400, None, None, None))

    async_fire_time_changed(hass, utcnow() + timedelta(minutes=2))
    await hass.async_block_till_done()

    state_tv = hass.states.get("media_player.panasonic_viera_tv")
    assert state_tv.state == STATE_OFF
