"""Denon HEOS Media Player."""

from datetime import datetime
from pytz import UTC

from homeassistant.components.media_player import MediaPlayerDevice
from homeassistant.components.media_player.const import (
    DOMAIN,
    MEDIA_TYPE_MUSIC,
    SUPPORT_NEXT_TRACK,
    SUPPORT_PAUSE,
    SUPPORT_PLAY,
    SUPPORT_PLAY_MEDIA,
    SUPPORT_PREVIOUS_TRACK,
    SUPPORT_STOP,
    SUPPORT_VOLUME_MUTE,
    SUPPORT_VOLUME_SET,
    SUPPORT_VOLUME_STEP,
)
from homeassistant.const import STATE_IDLE, STATE_PAUSED, STATE_PLAYING

from . import DOMAIN as HEOS_DOMAIN

DEPENDENCIES = ["heos"]

SUPPORT_HEOS = (
    SUPPORT_PLAY
    | SUPPORT_STOP
    | SUPPORT_PAUSE
    | SUPPORT_PLAY_MEDIA
    | SUPPORT_PREVIOUS_TRACK
    | SUPPORT_NEXT_TRACK
    | SUPPORT_VOLUME_MUTE
    | SUPPORT_VOLUME_SET
    | SUPPORT_VOLUME_STEP
)

PLAY_STATE_TO_STATE = {
    "play": STATE_PLAYING,
    "pause": STATE_PAUSED,
    "stop": STATE_IDLE,
}


async def async_setup_platform(hass, config, async_add_devices,
                               discover_info=None):
    """Set up the HEOS platform."""
    controller = hass.data[HEOS_DOMAIN][DOMAIN]
    players = controller.get_players()
    devices = [HeosMediaPlayer(p) for p in players]
    async_add_devices(devices, True)


class HeosMediaPlayer(MediaPlayerDevice):
    """The HEOS player."""

    def __init__(self, player):
        """Initialize."""
        self._player = player
        self._position_jitter_acceptance_ms = 500
        self._cache_position_ms = 0
        self._cache_position_at = datetime.now(UTC)

    def _update_state(self):
        self.async_schedule_update_ha_state()

    async def async_update(self):
        """Update the player."""
        self._player.request_update()

    async def async_added_to_hass(self):
        """Device added to hass."""
        self._player.state_change_callback = self._update_state

    @property
    def unique_id(self):
        """Get unique id of the player."""
        return self._player.player_id

    @property
    def name(self):
        """Return the name of the device."""
        return self._player.name

    @property
    def volume_level(self):
        """Volume level of the device (0..1)."""
        volume = self._player.volume
        return float(volume) / 100

    @property
    def state(self):
        """Get state."""
        return PLAY_STATE_TO_STATE.get(self._player.play_state)

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def media_content_type(self):
        """Content type of current playing media."""
        return MEDIA_TYPE_MUSIC

    @property
    def media_artist(self):
        """Artist of current playing media."""
        return self._player.media_artist

    @property
    def media_title(self):
        """Album name of current playing media."""
        return self._player.media_title

    @property
    def media_album_name(self):
        """Album name of current playing media."""
        return self._player.media_album

    @property
    def media_image_url(self):
        """Return the image url of current playing media."""
        return self._player.media_image_url

    @property
    def media_content_id(self):
        """Return the content ID of current playing media."""
        return self._player.media_id

    @property
    def is_volume_muted(self):
        """Boolean if volume is currently muted."""
        return self._player.mute == "on"

    async def async_mute_volume(self, mute):
        """Mute volume."""
        self._player.set_mute(mute)

    @property
    def media_duration(self):
        """Duration of current playing media in seconds."""
        return self._player.duration / 1000.0

    def _get_cache_position(self):
        """Position cache.
        Return cached value if jitter increases above 0,5s."""
        pos_now = self._player.current_position_updated_at
        if not pos_now:
            return (None, None)

        pos_ms = self._player.current_position
        if pos_ms == self._cache_position_ms:
            return (pos_ms / 1000.0, self._cache_position_at)

        delta_pos_at = pos_now - self._cache_position_at
        delta_pos_at_ms = (
            delta_pos_at.seconds * 1000 + delta_pos_at.microseconds / 1000
        )
        delta_pos_ms = abs(pos_ms - self._cache_position_ms)
        jitter_ms = abs(delta_pos_ms - delta_pos_at_ms)
        if jitter_ms > self._position_jitter_acceptance_ms:
            self._cache_position_at = pos_now
            self._cache_position_ms = pos_ms

        return (self._cache_position_ms / 1000.0, self._cache_position_at)

    @property
    def media_position_updated_at(self):
        """Get time when position updated."""
        return self._get_cache_position()[1]

    @property
    def media_position(self):
        """Get media position."""
        return self._get_cache_position()[0]

    async def async_media_next_track(self):
        """Go TO next track."""
        self._player.play_next()

    async def async_media_previous_track(self):
        """Go TO previous track."""
        self._player.play_previous()

    @property
    def supported_features(self):
        """Flag of media commands that are supported."""
        return SUPPORT_HEOS

    async def async_set_volume_level(self, volume):
        """Set volume level, range 0..1."""
        self._player.set_volume(volume * 100)

    async def async_media_play(self):
        """Play media player."""
        self._player.play()

    async def async_media_stop(self):
        """Stop media player."""
        self._player.stop()

    async def async_media_pause(self):
        """Pause media player."""
        self._player.pause()
