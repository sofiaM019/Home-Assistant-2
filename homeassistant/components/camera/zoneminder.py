"""
Support for ZoneMinder camera streaming.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/camera.zoneminder/
"""
import asyncio
import logging

from homeassistant.const import CONF_NAME
from homeassistant.components.camera.mjpeg import (
    CONF_MJPEG_URL, CONF_STILL_IMAGE_URL, MjpegCamera)

from homeassistant.components import zoneminder

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ['zoneminder']
DOMAIN = 'zoneminder'


@asyncio.coroutine
def async_setup_platform(hass, config, async_add_entities,
                         discovery_info=None):
    """Set up the ZoneMinder cameras."""
    from zoneminder.zm import ZoneMinder
    zm: ZoneMinder = hass.data[DOMAIN]

    cameras = []
    monitors = zoneminder.get_state('api/monitors.json')
    if not monitors:
        _LOGGER.warning("Could not fetch monitors from ZoneMinder")
        return

    for i in monitors['monitors']:
        monitor = i['Monitor']

        if monitor['Function'] == 'None':
            _LOGGER.info("Skipping camera %s", monitor['Id'])
            continue

        _LOGGER.info("Initializing camera %s", monitor['Id'])

        device_info = {
            CONF_NAME: monitor['Name'],
            CONF_MJPEG_URL: zm.get_mjpeg_image_url(monitor),
            CONF_STILL_IMAGE_URL: zm.get_still_image_url(monitor)
        }
        cameras.append(ZoneMinderCamera(hass, device_info, monitor))

    if not cameras:
        _LOGGER.warning("No active cameras found")
        return

    async_add_entities(cameras)


class ZoneMinderCamera(MjpegCamera):
    """Representation of a ZoneMinder Monitor Stream."""

    def __init__(self, hass, device_info, monitor):
        """Initialize as a subclass of MjpegCamera."""
        super().__init__(hass, device_info)
        self._monitor_id = int(monitor['Id'])
        self._is_recording = None

    @property
    def should_poll(self):
        """Update the recording state periodically."""
        return True

    def update(self):
        """Update our recording state from the ZM API."""
        _LOGGER.debug("Updating camera state for monitor %i", self._monitor_id)
        status = self.hass.data[DOMAIN].is_recording(self._monitor_id)

        if not status:
            _LOGGER.warning("Could not get status for monitor %i",
                            self._monitor_id)
            return

        self._is_recording = status

    @property
    def is_recording(self):
        """Return whether the monitor is in alarm mode."""
        return self._is_recording
