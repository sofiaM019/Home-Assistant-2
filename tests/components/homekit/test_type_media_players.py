"""Test different accessory types: Media Players."""

from homeassistant.components.homekit.const import (
    ATTR_VALUE, CONF_FEATURE_LIST, FEATURE_ON_OFF, FEATURE_PLAY_PAUSE,
    FEATURE_PLAY_STOP, FEATURE_SELECT_SOURCE, FEATURE_TOGGLE_MUTE,
    FEATURE_VOLUME_STEP)
from homeassistant.components.homekit.type_media_players import (
    MediaPlayer, TelevisionMediaPlayer)
from homeassistant.components.media_player.const import (
    ATTR_INPUT_SOURCE, ATTR_INPUT_SOURCE_LIST,
    ATTR_MEDIA_VOLUME_MUTED, DOMAIN)
from homeassistant.const import (
    ATTR_DEVICE_CLASS, ATTR_ENTITY_ID, ATTR_SUPPORTED_FEATURES, CONF_TYPE,
    STATE_IDLE, STATE_OFF, STATE_ON, STATE_PAUSED, STATE_PLAYING)


from tests.common import async_mock_service


async def test_media_player_set_state(hass, hk_driver, events):
    """Test if accessory and HA are updated accordingly."""
    config = {CONF_FEATURE_LIST: {
        FEATURE_ON_OFF: None, FEATURE_PLAY_PAUSE: None,
        FEATURE_PLAY_STOP: None, FEATURE_TOGGLE_MUTE: None}}
    entity_id = 'media_player.test'

    hass.states.async_set(entity_id, None, {ATTR_SUPPORTED_FEATURES: 20873,
                                            ATTR_MEDIA_VOLUME_MUTED: False})
    await hass.async_block_till_done()
    acc = MediaPlayer(hass, hk_driver, 'MediaPlayer', entity_id, 2, config)
    await hass.async_add_job(acc.run)

    assert acc.aid == 2
    assert acc.category == 8  # Switch

    assert acc.chars[FEATURE_ON_OFF].value is False
    assert acc.chars[FEATURE_PLAY_PAUSE].value is False
    assert acc.chars[FEATURE_PLAY_STOP].value is False
    assert acc.chars[FEATURE_TOGGLE_MUTE].value is False

    hass.states.async_set(entity_id, STATE_ON, {ATTR_MEDIA_VOLUME_MUTED: True})
    await hass.async_block_till_done()
    assert acc.chars[FEATURE_ON_OFF].value is True
    assert acc.chars[FEATURE_TOGGLE_MUTE].value is True

    hass.states.async_set(entity_id, STATE_OFF)
    await hass.async_block_till_done()
    assert acc.chars[FEATURE_ON_OFF].value is False

    hass.states.async_set(entity_id, STATE_PLAYING)
    await hass.async_block_till_done()
    assert acc.chars[FEATURE_PLAY_PAUSE].value is True
    assert acc.chars[FEATURE_PLAY_STOP].value is True

    hass.states.async_set(entity_id, STATE_PAUSED)
    await hass.async_block_till_done()
    assert acc.chars[FEATURE_PLAY_PAUSE].value is False

    hass.states.async_set(entity_id, STATE_IDLE)
    await hass.async_block_till_done()
    assert acc.chars[FEATURE_PLAY_STOP].value is False

    # Set from HomeKit
    call_turn_on = async_mock_service(hass, DOMAIN, 'turn_on')
    call_turn_off = async_mock_service(hass, DOMAIN, 'turn_off')
    call_media_play = async_mock_service(hass, DOMAIN, 'media_play')
    call_media_pause = async_mock_service(hass, DOMAIN, 'media_pause')
    call_media_stop = async_mock_service(hass, DOMAIN, 'media_stop')
    call_toggle_mute = async_mock_service(hass, DOMAIN, 'volume_mute')

    await hass.async_add_job(acc.chars[FEATURE_ON_OFF]
                             .client_update_value, True)
    await hass.async_block_till_done()
    assert call_turn_on
    assert call_turn_on[0].data[ATTR_ENTITY_ID] == entity_id
    assert len(events) == 1
    assert events[-1].data[ATTR_VALUE] is None

    await hass.async_add_job(acc.chars[FEATURE_ON_OFF]
                             .client_update_value, False)
    await hass.async_block_till_done()
    assert call_turn_off
    assert call_turn_off[0].data[ATTR_ENTITY_ID] == entity_id
    assert len(events) == 2
    assert events[-1].data[ATTR_VALUE] is None

    await hass.async_add_job(acc.chars[FEATURE_PLAY_PAUSE]
                             .client_update_value, True)
    await hass.async_block_till_done()
    assert call_media_play
    assert call_media_play[0].data[ATTR_ENTITY_ID] == entity_id
    assert len(events) == 3
    assert events[-1].data[ATTR_VALUE] is None

    await hass.async_add_job(acc.chars[FEATURE_PLAY_PAUSE]
                             .client_update_value, False)
    await hass.async_block_till_done()
    assert call_media_pause
    assert call_media_pause[0].data[ATTR_ENTITY_ID] == entity_id
    assert len(events) == 4
    assert events[-1].data[ATTR_VALUE] is None

    await hass.async_add_job(acc.chars[FEATURE_PLAY_STOP]
                             .client_update_value, True)
    await hass.async_block_till_done()
    assert call_media_play
    assert call_media_play[1].data[ATTR_ENTITY_ID] == entity_id
    assert len(events) == 5
    assert events[-1].data[ATTR_VALUE] is None

    await hass.async_add_job(acc.chars[FEATURE_PLAY_STOP]
                             .client_update_value, False)
    await hass.async_block_till_done()
    assert call_media_stop
    assert call_media_stop[0].data[ATTR_ENTITY_ID] == entity_id
    assert len(events) == 6
    assert events[-1].data[ATTR_VALUE] is None

    await hass.async_add_job(acc.chars[FEATURE_TOGGLE_MUTE]
                             .client_update_value, True)
    await hass.async_block_till_done()
    assert call_toggle_mute
    assert call_toggle_mute[0].data[ATTR_ENTITY_ID] == entity_id
    assert call_toggle_mute[0].data[ATTR_MEDIA_VOLUME_MUTED] is True
    assert len(events) == 7
    assert events[-1].data[ATTR_VALUE] is None

    await hass.async_add_job(acc.chars[FEATURE_TOGGLE_MUTE]
                             .client_update_value, False)
    await hass.async_block_till_done()
    assert call_toggle_mute
    assert call_toggle_mute[1].data[ATTR_ENTITY_ID] == entity_id
    assert call_toggle_mute[1].data[ATTR_MEDIA_VOLUME_MUTED] is False
    assert len(events) == 8
    assert events[-1].data[ATTR_VALUE] is None


