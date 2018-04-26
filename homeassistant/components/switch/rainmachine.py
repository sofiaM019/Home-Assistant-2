"""Implements a RainMachine sprinkler controller for Home Assistant."""

from logging import getLogger

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.rainmachine import (
    DATA_RAINMACHINE, aware_throttle)
from homeassistant.components.switch import PLATFORM_SCHEMA, SwitchDevice
from homeassistant.const import ATTR_ATTRIBUTION, ATTR_DEVICE_CLASS

_LOGGER = getLogger(__name__)
DEPENDENCIES = ['rainmachine']

ATTR_CS_ON = 'cs_on'
ATTR_CYCLES = 'cycles'
ATTR_DELAY = 'delay'
ATTR_DELAY_ON = 'delay_on'
ATTR_FREQUENCY = 'frequency'
ATTR_SOAK = 'soak'
ATTR_START_TIME = 'start_time'
ATTR_STATUS = 'status'
ATTR_TOTAL_DURATION = 'total_duration'

CONF_ZONE_RUN_TIME = 'zone_run_time'

DEFAULT_ZONE_RUN_SECONDS = 60 * 10

DAYS = [
    'Monday',
    'Tuesday',
    'Wednesday',
    'Thursday',
    'Friday',
    'Saturday',
    'Sunday'
]

