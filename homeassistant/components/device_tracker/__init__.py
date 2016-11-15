"""
Provide functionality to keep track of devices.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/device_tracker/
"""
import asyncio
from datetime import timedelta
import logging
import os
import threading
from typing import Any, Sequence, Callable

import voluptuous as vol

from homeassistant.bootstrap import (
    async_prepare_setup_platform, log_exception)
from homeassistant.core import callback
from homeassistant.components import group, zone
from homeassistant.components.discovery import SERVICE_NETGEAR
from homeassistant.config import load_yaml_config_file
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_per_platform, discovery
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.typing import GPSType, ConfigType, HomeAssistantType
import homeassistant.helpers.config_validation as cv
import homeassistant.util as util
from homeassistant.util.async import run_coroutine_threadsafe
import homeassistant.util.dt as dt_util
from homeassistant.util.yaml import dump

from homeassistant.helpers.event import async_track_utc_time_change
from homeassistant.const import (
    ATTR_GPS_ACCURACY, ATTR_LATITUDE, ATTR_LONGITUDE,
    DEVICE_DEFAULT_NAME, STATE_HOME, STATE_NOT_HOME, ATTR_ENTITY_ID)

DOMAIN = 'device_tracker'
DEPENDENCIES = ['zone']

GROUP_NAME_ALL_DEVICES = 'all devices'
ENTITY_ID_ALL_DEVICES = group.ENTITY_ID_FORMAT.format('all_devices')

ENTITY_ID_FORMAT = DOMAIN + '.{}'

YAML_DEVICES = 'known_devices.yaml'

CONF_TRACK_NEW = 'track_new_devices'
DEFAULT_TRACK_NEW = True

CONF_CONSIDER_HOME = 'consider_home'
DEFAULT_CONSIDER_HOME = 180

CONF_SCAN_INTERVAL = 'interval_seconds'
DEFAULT_SCAN_INTERVAL = 12

CONF_AWAY_HIDE = 'hide_if_away'
DEFAULT_AWAY_HIDE = False

EVENT_NEW_DEVICE = 'device_tracker_new_device'

SERVICE_SEE = 'see'

ATTR_MAC = 'mac'
ATTR_DEV_ID = 'dev_id'
ATTR_HOST_NAME = 'host_name'
ATTR_LOCATION_NAME = 'location_name'
ATTR_GPS = 'gps'
ATTR_BATTERY = 'battery'
ATTR_ATTRIBUTES = 'attributes'

PLATFORM_SCHEMA = cv.PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_SCAN_INTERVAL): cv.positive_int,  # seconds
    vol.Optional(CONF_TRACK_NEW, default=DEFAULT_TRACK_NEW): cv.boolean,
    vol.Optional(CONF_CONSIDER_HOME,
                 default=timedelta(seconds=DEFAULT_CONSIDER_HOME)): vol.All(
                     cv.time_period, cv.positive_timedelta)
})

DISCOVERY_PLATFORMS = {
    SERVICE_NETGEAR: 'netgear',
}
_LOGGER = logging.getLogger(__name__)


def is_on(hass: HomeAssistantType, entity_id: str=None):
    """Return the state if any or a specified device is home."""
    entity = entity_id or ENTITY_ID_ALL_DEVICES

    return hass.states.is_state(entity, STATE_HOME)


def see(hass: HomeAssistantType, mac: str=None, dev_id: str=None,
        host_name: str=None, location_name: str=None,
        gps: GPSType=None, gps_accuracy=None,
        battery=None, attributes: dict=None):
    """Call service to notify you see device."""
    data = {key: value for key, value in
            ((ATTR_MAC, mac),
             (ATTR_DEV_ID, dev_id),
             (ATTR_HOST_NAME, host_name),
             (ATTR_LOCATION_NAME, location_name),
             (ATTR_GPS, gps),
             (ATTR_GPS_ACCURACY, gps_accuracy),
             (ATTR_BATTERY, battery)) if value is not None}
    if attributes:
        data[ATTR_ATTRIBUTES] = attributes
    hass.services.call(DOMAIN, SERVICE_SEE, data)


