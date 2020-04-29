"""Common Met Office Data class used by both sensor and entity."""

import logging

import datapoint

from .const import MODE_3HOURLY

_LOGGER = logging.getLogger(__name__)


class MetOfficeData:
    """Get current and forecast data from Datapoint.

    Please note that the 'datapoint' library is not asyncio-friendly, so some
    calls have had to be wrapped with the standard hassio helper
    async_add_executor_job.
    """

    def __init__(self, hass, api_key, latitude, longitude):
        """Initialize the data object."""
        self._hass = hass
        self._latitude = latitude
        self._longitude = longitude

        self._datapoint = datapoint.connection(api_key=api_key)
        self._site = None

        # Holds the current data from the Met Office
        self.site_id = None
        self.site_name = None
        self.now = None

    @property
    def latitude(self):
        """Return the stored latitude value."""
        return self._latitude

    @latitude.setter
    async def latitude(self, latitude):
        """Update the stored latitude value and flag the DataPoint Site for a possible refresh."""
        if self._latitude != latitude:
            self._latitude = latitude
            await self.async_update_site()

    @property
    def longitude(self):
        """Return the stored longitude value."""
        return self._longitude

    @longitude.setter
    async def longitude(self, longitude):
        """Update the stored longitude value and flag the DataPoint Site for a possible refresh."""
        if self._longitude != longitude:
            self._longitude = longitude
            await self.async_update_site()

    async def async_update_site(self):
        """Async wrapper for getting the DataPoint site."""
        return await self._hass.async_add_executor_job(self._update_site)

    def _update_site(self):
        """Return the stored DataPoint Site (will retrieve an updated one if the latitude/longitude have been updated)."""
        try:
            new_site = self._datapoint.get_nearest_site(
                latitude=self._latitude, longitude=self._longitude
            )
            if self._site is None or self._site.id != new_site.id:
                self._site = new_site
                self.now = None

            self.site_id = self._site.id
            self.site_name = self._site.name

        except datapoint.exceptions.APIException as err:
            _LOGGER.error("Received error from Met Office Datapoint: %s", err)
            self._site = None
            self.site_id = None
            self.site_name = None
            self.now = None

        return self._site

    async def async_update(self):
        """Async wrapper for update method."""
        return await self._hass.async_add_executor_job(self._update)

    def _update(self):
        """Get the latest data from DataPoint."""
        if self._site is None:
            _LOGGER.error("No Met Office forecast site held, check logs for problems")
            return

        try:
            forecast = self._datapoint.get_forecast_for_site(
                self._site.id, MODE_3HOURLY
            )
            self.now = forecast.now()
        except (ValueError, datapoint.exceptions.APIException) as err:
            _LOGGER.error("Check Met Office connection: %s", err.args)
            self.now = None
