"""The tests for the geojson platform."""
from datetime import timedelta
from unittest.mock import ANY, call, patch

from aio_geojson_generic_client import GenericFeed
from freezegun import freeze_time

from homeassistant.components import geo_json_events, geo_location
from homeassistant.components.geo_json_events.const import (
    ATTR_EXTERNAL_ID,
    DEFAULT_SCAN_INTERVAL,
)
from homeassistant.components.geo_location import ATTR_SOURCE
from homeassistant.const import (
    ATTR_FRIENDLY_NAME,
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
    ATTR_UNIT_OF_MEASUREMENT,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_RADIUS,
    CONF_SCAN_INTERVAL,
    CONF_URL,
    EVENT_HOMEASSISTANT_START,
    LENGTH_KILOMETERS,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component
import homeassistant.util.dt as dt_util

from tests.common import async_fire_time_changed
from tests.components.geo_json_events import _generate_mock_feed_entry
from tests.components.geo_json_events.conftest import URL

CONFIG = {geo_json_events.DOMAIN: {CONF_URL: URL, CONF_RADIUS: 200}}

CONFIG_WITH_CUSTOM_LOCATION = {
    geo_json_events.DOMAIN: {
        CONF_URL: URL,
        CONF_RADIUS: 200,
        CONF_LATITUDE: 15.1,
        CONF_LONGITUDE: 25.2,
    }
}

CONFIG_LEGACY = {
    geo_location.DOMAIN: [
        {
            "platform": "geo_json_events",
            CONF_URL: URL,
            CONF_RADIUS: 190,
            CONF_SCAN_INTERVAL: timedelta(minutes=2),
        }
    ]
}


async def test_setup(hass: HomeAssistant) -> None:
    """Test the general setup of the platform."""
    # Set up some mock feed entries for this test.
    mock_entry_1 = _generate_mock_feed_entry("1234", "Title 1", 15.5, (-31.0, 150.0))
    mock_entry_2 = _generate_mock_feed_entry("2345", "Title 2", 20.5, (-31.1, 150.1))
    mock_entry_3 = _generate_mock_feed_entry("3456", "Title 3", 25.5, (-31.2, 150.2))
    mock_entry_4 = _generate_mock_feed_entry("4567", "Title 4", 12.5, (-31.3, 150.3))

    # Patching 'utcnow' to gain more control over the timed update.
    utcnow = dt_util.utcnow()
    with freeze_time(utcnow), patch(
        "aio_geojson_client.feed.GeoJsonFeed.update"
    ) as mock_feed_update:
        mock_feed_update.return_value = (
            "OK",
            [mock_entry_1, mock_entry_2, mock_entry_3],
        )
        assert await async_setup_component(hass, geo_json_events.DOMAIN, CONFIG)
        await hass.async_block_till_done()
        # Artificially trigger update and collect events.
        hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
        await hass.async_block_till_done()

        # 3 geolocation and 1 sensor entities
        assert len(hass.states.async_entity_ids("geo_location")) == 3
        entity_registry = er.async_get(hass)
        assert len(entity_registry.entities) == 3

        state = hass.states.get("geo_location.title_1")
        assert state is not None
        assert state.name == "Title 1"
        assert state.attributes == {
            ATTR_EXTERNAL_ID: "1234",
            ATTR_LATITUDE: -31.0,
            ATTR_LONGITUDE: 150.0,
            ATTR_FRIENDLY_NAME: "Title 1",
            ATTR_UNIT_OF_MEASUREMENT: LENGTH_KILOMETERS,
            ATTR_SOURCE: "geo_json_events",
        }
        assert round(abs(float(state.state) - 15.5), 7) == 0

        state = hass.states.get("geo_location.title_2")
        assert state is not None
        assert state.name == "Title 2"
        assert state.attributes == {
            ATTR_EXTERNAL_ID: "2345",
            ATTR_LATITUDE: -31.1,
            ATTR_LONGITUDE: 150.1,
            ATTR_FRIENDLY_NAME: "Title 2",
            ATTR_UNIT_OF_MEASUREMENT: LENGTH_KILOMETERS,
            ATTR_SOURCE: "geo_json_events",
        }
        assert round(abs(float(state.state) - 20.5), 7) == 0

        state = hass.states.get("geo_location.title_3")
        assert state is not None
        assert state.name == "Title 3"
        assert state.attributes == {
            ATTR_EXTERNAL_ID: "3456",
            ATTR_LATITUDE: -31.2,
            ATTR_LONGITUDE: 150.2,
            ATTR_FRIENDLY_NAME: "Title 3",
            ATTR_UNIT_OF_MEASUREMENT: LENGTH_KILOMETERS,
            ATTR_SOURCE: "geo_json_events",
        }
        assert round(abs(float(state.state) - 25.5), 7) == 0

        # Simulate an update - two existing, one new entry,
        # one outdated entry
        mock_feed_update.return_value = (
            "OK",
            [mock_entry_1, mock_entry_4, mock_entry_3],
        )
        async_fire_time_changed(hass, utcnow + timedelta(seconds=DEFAULT_SCAN_INTERVAL))
        await hass.async_block_till_done()

        assert len(hass.states.async_entity_ids("geo_location")) == 3

        # Simulate an update - empty data, but successful update,
        # so no changes to entities.
        mock_feed_update.return_value = "OK_NO_DATA", None
        async_fire_time_changed(
            hass, utcnow + 2 * timedelta(seconds=DEFAULT_SCAN_INTERVAL)
        )
        await hass.async_block_till_done()

        assert len(hass.states.async_entity_ids("geo_location")) == 3

        # Simulate an update - empty data, removes all entities
        mock_feed_update.return_value = "ERROR", None
        async_fire_time_changed(
            hass, utcnow + 3 * timedelta(seconds=DEFAULT_SCAN_INTERVAL)
        )
        await hass.async_block_till_done()

        assert len(hass.states.async_entity_ids("geo_location")) == 0


async def test_setup_with_custom_location(hass: HomeAssistant) -> None:
    """Test the setup with a custom location."""
    # Set up some mock feed entries for this test.
    mock_entry_1 = _generate_mock_feed_entry("1234", "Title 1", 2000.5, (-31.1, 150.1))

    with patch(
        "aio_geojson_generic_client.feed_manager.GenericFeed",
        wraps=GenericFeed,
    ) as mock_feed, patch(
        "aio_geojson_client.feed.GeoJsonFeed.update"
    ) as mock_feed_update:
        mock_feed_update.return_value = "OK", [mock_entry_1]

        assert await async_setup_component(
            hass, geo_location.DOMAIN, CONFIG_WITH_CUSTOM_LOCATION
        )
        await hass.async_block_till_done()

        # Artificially trigger update.
        hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
        # Collect events.
        await hass.async_block_till_done()

        all_states = hass.states.async_all()
        assert len(all_states) == 1

        assert mock_feed.call_args == call(
            ANY, (15.1, 25.2), URL, filter_radius=200.0
        )


async def test_setup_as_legacy_platform(hass):
    """Test the setup with YAML legacy configuration."""
    # Set up some mock feed entries for this test.
    mock_entry_1 = _generate_mock_feed_entry("1234", "Title 1", 20.5, (-31.1, 150.1))

    with patch(
        "aio_geojson_generic_client.feed_manager.GenericFeed",
        wraps=GenericFeed,
    ) as mock_feed, patch(
        "aio_geojson_client.feed.GeoJsonFeed.update"
    ) as mock_feed_update:
        mock_feed_update.return_value = "OK", [mock_entry_1]

        assert await async_setup_component(hass, geo_location.DOMAIN, CONFIG_LEGACY)
        await hass.async_block_till_done()

        # Artificially trigger update.
        hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
        await hass.async_block_till_done()

        assert len(hass.states.async_entity_ids("geo_location")) == 1

        assert mock_feed.call_args == call(ANY, ANY, URL, filter_radius=190.0)