@asyncio.coroutine
def async_setup(hass: HomeAssistantType, config: ConfigType):
    """Setup device tracker."""
    yaml_path = hass.config.path(YAML_DEVICES)

    try:
        conf = config.get(DOMAIN, [])
    except vol.Invalid as ex:
        log_exception(ex, DOMAIN, config, hass)
        return False
    else:
        conf = conf[0] if len(conf) > 0 else {}
        consider_home = conf.get(CONF_CONSIDER_HOME,
                                 timedelta(seconds=DEFAULT_CONSIDER_HOME))
        track_new = conf.get(CONF_TRACK_NEW, DEFAULT_TRACK_NEW)

    devices = yield from async_load_config(yaml_path, hass, consider_home)

    tracker = DeviceTracker(hass, consider_home, track_new, devices)

    @asyncio.coroutine
    def async_setup_platform(p_type, p_config, disc_info=None):
        """Setup a device tracker platform."""
        platform = yield from async_prepare_setup_platform(
            hass, config, DOMAIN, p_type)
        if platform is None:
            return

        try:
            if hasattr(platform, 'get_scanner'):
                scanner = yield from hass.loop.run_in_executor(
                    None, platform.get_scanner, hass, {DOMAIN: p_config})

                if scanner is None:
                    _LOGGER.error('Error setting up platform %s', p_type)
                    return

                yield from async_setup_scanner_platform(
                    hass, p_config, scanner, tracker.async_see)
                return

            ret = yield from hass.loop.run_in_executor(
                None, platform.setup_scanner, hass, p_config, tracker.see)
            if not ret:
                _LOGGER.error('Error setting up platform %s', p_type)
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception('Error setting up platform %s', p_type)

    setup_tasks = [async_setup_platform(p_type, p_config) for p_type, p_config
                   in config_per_platform(config, DOMAIN)]
    yield from asyncio.wait(setup_tasks, loop=hass.loop)
    yield from tracker.async_setup_group()

    @callback
    def async_device_tracker_discovered(service, info):
        """Called when a device tracker platform is discovered."""
        hass.async_add_job(
            async_setup_platform(DISCOVERY_PLATFORMS[service], {}, info))

    discovery.async_listen(
        hass, DISCOVERY_PLATFORMS.keys(), async_device_tracker_discovered)

    # Clean up stale devices
    async_track_utc_time_change(
        hass, tracker.async_update_stale, second=range(0, 60, 5))

    @asyncio.coroutine
    def async_see_service(call):
        """Service to see a device."""
        args = {key: value for key, value in call.data.items() if key in
                (ATTR_MAC, ATTR_DEV_ID, ATTR_HOST_NAME, ATTR_LOCATION_NAME,
                 ATTR_GPS, ATTR_GPS_ACCURACY, ATTR_BATTERY, ATTR_ATTRIBUTES)}
        yield from tracker.async_see(**args)

    descriptions = hass.loop.run_in_executor(
        None, load_yaml_config_file,
        os.path.join(os.path.dirname(__file__), 'services.yaml')
    )
    hass.services.async_register(
        DOMAIN, SERVICE_SEE, async_see_service, descriptions.get(SERVICE_SEE))

    return True


