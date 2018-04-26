"""
This component provides support for RainMachine programs and zones.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/switch.rainmachine/
"""

from logging import getLogger

from homeassistant.components.rainmachine import (
    CONF_ZONE_RUN_TIME, DATA_RAINMACHINE, DEFAULT_ATTRIBUTION, MIN_SCAN_TIME,
    MIN_SCAN_TIME_FORCED)
from homeassistant.components.switch import SwitchDevice
from homeassistant.const import ATTR_ATTRIBUTION
from homeassistant.util import Throttle

DEPENDENCIES = ['rainmachine']

_LOGGER = getLogger(__name__)

ATTR_AREA = 'area'
ATTR_CS_ON = 'cs_on'
ATTR_CURRENT_CYCLE = 'current_cycle'
ATTR_CURRENT_FIELD_CAPACITY = 'current_field_capacity'
ATTR_CYCLES = 'cycles'
ATTR_DELAY = 'delay'
ATTR_DELAY_ON = 'delay_on'
ATTR_EFFICIENCY = 'sprinkler_head_efficiency'
ATTR_FIELD_CAPACITY = 'field_capacity'
ATTR_FLOW_RATE = 'flow_rate'
ATTR_FREQUENCY = 'frequency'
ATTR_IGNORE_WEATHER = 'ignoring_weather_data'
ATTR_INTAKE_RATE = 'soil_intake_rate'
ATTR_MACHINE_DURATION = 'machine_duration'
ATTR_MASTER_VALVE = 'master_valve'
ATTR_MAX_DEPLETION = 'max_allowed_depletion'
ATTR_NEXT_RUN = 'next_run'
ATTR_NO_CYCLES = 'number_of_cycles'
ATTR_PERM_WILTING = 'permanent_wilting_point'
ATTR_PRECIP_RATE = 'sprinkler_head_precipitation_rate'
ATTR_REFERENCE_TIME = 'suggested_summer_watering_seconds'
ATTR_RESTRICTIONS = 'restrictions'
ATTR_ROOT_DEPTH = 'average_root_depth'
ATTR_SAVINGS = 'savings'
ATTR_SECONDS_REMAINING = 'seconds_remaining'
ATTR_SIMULATION_EXPIRED = 'simulation_expired'
ATTR_SLOPE = 'slope'
ATTR_SOAK = 'soak'
ATTR_SOIL_TYPE = 'soil_type'
ATTR_SPRINKLER_TYPE = 'sprinkler_head_type'
ATTR_START_TIME = 'start_time'
ATTR_STATUS = 'status'
ATTR_SUN_EXPOSURE = 'sun_exposure'
ATTR_SURFACE_ACCUM = 'soil_surface_accumulation'
ATTR_TALL = 'is_tall'
ATTR_TOTAL_DURATION = 'total_duration'
ATTR_USER_DURATION = 'user_duration'
ATTR_USE_WATERSENSE = 'using_watersense'
ATTR_VEGETATION_TYPE = 'vegetation_type'
ATTR_WATER_SKIP = 'watering_percentage_skip_amount'
ATTR_YEARLY_RECURRING = 'yearly_recurring'
ATTR_ZONES = 'zones'

DEFAULT_ZONE_RUN = 60 * 10

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

SOIL_TYPE_MAP = {
    0: 'Not Set',
    1: 'Clay Loam',
    2: 'Silty Clay',
    3: 'Clay',
    4: 'Loam',
    5: 'Sandy Loam',
    6: 'Loamy Sand',
    7: 'Sand',
    8: 'Sandy Clay',
    9: 'Silt Loam',
    10: 'Silt',
    99: 'Other'
}

SLOPE_TYPE_MAP = {
    0: 'Not Set',
    1: 'Flat',
    2: 'Moderate',
    3: 'High',
    4: 'Very High',
    99: 'Other'
}

SPRINKLER_TYPE_MAP = {
    0: 'Not Set',
    1: 'Popup Spray',
    2: 'Rotors',
    3: 'Surface Drip',
    4: 'Bubblers',
    99: 'Other'
}

SUN_EXPOSURE_MAP = {
    0: 'Not Set',
    1: 'Full Sun',
    2: 'Partial Shade',
    3: 'Full Shade'
}

