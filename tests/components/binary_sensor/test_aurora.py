"""The tests for the Aurora sensor platform."""
import re
import unittest

import requests_mock

from homeassistant.components.binary_sensor import aurora
from tests.common import load_fixture, get_test_home_assistant


class TestAuroraSensorSetUp(unittest.TestCase):
    """Test the aurora platform."""

    def setUp(self):
        """Initialize values for this testcase class."""
        self.hass = get_test_home_assistant()
        self.lat = 37.8267
        self.lon = -122.423
        self.hass.config.latitude = self.lat
        self.hass.config.longitude = self.lon
        self.entities = []

    def tearDown(self):  # pylint: disable=invalid-name
        """Stop everything that was started."""
        self.hass.stop()

    @requests_mock.Mocker()
    def test_setup_and_initial_state(self, mock_req):
        """Test that the component is created and initialized as expected."""
        uri = re.compile(
            "http://services\.swpc\.noaa\.gov/text/aurora-nowcast-map\.txt"
        )
        mock_req.get(uri, text=load_fixture('aurora.txt'))

        entities = []

        def mock_add_entities(new_entities, update_before_add=False):
            """Mock add entities."""
            if update_before_add:
                for entity in new_entities:
                    entity.update()

            for entity in new_entities:
                entities.append(entity)

        aurora.setup_platform(self.hass, {"name": "Test"}, mock_add_entities)

        aurora_component = entities[0]
        self.assertEqual(len(entities), 1)
        self.assertEqual(aurora_component.name, "Test")
        self.assertEqual(
            aurora_component.device_state_attributes["visibility_level"],
            '0'
        )
        self.assertEqual(
            aurora_component.device_state_attributes["message"],
            "nothing's out"
        )
        self.assertFalse(aurora_component.is_on)


class TestAuroraGateway(unittest.TestCase):
    """Test for the aurora tracker's API gateway."""

    def setUp(self):
        """Initialize values for this testcase class."""
        self.lat = 5
        self.lon = 5

    @requests_mock.Mocker()
    def test_correctly_parses_expected_input(self, mock_req):
        """Test that the gateway correctly parses the expected response."""
        uri = re.compile(
            "http://services\.swpc\.noaa\.gov/text/aurora-nowcast-map\.txt"
        )
        mock_req.get(uri, text=load_fixture('aurora.txt'))

        gateway = aurora.AuroraAPIGateway(self.lat, self.lon)

        forecast = gateway.get_aurora_forecast()

        self.assertEquals(forecast, "5")