class DeviceTracker(object):
    """Representation of a device tracker."""

    def __init__(self, hass: HomeAssistantType, consider_home: timedelta,
                 track_new: bool, devices: Sequence) -> None:
        """Initialize a device tracker."""
        self.hass = hass
        self.devices = {dev.dev_id: dev for dev in devices}
        self.mac_to_dev = {dev.mac: dev for dev in devices if dev.mac}
        for dev in devices:
            if self.devices[dev.dev_id] is not dev:
                _LOGGER.warning('Duplicate device IDs detected %s', dev.dev_id)
            if dev.mac and self.mac_to_dev[dev.mac] is not dev:
                _LOGGER.warning('Duplicate device MAC addresses detected %s',
                                dev.mac)
        self.consider_home = consider_home
        self.track_new = track_new

        for device in devices:
            if device.track:
                hass.async_add_job(device.async_update_ha_state())

        self.group = None  # type: group.Group

    def see(self, mac: str=None, dev_id: str=None, host_name: str=None,
            location_name: str=None, gps: GPSType=None, gps_accuracy=None,
            battery: str=None, attributes: dict=None):
        """Notify the device tracker that you see a device."""
        run_coroutine_threadsafe(
            self.async_see(mac, dev_id, host_name, location_name, gps,
                           battery, attributes), loop=self.hass.loop).result()

    def async_see(self, mac: str=None, dev_id: str=None, host_name: str=None,
                  location_name: str=None, gps: GPSType=None,
                  gps_accuracy=None, battery: str=None, attributes: dict=None):
        """Notify the device tracker that you see a device.

        This method is a coroutine.
        """
        if mac is None and dev_id is None:
            raise HomeAssistantError('Neither mac or device id passed in')
        elif mac is not None:
            mac = str(mac).upper()
            device = self.mac_to_dev.get(mac)
            if not device:
                dev_id = util.slugify(host_name or '') or util.slugify(mac)
        else:
            dev_id = cv.slug(str(dev_id).lower())
            device = self.devices.get(dev_id)

        if device:
            device.seen(host_name, location_name, gps, gps_accuracy,
                        battery, attributes)
            if device.track:
                device.update_ha_state()
            return

        # If no device can be found, create it
        dev_id = util.ensure_unique_string(dev_id, self.devices.keys())
        device = Device(
            self.hass, self.consider_home, self.track_new,
            dev_id, mac, (host_name or dev_id).replace('_', ' '))
        self.devices[dev_id] = device
        if mac is not None:
            self.mac_to_dev[mac] = device

        yield from self.hass.loop.run_in_executor(
            None, device.seen, host_name, location_name, gps, gps_accuracy,
            battery, attributes)

        if device.track:
            yield from device.async_update_ha_state()

        self.hass.bus.async_fire(EVENT_NEW_DEVICE, {
            ATTR_ENTITY_ID: device.entity_id,
            ATTR_HOST_NAME: device.host_name,
        })

        # During init, we ignore the group
        if self.group is not None:
            yield from self.async_group.update_tracked_entity_ids(
                list(self.group.tracking) + [device.entity_id])

        # update known_devices.yaml
        yield from self.hass.run_in_executor(
            None, update_config, self.hass.config.path(YAML_DEVICES),
            dev_id, device
        )

    @asyncio.coroutine
    def async_setup_group(self):
        """Initialize group for all tracked devices.

        This method is a coroutine.
        """
        entity_ids = (dev.entity_id for dev in self.devices.values()
                      if dev.track)
        self.group = yield from group.Group.async_create_group(
            self.hass, GROUP_NAME_ALL_DEVICES, entity_ids, False)

    @asyncio.coroutine
    def async_update_stale(self, now: dt_util.dt.datetime):
        """Update stale devices.

        This method is a coroutine.
        """
        for device in self.devices.values():
            if (device.track and device.last_update_home) and \
               device.stale(now):
                self.hass_async_add_job(device.async_update_ha_state(True))


class Device(Entity):
    """Represent a tracked device."""

    host_name = None  # type: str
    location_name = None  # type: str
    gps = None  # type: GPSType
    gps_accuracy = 0
    last_seen = None  # type: dt_util.dt.datetime
    battery = None  # type: str
    attributes = None  # type: dict

    # Track if the last update of this device was HOME.
    last_update_home = False
    _state = STATE_NOT_HOME

    def __init__(self, hass: HomeAssistantType, consider_home: timedelta,
                 track: bool, dev_id: str, mac: str, name: str=None,
                 picture: str=None, gravatar: str=None,
                 hide_if_away: bool=False) -> None:
        """Initialize a device."""
        self.hass = hass
        self.entity_id = ENTITY_ID_FORMAT.format(dev_id)

        # Timedelta object how long we consider a device home if it is not
        # detected anymore.
        self.consider_home = consider_home

        # Device ID
        self.dev_id = dev_id
        self.mac = mac

        # If we should track this device
        self.track = track

        # Configured name
        self.config_name = name

        # Configured picture
        if gravatar is not None:
            self.config_picture = get_gravatar_for_email(gravatar)
        else:
            self.config_picture = picture

        self.away_hide = hide_if_away

    @property
    def name(self):
        """Return the name of the entity."""
        return self.config_name or self.host_name or DEVICE_DEFAULT_NAME

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def entity_picture(self):
        """Return the picture of the device."""
        return self.config_picture

    @property
    def state_attributes(self):
        """Return the device state attributes."""
        attr = {}

        if self.gps:
            attr[ATTR_LATITUDE] = self.gps[0]
            attr[ATTR_LONGITUDE] = self.gps[1]
            attr[ATTR_GPS_ACCURACY] = self.gps_accuracy

        if self.battery:
            attr[ATTR_BATTERY] = self.battery

        if self.attributes:
            for key, value in self.attributes.items():
                attr[key] = value

        return attr

    @property
    def hidden(self):
        """If device should be hidden."""
        return self.away_hide and self.state != STATE_HOME

    def seen(self, host_name: str=None, location_name: str=None,
             gps: GPSType=None, gps_accuracy=0, battery: str=None,
             attributes: dict=None):
        """Mark the device as seen."""
        self.last_seen = dt_util.utcnow()
        self.host_name = host_name
        self.location_name = location_name
        self.gps_accuracy = gps_accuracy or 0
        self.battery = battery
        self.attributes = attributes
        self.gps = None
        if gps is not None:
            try:
                self.gps = float(gps[0]), float(gps[1])
            except (ValueError, TypeError, IndexError):
                _LOGGER.warning('Could not parse gps value for %s: %s',
                                self.dev_id, gps)
        self.update()

    def stale(self, now: dt_util.dt.datetime=None):
        """Return if device state is stale.

        Async friendly.
        """
        return self.last_seen and \
            (now or dt_util.utcnow()) - self.last_seen > self.consider_home

    def update(self):
        """Update state of entity."""
        if not self.last_seen:
            return
        elif self.location_name:
            self._state = self.location_name
        elif self.gps is not None:
            zone_state = zone.active_zone(self.hass, self.gps[0], self.gps[1],
                                          self.gps_accuracy)
            if zone_state is None:
                self._state = STATE_NOT_HOME
            elif zone_state.entity_id == zone.ENTITY_ID_HOME:
                self._state = STATE_HOME
            else:
                self._state = zone_state.name

        elif self.stale():
            self._state = STATE_NOT_HOME
            self.last_update_home = False
        else:
            self._state = STATE_HOME
            self.last_update_home = True


