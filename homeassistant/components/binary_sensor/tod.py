"""
Support for showing the binary sensors represending current time of the day.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/binary_sensor.tod/

"""
from datetime import datetime, timedelta
import logging
import pytz

import voluptuous as vol

from homeassistant.components.binary_sensor import (
    BinarySensorDevice, ENTITY_ID_FORMAT, PLATFORM_SCHEMA)
from homeassistant.const import (
    CONF_ENTITY_ID, CONF_FRIENDLY_NAME, CONF_AFTER, CONF_BEFORE,
    CONF_SENSORS, SUN_EVENT_SUNRISE, SUN_EVENT_SUNSET)
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import async_generate_entity_id
from homeassistant.helpers.event import async_track_point_in_utc_time
from homeassistant.helpers.sun import (
    get_astral_event_date, get_astral_event_next)
from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)

CONF_AFTER_OFFSET = 'after_offset'
CONF_BEFORE_OFFSET = 'before_offset'

ATTR_NEXT_UPDATE = 'next_update'


SENSOR_SCHEMA = vol.Schema({
    vol.Required(CONF_AFTER): vol.Any(cv.time, vol.All(
        vol.Lower, cv.sun_event)),
    vol.Optional(CONF_AFTER_OFFSET, default=timedelta(0)): cv.time_period,
    vol.Required(CONF_BEFORE): vol.Any(cv.time, vol.All(
        vol.Lower, cv.sun_event)),
    vol.Optional(CONF_BEFORE_OFFSET, default=timedelta(0)): cv.time_period,
    vol.Optional(CONF_FRIENDLY_NAME): cv.string,
})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_SENSORS): vol.Schema({cv.slug: SENSOR_SCHEMA}),
})


async def async_setup_platform(hass, config, async_add_entities,
                               discovery_info=None):
    """Set up the ToD sensors."""
    if hass.config.time_zone is None:
        _LOGGER.error("Timezone is not set in Home Assistant configuration")
        return

    sensors = []
    for name, device_config in config[CONF_SENSORS].items():
        after = device_config[CONF_AFTER]
        after_offset = device_config[CONF_AFTER_OFFSET]
        before = device_config[CONF_BEFORE]
        before_offset = device_config[CONF_BEFORE_OFFSET]
        friendly_name = device_config.get(CONF_FRIENDLY_NAME, name)
        sensors.append(
            TodSensor(
                hass, name, friendly_name, after, after_offset, before, before_offset
            )
        )

    async_add_entities(sensors)


def is_sun_event(event):
    """Return true if event is sun event not time."""
    return event in (SUN_EVENT_SUNRISE, SUN_EVENT_SUNSET)


class TodSensor(BinarySensorDevice):
    """Time of the Day Sensor."""

    def __init__(self, hass, name, friendly_name, after, after_offset,
                 before, before_offset):
        """Init the ToD Sensor..."""
        self.hass = hass
        self.entity_id = async_generate_entity_id(
            ENTITY_ID_FORMAT, name, hass=hass)
        self._name = friendly_name

        self._time_before = None
        self._time_after = None
        self._after_offset = after_offset
        self._before_offset = before_offset
        self._before = before
        self._after = after
        self._next_update = None

        self._calculate_initial_boudary_time()
        self._calculate_next_update()

    @property
    def should_poll(self):
        """Sensor does not need to be polled."""
        return False

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def after(self):
        """Return the timestamp for the begining of the period."""
        return self._time_after

    @property
    def before(self):
        """Return the timestamp for the end of the period."""
        return self._time_before

    @property
    def is_on(self):
        """Return True is senso is on."""
        if self.after < self.before:
            return self.after <= self.current_datetime < self.before
        return False

    @property
    def current_datetime(self):
        """Return local current datetime according to hass configuration."""
        return dt_util.utcnow()

    @property
    def next_update(self):
        """Return the next update point in the UTC time."""
        return self._next_update

    @property
    def state_attributes(self):
        """Return the state attributes of the sun."""
        return {
            CONF_AFTER: self.after.astimezone(
                self.hass.config.time_zone).isoformat(),
            CONF_BEFORE: self.before.astimezone(
                self.hass.config.time_zone).isoformat(),
            ATTR_NEXT_UPDATE: self.next_update.astimezone(
                self.hass.config.time_zone).isoformat(),
        }

    def _calculate_initial_boudary_time(self):
        """Calculate internal absolute time boudaries."""
        nowutc = self.current_datetime
        # if after value is a sun event instead of absolut time
        if is_sun_event(self._after):
            # calculate the today's event utc time or
            # if not available take next
            after_event_date = \
                get_astral_event_date(
                    self.hass, self._after, nowutc) or \
                get_astral_event_next(
                    self.hass, self._after, nowutc)
        else:
            # convert local time provided to UTC today
            # datetime.combine(date, time, tzinfo) is not supported
            # in python 3.5. The self._after is provided
            # with hass configured TZ not system wide
            after_event_date = datetime.combine(
                nowutc, self._after.replace(
                    tzinfo=self.hass.config.time_zone)).astimezone(tz=pytz.UTC)

        self._time_after = after_event_date

        # if before value is a sun event instead of absolut time
        if is_sun_event(self._before):
            # calculate the today's event utc time or
            # if not available take next
            before_event_date = \
                get_astral_event_date(
                    self.hass, self._before, nowutc) or \
                get_astral_event_next(
                    self.hass, self._before, nowutc)
            # before is earler than after
            if before_event_date < after_event_date:
                # take next day for before
                before_event_date = get_astral_event_next(
                    self.hass, self._before, after_event_date)
        else:
            # convert local time provided to UTC today,
            # datetime.combine(date, time, tzinfo) is not supported
            # in python 3.5. The self._after is provided
            # with hass configured TZ not system wide
            before_event_date = datetime.combine(
                nowutc, self._before.replace(
                    tzinfo=self.hass.config.time_zone)).astimezone(tz=pytz.UTC)

            # it is safe to add timedelta days=1 to UTC as there is no DST
            if before_event_date < after_event_date + self._after_offset:
                before_event_date += timedelta(days=1)

        self._time_before = before_event_date

        # add offset to utc boundries according to the configuration
        self._time_after += self._after_offset
        self._time_before += self._before_offset

    def _turn_to_next_day(self):
        """Turn to to the next day."""
        if is_sun_event(self._after):
            self._time_after = get_astral_event_next(
                self.hass, self._after,
                self._time_after - self._after_offset)
            self._time_after += self._after_offset
        else:
            # offset is already there
            self._time_after += timedelta(days=1)

        if is_sun_event(self._before):
            self._time_before = get_astral_event_next(
                self.hass, self._before,
                self._time_before - self._before_offset)
            self._time_before += self._before_offset
        else:
            # offset is already there
            self._time_before += timedelta(days=1)

    async def async_added_to_hass(self):
        """Register callbacks."""
        self.point_in_time_listener(dt_util.now())

    def _calculate_next_update(self):
        """Datetime when the next update to the state."""
        now = self.current_datetime
        if now < self.after:
            self._next_update = self.after
            return
        if now < self.before:
            self._next_update = self.before
            return
        self._turn_to_next_day()
        self._next_update = self.after

    @callback
    def point_in_time_listener(self, now):
        """Run when the state of the sensor should be updated."""
        self._calculate_next_update()
        self.async_schedule_update_ha_state()

        async_track_point_in_utc_time(
            self.hass, self.point_in_time_listener,
            self.next_update)