PROGRAM_STATUS_MAP = {
    0: 'Not Running',
    1: 'Running',
    2: 'Queued'
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_ZONE_RUN_TIME, default=DEFAULT_ZONE_RUN_SECONDS):
        cv.positive_int
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set this component up under its platform."""
    client = hass.data.get(DATA_RAINMACHINE)
    device_name = client.provision.device_name()['name']
    device_mac = client.provision.wifi()['macAddress']

    _LOGGER.debug('Config received: %s', config)

    zone_run_time = config[CONF_ZONE_RUN_TIME]

    entities = []
    for program in client.programs.all().get('programs', {}):
        if not program.get('active'):
            continue

        _LOGGER.debug('Adding program: %s', program)
        entities.append(
            RainMachineProgram(
                client,
                device_name,
                device_mac,
                program))

    for zone in client.zones.all().get('zones', {}):
        if not zone.get('active'):
            continue

        _LOGGER.debug('Adding zone: %s', zone)
        entities.append(
            RainMachineZone(
                client,
                device_name,
                device_mac,
                zone,
                zone_run_time))

    add_devices(entities, True)


class RainMachineEntity(SwitchDevice):
    """A class to represent a generic RainMachine entity."""

    def __init__(self, client, device_name, device_mac, entity_json):
        """Initialize a generic RainMachine entity."""
        self._api_type = 'remote' if client.auth.using_remote_api else 'local'
        self._client = client
        self._entity_json = entity_json

        self.device_mac = device_mac
        self.device_name = device_name

        self._attrs = {
            ATTR_ATTRIBUTION: '© RainMachine',
            ATTR_DEVICE_CLASS: self.device_name
        }

    @property
    def device_state_attributes(self) -> dict:
        """Return the state attributes."""
        return self._attrs

    @property
    def icon(self) -> str:
        """Return the icon."""
        return 'mdi:water'

    @property
    def is_enabled(self) -> bool:
        """Return whether the entity is enabled."""
        return self._entity_json.get('active')

    @property
    def rainmachine_entity_id(self) -> int:
        """Return the RainMachine ID for this entity."""
        return self._entity_json.get('uid')

    @aware_throttle('local')
    def _local_update(self) -> None:
        """Call an update with scan times appropriate for the local API."""
        self._update()

    @aware_throttle('remote')
    def _remote_update(self) -> None:
        """Call an update with scan times appropriate for the remote API."""
        self._update()

    def _update(self) -> None:  # pylint: disable=no-self-use
        """Logic for update method, regardless of API type."""
        raise NotImplementedError()

    def update(self) -> None:
        """Determine how the entity updates itself."""
        if self._api_type == 'remote':
            self._remote_update()
        else:
            self._local_update()


class RainMachineProgram(RainMachineEntity):
    """A RainMachine program."""

    def __init__(self, client, device_name, device_mac, program_json):
        """Initialize."""
        super().__init__(client, device_name, device_mac, program_json)

        frequency = calculate_running_days(
            self._entity_json['frequency']['type'],
            self._entity_json['frequency']['param'])

        self._attrs.update({
            ATTR_CS_ON: self._entity_json['cs_on'],
            ATTR_CYCLES: self._entity_json['cycles'],
            ATTR_DELAY: self._entity_json['delay'],
            ATTR_DELAY_ON: self._entity_json['delay_on'],
            ATTR_FREQUENCY: frequency,
            ATTR_SOAK: self._entity_json['soak'],
            ATTR_START_TIME: self._entity_json['startTime'],
            ATTR_STATUS: PROGRAM_STATUS_MAP[self._entity_json['status']]
        })

    @property
    def is_on(self) -> bool:
        """Return whether the program is running."""
        return bool(self._entity_json.get('status'))

    @property
    def name(self) -> str:
        """Return the name of the program."""
        return 'Program: {}'.format(self._entity_json.get('name'))

    @property
    def unique_id(self) -> str:
        """Return a unique, HASS-friendly identifier for this entity."""
        return '{0}_program_{1}'.format(
            self.device_mac.replace(':', ''), self.rainmachine_entity_id)

    @staticmethod
    def calculate_running_days(freq_type: int, freq_param: str) -> str:
        """Calculates running days from an RM string ("0010001100")."""
        if freq_type == 0:
            return 'Daily'

        if freq_type == 1:
            return 'Every {0} Days'.format(freq_param)

        if freq_type == 2:
            return ', '.join([
                DAYS[idx] for idx, val in enumerate(freq_param[2:-1][::-1])
                if val == '1'
            ])

        if freq_type == 4:
            return '{0} Days'.format('Odd' if freq_param == '1' else 'Even')

        return None

    def turn_off(self, **kwargs) -> None:
        """Turn the program off."""
        import regenmaschine.exceptions as exceptions

        try:
            self._client.programs.stop(self.rainmachine_entity_id)
        except exceptions.BrokenAPICall:
            _LOGGER.error('programs.stop currently broken in remote API')
        except exceptions.HTTPError as exc_info:
            _LOGGER.error('Unable to turn off program "%s"', self.unique_id)
            _LOGGER.debug(exc_info)

    def turn_on(self, **kwargs) -> None:
        """Turn the program on."""
        import regenmaschine.exceptions as exceptions

        try:
            self._client.programs.start(self.rainmachine_entity_id)
        except exceptions.BrokenAPICall:
            _LOGGER.error('programs.start currently broken in remote API')
        except exceptions.HTTPError as exc_info:
            _LOGGER.error('Unable to turn on program "%s"', self.unique_id)
            _LOGGER.debug(exc_info)

    def _update(self) -> None:
        """Update info for the program."""
        import regenmaschine.exceptions as exceptions

        try:
            self._entity_json = self._client.programs.get(
                self.rainmachine_entity_id)
        except exceptions.HTTPError as exc_info:
            _LOGGER.error('Unable to update info for program "%s"',
                          self.unique_id)
            _LOGGER.debug(exc_info)


class RainMachineZone(RainMachineEntity):
    """A RainMachine zone."""

    def __init__(self, client, device_name, device_mac, zone_json,
                 zone_run_time):
        """Initialize a RainMachine zone."""
        super().__init__(client, device_name, device_mac, zone_json)
        self._run_time = zone_run_time
        self._attrs.update({
            ATTR_CYCLES: self._entity_json.get('noOfCycles'),
            ATTR_TOTAL_DURATION: self._entity_json.get('userDuration')
        })

    @property
    def is_on(self) -> bool:
        """Return whether the zone is running."""
        return bool(self._entity_json.get('state'))

    @property
    def name(self) -> str:
        """Return the name of the zone."""
        return 'Zone: {}'.format(self._entity_json.get('name'))

    @property
    def unique_id(self) -> str:
        """Return a unique, HASS-friendly identifier for this entity."""
        return '{0}_zone_{1}'.format(
            self.device_mac.replace(':', ''), self.rainmachine_entity_id)

    def turn_off(self, **kwargs) -> None:
        """Turn the zone off."""
        import regenmaschine.exceptions as exceptions

        try:
            self._client.zones.stop(self.rainmachine_entity_id)
        except exceptions.HTTPError as exc_info:
            _LOGGER.error('Unable to turn off zone "%s"', self.unique_id)
            _LOGGER.debug(exc_info)

    def turn_on(self, **kwargs) -> None:
        """Turn the zone on."""
        import regenmaschine.exceptions as exceptions

        try:
            self._client.zones.start(self.rainmachine_entity_id,
                                     self._run_time)
        except exceptions.HTTPError as exc_info:
            _LOGGER.error('Unable to turn on zone "%s"', self.unique_id)
            _LOGGER.debug(exc_info)

    def _update(self) -> None:
        """Update info for the zone."""
        import regenmaschine.exceptions as exceptions

        try:
            self._entity_json = self._client.zones.get(
                self.rainmachine_entity_id)
        except exceptions.HTTPError as exc_info:
            _LOGGER.error('Unable to update info for zone "%s"',
                          self.unique_id)
            _LOGGER.debug(exc_info)
