"""The tests for the Google Actions component."""
# pylint: disable=protected-access
import asyncio

from homeassistant import const
from homeassistant.components import google_assistant as ga

DETERMINE_SERVICE_TESTS = [{  # Test light brightness
    'entity_id': 'light.test',
    'command': ga.const.COMMAND_BRIGHTNESS,
    'params': {
        'brightness': 95
    },
    'expected': (
        const.SERVICE_TURN_ON,
        {'entity_id': 'light.test', 'brightness': 242}
    )
}, {  # Test light color temperature
    'entity_id': 'light.test',
    'command': ga.const.COMMAND_COLOR,
    'params': {
        'color': {
            'temperature': 2300,
            'name': 'warm white'
        }
    },
    'expected': (
        const.SERVICE_TURN_ON,
        {'entity_id': 'light.test', 'kelvin': 2300}
    )
}, {  # Test light color blue
    'entity_id': 'light.test',
    'command': ga.const.COMMAND_COLOR,
    'params': {
        'color': {
            'spectrumRGB': 255,
            'name': 'blue'
        }
    },
    'expected': (
        const.SERVICE_TURN_ON,
        {'entity_id': 'light.test', 'rgb_color': [0, 0, 255]}
    )
}, {  # Test light color yellow
    'entity_id': 'light.test',
    'command': ga.const.COMMAND_COLOR,
    'params': {
        'color': {
            'spectrumRGB': 16776960,
            'name': 'yellow'
        }
    },
    'expected': (
        const.SERVICE_TURN_ON,
        {'entity_id': 'light.test', 'rgb_color': [255, 255, 0]}
    )
}, {  # Test unhandled action/service
    'entity_id': 'light.test',
    'command': ga.const.COMMAND_COLOR,
    'params': {
        'color': {
            'unhandled': 2300
        }
    },
    'expected': (
        None,
        {'entity_id': 'light.test'}
    )
}, {  # Test switch to light custom type
    'entity_id': 'switch.decorative_lights',
    'command': ga.const.COMMAND_ONOFF,
    'params': {
        'on': True
    },
    'expected': (
        const.SERVICE_TURN_ON,
        {'entity_id': 'switch.decorative_lights'}
    )
}, {  # Test light on / off
    'entity_id': 'light.test',
    'command': ga.const.COMMAND_ONOFF,
    'params': {
        'on': False
    },
    'expected': (const.SERVICE_TURN_OFF, {'entity_id': 'light.test'})
}, {
    'entity_id': 'light.test',
    'command': ga.const.COMMAND_ONOFF,
    'params': {
        'on': True
    },
    'expected': (const.SERVICE_TURN_ON, {'entity_id': 'light.test'})
}, {  # Test Cover open close
    'entity_id': 'cover.bedroom',
    'command': ga.const.COMMAND_ONOFF,
    'params': {
        'on': True
    },
    'expected': (const.SERVICE_OPEN_COVER, {'entity_id': 'cover.bedroom'}),
}, {
    'entity_id': 'cover.bedroom',
    'command': ga.const.COMMAND_ONOFF,
    'params': {
        'on': False
    },
    'expected': (const.SERVICE_CLOSE_COVER, {'entity_id': 'cover.bedroom'}),
}, {  # Test cover position
    'entity_id': 'cover.bedroom',
    'command': ga.const.COMMAND_BRIGHTNESS,
    'params': {
        'brightness': 50
    },
    'expected': (
        const.SERVICE_SET_COVER_POSITION,
        {'entity_id': 'cover.bedroom', 'position': 50}
    ),
}, {  # Test media_player volume
    'entity_id': 'media_player.living_room',
    'command': ga.const.COMMAND_BRIGHTNESS,
    'params': {
        'brightness': 30
    },
    'expected': (
        const.SERVICE_VOLUME_SET,
        {'entity_id': 'media_player.living_room', 'volume_level': 0.3}
    ),
}]


@asyncio.coroutine
def test_make_actions_response():
    """Test make response helper."""
    reqid = 1234
    payload = 'hello'
    result = ga.smart_home.make_actions_response(reqid, payload)
    assert result['requestId'] == reqid
    assert result['payload'] == payload


@asyncio.coroutine
def test_determine_service():
    """Test all branches of determine service."""
    for test in DETERMINE_SERVICE_TESTS:
        result = ga.smart_home.determine_service(
            test['entity_id'],
            test['command'],
            test['params'])
        assert result == test['expected']