VEGETATION_MAP = {
    0: 'Not Set',
    1: 'Not Set',
    2: 'Grass',
    3: 'Fruit Trees',
    4: 'Flowers',
    5: 'Vegetables',
    6: 'Citrus',
    7: 'Bushes',
    8: 'Xeriscape',
    99: 'Other'
}


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set this component up under its platform."""
    if discovery_info is None:
        return

    _LOGGER.debug('Config received: %s', discovery_info)

    zone_run_time = discovery_info.get(CONF_ZONE_RUN_TIME, DEFAULT_ZONE_RUN)

    client, device_mac = hass.data.get(DATA_RAINMACHINE)

    entities = []
    for program in client.programs.all().get('programs', {}):
        if not program.get('active'):
            continue

        _LOGGER.debug('Adding program: %s', program)
        entities.append(
            RainMachineProgram(client, device_mac, program))

    for zone in client.zones.all().get('zones', {}):
        if not zone.get('active'):
            continue

        _LOGGER.debug('Adding zone: %s', zone)
        entities.append(
            RainMachineZone(client, device_mac, zone,
                            zone_run_time))

    add_devices(entities, True)


class RainMachineEntity(SwitchDevice):
    """A class to represent a generic RainMachine entity."""

    def __init__(self, client, device_mac, entity_json):
        """Initialize a generic RainMachine entity."""
        self._api_type = 'remote' if client.auth.using_remote_api else 'local'
        self._client = client
        self._entity_json = entity_json

        self.device_mac = device_mac

        self._attrs = {
            ATTR_ATTRIBUTION: DEFAULT_ATTRIBUTION
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


class RainMachineProgram(RainMachineEntity):
    """A RainMachine program."""

    def __init__(self, client, device_mac, program_json):
        """Initialize."""
        super().__init__(client, device_mac, program_json)

        self._attrs.update({
            ATTR_CS_ON: self._entity_json['cs_on'],
            ATTR_CYCLES: self._entity_json['cycles'],
            ATTR_DELAY: self._entity_json['delay'],
            ATTR_DELAY_ON: self._entity_json['delay_on'],
            ATTR_FREQUENCY: self._calculate_running_days(),
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
        return 'Program: {0}'.format(self._entity_json.get('name'))

    @property
    def unique_id(self) -> str:
        """Return a unique, HASS-friendly identifier for this entity."""
        return '{0}_program_{1}'.format(
            self.device_mac.replace(':', ''), self.rainmachine_entity_id)

    @property
    def zones(self) -> list:
        """Return a list of active zones associated with this program."""
        return [z for z in self._entity_json['wateringTimes'] if z['active']]

    def _calculate_running_days(self) -> str:
        """Calculate running days from an RM string ("0010001100")."""
        freq_type = self._entity_json['frequency']['type']
        freq_param = self._entity_json['frequency']['param']
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
        from regenmaschine.exceptions import HTTPError

        try:
            self._client.programs.stop(self.rainmachine_entity_id)
        except HTTPError as exc_info:
            _LOGGER.error('Unable to turn off program "%s"', self.unique_id)
            _LOGGER.debug(exc_info)

    def turn_on(self, **kwargs) -> None:
        """Turn the program on."""
        from regenmaschine.exceptions import HTTPError

        try:
            self._client.programs.start(self.rainmachine_entity_id)
        except HTTPError as exc_info:
            _LOGGER.error('Unable to turn on program "%s"', self.unique_id)
            _LOGGER.debug(exc_info)

    @Throttle(MIN_SCAN_TIME, MIN_SCAN_TIME_FORCED)
    def update(self) -> None:
        """Update info for the program."""
        from regenmaschine.exceptions import HTTPError

        try:
            self._entity_json = self._client.programs.get(
                self.rainmachine_entity_id)

            self._attrs.update({
                ATTR_CS_ON: self._entity_json.get('cs_on'),
                ATTR_CYCLES: self._entity_json.get('cycles'),
                ATTR_DELAY: self._entity_json.get('delay'),
                ATTR_DELAY_ON: self._entity_json.get('delay_on'),
                ATTR_FREQUENCY: self._calculate_running_days(),
                ATTR_IGNORE_WEATHER:
                    self._entity_json.get('ignoreInternetWeather'),
                ATTR_NEXT_RUN: self._entity_json.get('nextRun'),
                ATTR_SIMULATION_EXPIRED:
                    self._entity_json.get('simulationExpired'),
                ATTR_SOAK: self._entity_json.get('soak'),
                ATTR_START_TIME: self._entity_json.get('startTime'),
                ATTR_STATUS:
                    PROGRAM_STATUS_MAP[self._entity_json.get('status')],
                ATTR_USE_WATERSENSE: self._entity_json.get('useWaterSense'),
                ATTR_WATER_SKIP: self._entity_json.get('freq_modified'),
                ATTR_YEARLY_RECURRING:
                    self._entity_json.get('yearlyRecurring'),
                ATTR_ZONES: ', '.join(z['name'] for z in self.zones)
            })
        except HTTPError as exc_info:
            _LOGGER.error('Unable to update info for program "%s"',
                          self.unique_id)
            _LOGGER.debug(exc_info)


class RainMachineZone(RainMachineEntity):
    """A RainMachine zone."""

    def __init__(self, client, device_mac, zone_json,
                 zone_run_time):
        """Initialize a RainMachine zone."""
        super().__init__(client, device_mac, zone_json)
        self._properties_json = {}
        self._run_time = zone_run_time

    @property
    def is_on(self) -> bool:
        """Return whether the zone is running."""
        return bool(self._entity_json.get('state'))

    @property
    def name(self) -> str:
        """Return the name of the zone."""
        return 'Zone: {0}'.format(self._entity_json.get('name'))

    @property
    def unique_id(self) -> str:
        """Return a unique, HASS-friendly identifier for this entity."""
        return '{0}_zone_{1}'.format(
            self.device_mac.replace(':', ''), self.rainmachine_entity_id)

    def turn_off(self, **kwargs) -> None:
        """Turn the zone off."""
        from regenmaschine.exceptions import HTTPError

        try:
            self._client.zones.stop(self.rainmachine_entity_id)
        except HTTPError as exc_info:
            _LOGGER.error('Unable to turn off zone "%s"', self.unique_id)
            _LOGGER.debug(exc_info)

    def turn_on(self, **kwargs) -> None:
        """Turn the zone on."""
        from regenmaschine.exceptions import HTTPError

        try:
            self._client.zones.start(self.rainmachine_entity_id,
                                     self._run_time)
        except HTTPError as exc_info:
            _LOGGER.error('Unable to turn on zone "%s"', self.unique_id)
            _LOGGER.debug(exc_info)

    @Throttle(MIN_SCAN_TIME, MIN_SCAN_TIME_FORCED)
    def update(self) -> None:
        """Update info for the zone."""
        from regenmaschine.exceptions import HTTPError

        try:
            self._entity_json = self._client.zones.get(
                self.rainmachine_entity_id)

            self._properties_json = self._client.zones.get(
                self.rainmachine_entity_id, properties=True)

            self._attrs.update({
                ATTR_AREA: self._properties_json.get('waterSense').get('area'),
                ATTR_CURRENT_CYCLE: self._entity_json.get('cycle'),
                ATTR_CURRENT_FIELD_CAPACITY:
                    self._properties_json.get(
                        'waterSense').get('currentFieldCapacity'),
                ATTR_EFFICIENCY:
                    self._properties_json.get(
                        'waterSense').get('appEfficiency'),
                ATTR_FIELD_CAPACITY:
                    self._properties_json.get(
                        'waterSense').get('fieldCapacity'),
                ATTR_FLOW_RATE:
                    self._properties_json.get('waterSense').get('flowRate'),
                ATTR_INTAKE_RATE:
                    self._properties_json.get(
                        'waterSense').get('soilIntakeRate'),
                ATTR_MACHINE_DURATION:
                    self._entity_json.get('machineDuration'),
                ATTR_MASTER_VALVE: self._entity_json.get('master'),
                ATTR_MAX_DEPLETION:
                    self._properties_json.get(
                        'waterSense').get('maxAllowedDepletion'),
                ATTR_NO_CYCLES: self._entity_json.get('noOfCycles'),
                ATTR_PERM_WILTING:
                    self._properties_json.get('waterSense').get('permWilting'),
                ATTR_PRECIP_RATE:
                    self._properties_json.get(
                        'waterSense').get('precipitationRate'),
                ATTR_REFERENCE_TIME:
                    self._properties_json.get(
                        'waterSense').get('referenceTime'),
                ATTR_RESTRICTIONS: self._entity_json.get('restriction'),
                ATTR_ROOT_DEPTH:
                    self._properties_json.get('waterSense').get('rootDepth'),
                ATTR_SAVINGS: self._properties_json.get('savings'),
                ATTR_SECONDS_REMAINING: self._entity_json.get('remaining'),
                ATTR_SLOPE: SLOPE_TYPE_MAP[self._properties_json.get('slope')],
                ATTR_SOIL_TYPE:
                    SOIL_TYPE_MAP[self._properties_json.get('sun')],
                ATTR_SPRINKLER_TYPE:
                    SPRINKLER_TYPE_MAP[self._properties_json.get('group_id')],
                ATTR_SUN_EXPOSURE:
                    SUN_EXPOSURE_MAP[self._properties_json.get('sun')],
                ATTR_SURFACE_ACCUM:
                    self._properties_json.get(
                        'waterSense').get('allowedSurfaceAcc'),
                ATTR_TALL:
                    self._properties_json.get('waterSense').get('isTallPlant'),
                ATTR_USER_DURATION: self._entity_json.get('userDuration'),
                ATTR_VEGETATION_TYPE:
                    VEGETATION_MAP[self._entity_json.get('type')],
            })
        except HTTPError as exc_info:
            _LOGGER.error('Unable to update info for zone "%s"',
                          self.unique_id)
            _LOGGER.debug(exc_info)
