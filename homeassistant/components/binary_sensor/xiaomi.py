"""Support for Xiaomi binary sensors."""
import logging

from homeassistant.components.binary_sensor import BinarySensorDevice
from homeassistant.components.xiaomi import (PY_XIAOMI_GATEWAY, XiaomiDevice)

_LOGGER = logging.getLogger(__name__)

NO_CLOSE = 'no_close'
ATTR_OPEN_SINCE = 'Open since'

MOTION = 'motion'
NO_MOTION = 'no_motion'
ATTR_NO_MOTION_SINCE = 'No motion since'

DENSITY = 'density'
ATTR_DENSITY = 'Density'


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Perform the setup for Xiaomi devices."""
    devices = []
    for (_, gateway) in hass.data[PY_XIAOMI_GATEWAY].gateways.items():
        for device in gateway.devices['binary_sensor']:
            model = device['model']
            if model == 'motion':
                devices.append(XiaomiMotionSensor(device, hass, gateway))
            elif model == 'magnet':
                devices.append(XiaomiDoorSensor(device, gateway))
            elif model == 'smoke':
                devices.append(XiaomiSmokeSensor(device, gateway))
            elif model == 'natgas':
                devices.append(XiaomiNatgasSensor(device, gateway))
            elif model == 'switch':
                devices.append(XiaomiButton(device, 'Switch', 'status',
                                            hass, gateway))
            elif model == 'sensor_switch.aq2':
                devices.append(XiaomiButton(device, 'Switch', 'status',
                                            hass, gateway))
            elif model == '86sw1':
                devices.append(XiaomiButton(device, 'Wall Switch', 'channel_0',
                                            hass, gateway))
            elif model == '86sw2':
                devices.append(XiaomiButton(device, 'Wall Switch (Left)',
                                            'channel_0', hass, gateway))
                devices.append(XiaomiButton(device, 'Wall Switch (Right)',
                                            'channel_1', hass, gateway))
                devices.append(XiaomiButton(device, 'Wall Switch (Both)',
                                            'dual_channel', hass, gateway))
            elif model == 'cube':
                devices.append(XiaomiCube(device, hass, gateway))
    add_devices(devices)


class XiaomiBinarySensor(XiaomiDevice, BinarySensorDevice):
    """Representation of a XiaomiBinarySensor."""

    def __init__(self, device, name, xiaomi_hub):
        """Initialize the XiaomiSmokeSensor."""
        self._data_key = None
        self._device_class = None
        self._density = 0
        XiaomiDevice.__init__(self, device, name, xiaomi_hub)

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def device_class(self):
        """Return the class of binary sensor."""
        return self._device_class


class XiaomiNatgasSensor(XiaomiBinarySensor):
    """Representation of a XiaomiNatgasSensor."""

    def __init__(self, device, xiaomi_hub):
        """Initialize the XiaomiSmokeSensor."""
        self._data_key = 'alarm'
        self._density = None
        self._device_class = 'gas'
        XiaomiBinarySensor.__init__(self, device, 'Natgas Sensor', xiaomi_hub)

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        attrs = {ATTR_DENSITY: self._density}
        attrs.update(super().device_state_attributes)
        return attrs

    def parse_data(self, data):
        """Parse data sent by gateway."""
        if DENSITY in data:
            self._density = int(data.get(DENSITY))

        value = data.get(self._data_key)
        if value is None:
            return False

        if value == '1':
            if self._state:
                return False
            self._state = True
            return True
        elif value == '0':
            if self._state:
                self._state = False
                return True
            return False


class XiaomiMotionSensor(XiaomiBinarySensor):
    """Representation of a XiaomiMotionSensor."""

    def __init__(self, device, hass, xiaomi_hub):
        """Initialize the XiaomiMotionSensor."""
        self._hass = hass
        self._data_key = 'status'
        self._no_motion_since = 0
        self._should_poll = False
        self._device_class = 'motion'
        XiaomiBinarySensor.__init__(self, device, 'Motion Sensor', xiaomi_hub)

    @property
    def should_poll(self):
        """Return True if entity has to be polled for state."""
        return self._should_poll

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        attrs = {ATTR_NO_MOTION_SINCE: self._no_motion_since}
        attrs.update(super().device_state_attributes)
        return attrs

    def parse_data(self, data):
        """Parse data sent by gateway."""
        self._should_poll = False
        if NO_MOTION in data:  # handle push from the hub
            self._no_motion_since = data[NO_MOTION]
            self._state = False
            return True

        value = data.get(self._data_key)
        if value is None:
            return False

        if value == MOTION:
            self._should_poll = True
            if self.entity_id is not None:
                self._hass.bus.fire('motion', {
                    'entity_id': self.entity_id
                })

            self._no_motion_since = 0
            if self._state:
                return False
            self._state = True
            return True
        elif value == NO_MOTION:
            if not self._state:
                return False
            self._state = False
            return True

    def update(self):
        """Update the sensor state."""
        _LOGGER.debug('Updating xiaomi motion sensor by polling')
        self.xiaomi_hub.get_from_hub(self._sid)


class XiaomiDoorSensor(XiaomiBinarySensor):
    """Representation of a XiaomiDoorSensor."""

    def __init__(self, device, xiaomi_hub):
        """Initialize the XiaomiDoorSensor."""
        self._data_key = 'status'
        self._open_since = 0
        self._should_poll = False
        self._device_class = 'opening'
        XiaomiBinarySensor.__init__(self, device, 'Door Window Sensor', xiaomi_hub)

    @property
    def should_poll(self):
        """Return True if entity has to be polled for state."""
        return self._should_poll

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        attrs = {ATTR_OPEN_SINCE: self._open_since}
        attrs.update(super().device_state_attributes)
        return attrs

    def parse_data(self, data):
        """Parse data sent by gateway."""
        self._should_poll = False
        if NO_CLOSE in data:  # handle push from the hub
            self._open_since = data[NO_CLOSE]
            return True

        value = data.get(self._data_key)
        if value is None:
            return False

        if value == 'open':
            self._should_poll = True
            if self._state:
                return False
            self._state = True
            return True
        elif value == 'close':
            self._open_since = 0
            if self._state:
                self._state = False
                return True
            return False

    def update(self):
        """Update the sensor state."""
        _LOGGER.debug('Updating xiaomi door sensor by polling')
        self.xiaomi_hub.get_from_hub(self._sid)


class XiaomiSmokeSensor(XiaomiBinarySensor):
    """Representation of a XiaomiSmokeSensor."""

    def __init__(self, device, xiaomi_hub):
        """Initialize the XiaomiSmokeSensor."""
        self._data_key = 'alarm'
        self._density = 0
        self._device_class = 'smoke'
        XiaomiBinarySensor.__init__(self, device, 'Smoke Sensor', xiaomi_hub)

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        attrs = {ATTR_DENSITY: self._density}
        attrs.update(super().device_state_attributes)
        return attrs

    def parse_data(self, data):
        """Parse data sent by gateway."""
        if DENSITY in data:
            self._density = int(data.get(DENSITY))
        value = data.get(self._data_key)
        if value is None:
            return False

        if value == '1':
            if self._state:
                return False
            self._state = True
            return True
        elif value == '0':
            if self._state:
                self._state = False
                return True
            return False


class XiaomiButton(XiaomiBinarySensor):
    """Representation of a Xiaomi Button."""

    def __init__(self, device, name, data_key, hass, xiaomi_hub):
        """Initialize the XiaomiButton."""
        self._hass = hass
        self._data_key = data_key
        XiaomiBinarySensor.__init__(self, device, name, xiaomi_hub)

    def parse_data(self, data):
        """Parse data sent by gateway."""
        value = data.get(self._data_key)
        if value is None:
            return False

        if value == 'long_click_press':
            self._state = True
            click_type = 'long_click_press'
        elif value == 'long_click_release':
            self._state = False
            click_type = 'hold'
        elif value == 'click':
            click_type = 'single'
        elif value == 'double_click':
            click_type = 'double'
        elif value == 'both_click':
            click_type = 'both'
        else:
            return False

        self._hass.bus.fire('click', {
            'entity_id': self.entity_id,
            'click_type': click_type
        })
        if value in ['long_click_press', 'long_click_release']:
            return True
        return False


class XiaomiCube(XiaomiBinarySensor):
    """Representation of a Xiaomi Cube."""

    STATUS = 'status'
    ROTATE = 'rotate'

    def __init__(self, device, hass, xiaomi_hub):
        """Initialize the XiaomiButton."""
        self._hass = hass
        self._state = False
        XiaomiBinarySensor.__init__(self, device, 'Cube', xiaomi_hub)

    def parse_data(self, data):
        """Parse data sent by gateway."""
        if self.STATUS in data:
            self._hass.bus.fire('cube_action', {
                'entity_id': self.entity_id,
                'action_type': data[self.STATUS]
            })

        if self.ROTATE in data:
            self._hass.bus.fire('cube_action', {
                'entity_id': self.entity_id,
                'action_type': self.ROTATE,
                'action_value': float(data[self.ROTATE].replace(",", "."))
            })
        return False