@asyncio.coroutine
def async_load_config(path: str, hass: HomeAssistantType,
                      consider_home: timedelta):
    """Load devices from YAML configuration file.

    This method is a coroutine.
    """
    dev_schema = vol.Schema({
        vol.Required('name'): cv.string,
        vol.Optional('track', default=False): cv.boolean,
        vol.Optional('mac', default=None): vol.Any(None, vol.All(cv.string,
                                                                 vol.Upper)),
        vol.Optional(CONF_AWAY_HIDE, default=DEFAULT_AWAY_HIDE): cv.boolean,
        vol.Optional('gravatar', default=None): vol.Any(None, cv.string),
        vol.Optional('picture', default=None): vol.Any(None, cv.string),
        vol.Optional(CONF_CONSIDER_HOME, default=consider_home): vol.All(
            cv.time_period, cv.positive_timedelta)
    })
    try:
        result = []
        try:
            devices = yield from hass.loop.run_in_executor(
                None, load_yaml_config_file, path)
        except HomeAssistantError as err:
            _LOGGER.error('Unable to load %s: %s', path, str(err))
            return []

        for dev_id, device in devices.items():
            try:
                device = dev_schema(device)
                device['dev_id'] = cv.slugify(dev_id)
            except vol.Invalid as exp:
                log_exception(exp, dev_id, devices, hass)
            else:
                result.append(Device(hass, **device))
        return result
    except (HomeAssistantError, FileNotFoundError):
        # When YAML file could not be loaded/did not contain a dict
        return []


@asyncio.coroutine
def async_setup_scanner_platform(hass: HomeAssistantType, config: ConfigType,
                                 scanner: Any, async_see_device: Callable):
    """Helper method to connect scanner-based platform to device tracker.

    This method is a coroutine.
    """
    interval = config.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    # Initial scan of each mac we also tell about host name for config
    seen = set()  # type: Any

    def device_tracker_scan(now: dt_util.dt.datetime):
        """Called when interval matches."""
        found_devices = scanner.scan_devices()

        for mac in found_devices:
            if mac in seen:
                host_name = None
            else:
                host_name = scanner.get_device_name(mac)
                seen.add(mac)
            hass.async_add_job(async_see_device(mac=mac, host_name=host_name))

        return tasks

    async_track_utc_time_change(
        hass, device_tracker_scan, second=range(0, 60, interval))

    hass.async_add_job(device_tracker_scan(None))


def update_config(path: str, dev_id: str, device: Device):
    """Add device to YAML configuration file."""
    with open(path, 'a') as out:
        device = {device.dev_id: {
            'name': device.name,
            'mac': device.mac,
            'picture': device.config_picture,
            'track': device.track,
            CONF_AWAY_HIDE: device.away_hide
        }}
        out.write('\n')
        out.write(dump(device))


def get_gravatar_for_email(email: str):
    """Return an 80px Gravatar for the given email address."""
    import hashlib
    url = 'https://www.gravatar.com/avatar/{}.jpg?s=80&d=wavatar'
    return url.format(hashlib.md5(email.encode('utf-8').lower()).hexdigest())
