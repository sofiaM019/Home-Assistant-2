"""The tests for the Input slider component."""
# pylint: disable=too-many-public-methods,protected-access
import unittest

import voluptuous as vol

from homeassistant.components import input_slider
from tests.common import get_test_home_assistant


class TestInputSlider(unittest.TestCase):
    """Test the input slider component."""

    def setUp(self):  # pylint: disable=invalid-name
        """Setup things to be run when tests are started."""
        self.hass = get_test_home_assistant()

    def tearDown(self):  # pylint: disable=invalid-name
        """Stop everything that was started."""
        self.hass.stop()

    def test_config(self):
        """Test config."""
        with self.assertRaises(vol.Invalid):
            input_slider.PLATFORM_SCHEMA(None)
        with self.assertRaises(vol.Invalid):
            input_slider.PLATFORM_SCHEMA({})
        with self.assertRaises(vol.Invalid):
            input_slider.PLATFORM_SCHEMA({'name with space': None})

        self.assertFalse(input_slider.setup(self.hass, {
            input_slider.DOMAIN: input_slider.PLATFORM_SCHEMA({
                'test_1': {
                    'min': 50,
                    'max': 50,
                },
            })
        }))

    def test_select_value(self):
        """Test select_value method."""
        self.assertTrue(input_slider.setup(self.hass, {
            'input_slider': input_slider.PLATFORM_SCHEMA({
                'test_1': {
                    'initial': 50,
                    'min': 0,
                    'max': 100,
                },
            })
        }))
        entity_id = 'input_slider.test_1'

        state = self.hass.states.get(entity_id)
        self.assertEqual(50, float(state.state))

        input_slider.select_value(self.hass, entity_id, '30.4')
        self.hass.block_till_done()

        state = self.hass.states.get(entity_id)
        self.assertEqual(30.4, float(state.state))

        input_slider.select_value(self.hass, entity_id, '70')
        self.hass.block_till_done()

        state = self.hass.states.get(entity_id)
        self.assertEqual(70, float(state.state))

        input_slider.select_value(self.hass, entity_id, '110')
        self.hass.block_till_done()

        state = self.hass.states.get(entity_id)
        self.assertEqual(70, float(state.state))
