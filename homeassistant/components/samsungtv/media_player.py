"""Support for interface with an Samsung TV."""
from datetime import timedelta
from functools import partial

import voluptuous as vol

from homeassistant.components.media_player import DEVICE_CLASS_TV, MediaPlayerDevice
from homeassistant.components.media_player.const import (
    MEDIA_TYPE_CHANNEL,
    SUPPORT_NEXT_TRACK,
    SUPPORT_PAUSE,
    SUPPORT_PLAY,
    SUPPORT_PLAY_MEDIA,
    SUPPORT_PREVIOUS_TRACK,
    SUPPORT_SELECT_SOURCE,
    SUPPORT_TURN_OFF,
    SUPPORT_TURN_ON,
    SUPPORT_VOLUME_MUTE,
    SUPPORT_VOLUME_STEP,
)
from homeassistant.const import CONF_ID, CONF_IP_ADDRESS, CONF_NAME, STATE_OFF, STATE_ON
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.script import Script
from homeassistant.util import dt as dt_util

from .const import (
    CONF_MANUFACTURER,
    CONF_MODEL,
    CONF_ON_ACTION,
    DOMAIN,
    KEY_REMOTE,
    LOGGER,
)

KEY_PRESS_TIMEOUT = 1.2
SOURCES = {"TV": "KEY_TV", "HDMI": "KEY_HDMI"}

SUPPORT_SAMSUNGTV = (
    SUPPORT_PAUSE
    | SUPPORT_VOLUME_STEP
    | SUPPORT_VOLUME_MUTE
    | SUPPORT_PREVIOUS_TRACK
    | SUPPORT_SELECT_SOURCE
    | SUPPORT_NEXT_TRACK
    | SUPPORT_TURN_OFF
    | SUPPORT_PLAY
    | SUPPORT_PLAY_MEDIA
)


async def async_setup_platform(
    hass, config, add_entities, discovery_info=None
):  # pragma: no cover
    """Set up the Samsung TV platform."""
    pass


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Samsung TV from a config entry."""
    ip_address = config_entry.data[CONF_IP_ADDRESS]
    on_script = None
    if (
        DOMAIN in hass.data
        and ip_address in hass.data[DOMAIN]
        and CONF_ON_ACTION in hass.data[DOMAIN][ip_address]
        and hass.data[DOMAIN][ip_address][CONF_ON_ACTION]
    ):
        turn_on_action = hass.data[DOMAIN][ip_address][CONF_ON_ACTION]
        on_script = Script(hass, turn_on_action)
    async_add_entities([SamsungTVDevice(config_entry, on_script)])


class SamsungTVDevice(MediaPlayerDevice):
    """Representation of a Samsung TV."""

    def __init__(self, config_entry, on_script):
        """Initialize the Samsung device."""
        self._config_entry = config_entry
        self._manufacturer = config_entry.data.get(CONF_MANUFACTURER)
        self._model = config_entry.data.get(CONF_MODEL)
        self._name = config_entry.data.get(CONF_NAME)
        self._on_script = on_script
        self._uuid = config_entry.data.get(CONF_ID)
        # Assume that the TV is not muted
        self._muted = False
        # Assume that the TV is in Play mode
        self._playing = True
        self._state = None
        # Mark the end of a shutdown command (need to wait 15 seconds before
        # sending the next command to avoid turning the TV back ON).
        self._end_of_power_off = None

    @property
    def _remote(self):
        return self.hass.data[DOMAIN][self._config_entry.entry_id][KEY_REMOTE]

    def update(self):
        """Update state of device."""
        if self._power_off_in_progress():
            self._state = STATE_OFF
        elif self._remote.reconnect():
            self._state = STATE_ON
        else:
            self._state = STATE_OFF

    def send_key(self, key):
        """Send a key to the tv and handles exceptions."""
        if self._power_off_in_progress() and key not in ("KEY_POWER", "KEY_POWEROFF"):
            LOGGER.info("TV is powering off, not sending command: %s", key)
            return
        self._remote.send_command(key)

    def _power_off_in_progress(self):
        return (
            self._end_of_power_off is not None
            and self._end_of_power_off > dt_util.utcnow()
        )

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the device."""
        return self._uuid

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def device_info(self):
        """Return device specific attributes."""
        return {
            "name": self.name,
            "identifiers": {(DOMAIN, self.unique_id)},
            "manufacturer": self._manufacturer,
            "model": self._model,
        }

    @property
    def is_volume_muted(self):
        """Boolean if volume is currently muted."""
        return self._muted

    @property
    def source_list(self):
        """List of available input sources."""
        return list(SOURCES)

    @property
    def supported_features(self):
        """Flag media player features that are supported."""
        if self._on_script:
            return SUPPORT_SAMSUNGTV | SUPPORT_TURN_ON
        return SUPPORT_SAMSUNGTV

    @property
    def device_class(self):
        """Set the device class to TV."""
        return DEVICE_CLASS_TV

    def turn_off(self):
        """Turn off media player."""
        self._end_of_power_off = dt_util.utcnow() + timedelta(seconds=15)

        if self._config["method"] == "websocket":
            self.send_key("KEY_POWER")
        else:
            self.send_key("KEY_POWEROFF")
        # Force closing of remote session to provide instant UI feedback
        try:
            self._remote.close()
        except OSError:
            LOGGER.debug("Could not establish connection.")

    def volume_up(self):
        """Volume up the media player."""
        self.send_key("KEY_VOLUP")

    def volume_down(self):
        """Volume down media player."""
        self.send_key("KEY_VOLDOWN")

    def mute_volume(self, mute):
        """Send mute command."""
        self.send_key("KEY_MUTE")

    def media_play_pause(self):
        """Simulate play pause media player."""
        if self._playing:
            self.media_pause()
        else:
            self.media_play()

    def media_play(self):
        """Send play command."""
        self._playing = True
        self.send_key("KEY_PLAY")

    def media_pause(self):
        """Send media pause command to media player."""
        self._playing = False
        self.send_key("KEY_PAUSE")

    def media_next_track(self):
        """Send next track command."""
        self.send_key("KEY_CHUP")

    def media_previous_track(self):
        """Send the previous track command."""
        self.send_key("KEY_CHDOWN")

    async def async_play_media(self, media_type, media_id, **kwargs):
        """Support changing a channel."""
        if media_type != MEDIA_TYPE_CHANNEL:
            LOGGER.error("Unsupported media type")
            return

        # media_id should only be a channel number
        try:
            cv.positive_int(media_id)
        except vol.Invalid:
            LOGGER.error("Media ID must be positive integer")
            return

        keys = list(f"KEY_{digit}" for digit in media_id) + ["KEY_ENTER"]
        await self.hass.async_add_executor_job(
            partial(self._remote.send_commands, keys, KEY_PRESS_TIMEOUT)
        )

    async def async_turn_on(self):
        """Turn the media player on."""
        if self._on_script:
            await self._on_script.async_run()

    def select_source(self, source):
        """Select input source."""
        if source not in SOURCES:
            LOGGER.error("Unsupported source")
            return

        self.send_key(SOURCES[source])
