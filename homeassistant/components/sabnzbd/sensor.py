"""Support for monitoring an SABnzbd NZB client."""
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from . import DATA_SABNZBD, SENSOR_TYPES, SIGNAL_SABNZBD_UPDATED


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the SABnzbd sensors."""
    if discovery_info is None:
        return

    sab_api_data = hass.data[DATA_SABNZBD]
    sensors = sab_api_data.sensors
    client_name = sab_api_data.name
    async_add_entities(
        [
            SabnzbdSensor(SENSOR_TYPES[sensor], sab_api_data, client_name)
            for sensor in sensors
        ]
    )


class SabnzbdSensor(SensorEntity):
    """Representation of an SABnzbd sensor."""

    _attr_should_poll = False

    def __init__(self, myDescription, sabnzbd_api_data, client_name):
        """Initialize the sensor."""
        self.entity_description = myDescription
        self._field_name = self.entity_description.key
        self._sabnzbd_api = sabnzbd_api_data
        self._attr_state = None
        self.entity_description.name = f"{client_name} {self.entity_description.name}"

    async def async_added_to_hass(self):
        """Call when entity about to be added to hass."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, SIGNAL_SABNZBD_UPDATED, self.update_state
            )
        )

    def update_state(self, args):
        """Get the latest data and updates the states."""
        new_state = self._sabnzbd_api.get_queue_field(self._field_name)

        if self.entity_description.key == "kbpersec":
            self._attr_state = round(float(new_state) / 1024, 1)
        elif self.entity_description.key in ("mb", "diskspacetotal1", "day_size", "week_size", "month_size", "total_size"):
            self._attr_state = round(float(new_state), 2)
        else:
            self._attr_state = new_state

        self.schedule_update_ha_state()