async def test_media_player_television_set_state(hass, hk_driver, events):
    """Test if television accessory and HA are updated accordingly."""
    config = {CONF_FEATURE_LIST: {
        FEATURE_ON_OFF: None, FEATURE_PLAY_PAUSE: None,
        FEATURE_SELECT_SOURCE: None, FEATURE_TOGGLE_MUTE: None,
        FEATURE_VOLUME_STEP: None}}
    entity_id = 'media_player.television'

    hass.states.async_set(entity_id, None, {ATTR_DEVICE_CLASS: 'tv',
                                            ATTR_SUPPORTED_FEATURES: 20873,
                                            ATTR_MEDIA_VOLUME_MUTED: False,
                                            ATTR_INPUT_SOURCE_LIST:
                                            ['HDMI 1', 'HDMI 2', 'HDMI 3',
                                             'HDMI 4']
                                            })
    await hass.async_block_till_done()
    acc = TelevisionMediaPlayer(hass, hk_driver, 'MediaPlayer', entity_id, 2,
                                config)
    await hass.async_add_job(acc.run)

    assert acc.aid == 2
    assert acc.category == 31  # Television

    assert acc.chars[FEATURE_ON_OFF].value == 0
    assert acc.chars[FEATURE_PLAY_PAUSE].value == 0
    assert acc.chars[FEATURE_SELECT_SOURCE].value == 0
    assert acc.chars[FEATURE_TOGGLE_MUTE].value is False

    hass.states.async_set(entity_id, STATE_ON, {ATTR_MEDIA_VOLUME_MUTED: True})
    await hass.async_block_till_done()
    assert acc.chars[FEATURE_ON_OFF].value == 1
    assert acc.chars[FEATURE_TOGGLE_MUTE].value is True

    hass.states.async_set(entity_id, STATE_OFF)
    await hass.async_block_till_done()
    assert acc.chars[FEATURE_ON_OFF].value == 0

    hass.states.async_set(entity_id, STATE_ON, {ATTR_INPUT_SOURCE: 'HDMI 2'})
    await hass.async_block_till_done()
    assert acc.chars[FEATURE_SELECT_SOURCE].value == 1

    hass.states.async_set(entity_id, STATE_ON, {ATTR_INPUT_SOURCE: 'HDMI 3'})
    await hass.async_block_till_done()
    assert acc.chars[FEATURE_SELECT_SOURCE].value == 2

    # Set from HomeKit
    call_turn_on = async_mock_service(hass, DOMAIN, 'turn_on')
    call_turn_off = async_mock_service(hass, DOMAIN, 'turn_off')
    call_media_play = async_mock_service(hass, DOMAIN, 'media_play')
    call_media_pause = async_mock_service(hass, DOMAIN, 'media_pause')
    call_toggle_mute = async_mock_service(hass, DOMAIN, 'volume_mute')
    call_select_source = async_mock_service(hass, DOMAIN, 'select_source')
    call_volume_up = async_mock_service(hass, DOMAIN, 'volume_up')
    call_volume_down = async_mock_service(hass, DOMAIN, 'volume_down')

    await hass.async_add_job(acc.chars[FEATURE_ON_OFF]
                             .client_update_value, 1)
    await hass.async_block_till_done()
    assert call_turn_on
    assert call_turn_on[0].data[ATTR_ENTITY_ID] == entity_id
    assert len(events) == 1
    assert events[-1].data[ATTR_VALUE] is None

    await hass.async_add_job(acc.chars[FEATURE_ON_OFF]
                             .client_update_value, 0)
    await hass.async_block_till_done()
    assert call_turn_off
    assert call_turn_off[0].data[ATTR_ENTITY_ID] == entity_id
    assert len(events) == 2
    assert events[-1].data[ATTR_VALUE] is None

    hass.states.async_set(entity_id, STATE_PAUSED)
    await hass.async_block_till_done()
    await hass.async_add_job(acc.chars[FEATURE_PLAY_PAUSE]
                             .client_update_value, 11)
    await hass.async_block_till_done()
    assert call_media_play
    assert call_media_play[0].data[ATTR_ENTITY_ID] == entity_id
    assert len(events) == 3
    assert events[-1].data[ATTR_VALUE] is None

    hass.states.async_set(entity_id, STATE_PLAYING)
    await hass.async_block_till_done()
    await hass.async_add_job(acc.chars[FEATURE_PLAY_PAUSE]
                             .client_update_value, 11)
    await hass.async_block_till_done()
    assert call_media_pause
    assert call_media_pause[0].data[ATTR_ENTITY_ID] == entity_id
    assert len(events) == 4
    assert events[-1].data[ATTR_VALUE] is None

    await hass.async_add_job(acc.chars[FEATURE_TOGGLE_MUTE]
                             .client_update_value, True)
    await hass.async_block_till_done()
    assert call_toggle_mute
    assert call_toggle_mute[0].data[ATTR_ENTITY_ID] == entity_id
    assert call_toggle_mute[0].data[ATTR_MEDIA_VOLUME_MUTED] is True
    assert len(events) == 5
    assert events[-1].data[ATTR_VALUE] is None

    await hass.async_add_job(acc.chars[FEATURE_TOGGLE_MUTE]
                             .client_update_value, False)
    await hass.async_block_till_done()
    assert call_toggle_mute
    assert call_toggle_mute[1].data[ATTR_ENTITY_ID] == entity_id
    assert call_toggle_mute[1].data[ATTR_MEDIA_VOLUME_MUTED] is False
    assert len(events) == 6
    assert events[-1].data[ATTR_VALUE] is None

    await hass.async_add_job(acc.chars[FEATURE_SELECT_SOURCE]
                             .client_update_value, 1)
    await hass.async_block_till_done()
    assert call_select_source
    assert call_select_source[0].data[ATTR_ENTITY_ID] == entity_id
    assert call_select_source[0].data[ATTR_INPUT_SOURCE] == 'HDMI 2'
    assert len(events) == 7
    assert events[-1].data[ATTR_VALUE] is None

    await hass.async_add_job(acc.chars[FEATURE_VOLUME_STEP]
                             .client_update_value, 0)
    await hass.async_block_till_done()
    assert call_volume_up
    assert call_volume_up[0].data[ATTR_ENTITY_ID] == entity_id
    assert len(events) == 8
    assert events[-1].data[ATTR_VALUE] is None

    await hass.async_add_job(acc.chars[FEATURE_VOLUME_STEP]
                             .client_update_value, 1)
    await hass.async_block_till_done()
    assert call_volume_down
    assert call_volume_down[0].data[ATTR_ENTITY_ID] == entity_id
    assert len(events) == 9
    assert events[-1].data[ATTR_VALUE] is None
