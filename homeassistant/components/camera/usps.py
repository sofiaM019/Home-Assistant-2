"""
Support for a camera made up of usps mail images.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/camera.usps/
"""
import logging

from homeassistant.components.usps import DATA_USPS
from homeassistant.components.camera import Camera

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ['usps']


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up USPS mail camera."""
    if discovery_info is None:
        return

    usps = hass.data[DATA_USPS]
    add_devices([USPSCamera(usps)])


class USPSCamera(Camera):
    """Representation of the images available from USPS."""

    def __init__(self, usps):
        """Initialize the USPS camera images."""
        super(USPSCamera, self).__init__()

        self._usps = usps
        self._name = self._usps.name
        self._session = self._usps.session

        self._mail_img = []
        self._last_mail = None
        self._mail_index = 0
        self._mail_count = 0

    def camera_image(self):
        """Update the camera's image if it has changed."""
        try:
            self._mail_count = len(self._usps.mail)
        except TypeError:
            # No mail
            return None

        if self._usps.mail != self._last_mail:
            # Mail items must have changed
            _LOGGER.debug("Fetching USPS mail images.")
            self._mail_img = []
            if self._usps.mail is not None and len(self._usps.mail) >= 1:
                self._last_mail = self._usps.mail
                for article in self._usps.mail:
                    _LOGGER.debug("Fetching article image: %s", article)
                    img = self._session.get(article['image']).content
                    self._mail_img.append(img)

        if self._mail_index < (self._mail_count - 1):
            self._mail_index += 1
        else:
            self._mail_index = 0

        try:
            return self._mail_img[self._mail_index]
        except IndexError:
            return None

    @property
    def name(self):
        """Return the name of this camera."""
        return '{} mail'.format(self._name)
