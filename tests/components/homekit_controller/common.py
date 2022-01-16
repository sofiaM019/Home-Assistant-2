"""Code to support homekit_controller tests."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import json
import logging
import os
from unittest import mock

from aiohomekit.model import Accessories, Accessory
from aiohomekit.model.characteristics import CharacteristicsTypes
from aiohomekit.model.services import ServicesTypes
from aiohomekit.testing import FakeController

from homeassistant.components import zeroconf
from homeassistant.components.homekit_controller import config_flow
from homeassistant.components.homekit_controller.const import (
    CONTROLLER,
    DOMAIN,
    HOMEKIT_ACCESSORY_DISPATCH,
    IDENTIFIER_ACCESSORY_ID,
    IDENTIFIER_SERIAL_NUMBER,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.setup import async_setup_component
import homeassistant.util.dt as dt_util

from tests.common import MockConfigEntry, async_fire_time_changed, load_fixture

logger = logging.getLogger(__name__)


@dataclass
class EntityTestInfo:
    """Describes how we expected an entity to be created by homekit_controller."""

    entity_id: str
    unique_id: str
    friendly_name: str
    state: str
    supported_features: int = 0


@dataclass
class DeviceTestInfo:
    """Describes how we exepced a device to be created by homekit_controlller."""

    unique_id: str
    name: str
    manufacturer: str
    model: str
    sw_version: str
    hw_version: str
    serial_number: str

    devices: list[DeviceTestInfo]
    entities: list[EntityTestInfo]


class Helper:
    """Helper methods for interacting with HomeKit fakes."""

    def __init__(self, hass, entity_id, pairing, accessory, config_entry):
        """Create a helper for a given accessory/entity."""
        self.hass = hass
        self.entity_id = entity_id
        self.pairing = pairing
        self.accessory = accessory
        self.config_entry = config_entry

        self.characteristics = {}
        for service in self.accessory.services:
            service_name = ServicesTypes.get_short(service.type)
            for char in service.characteristics:
                char_name = CharacteristicsTypes.get_short(char.type)
                self.characteristics[(service_name, char_name)] = char

    async def update_named_service(self, service, characteristics):
        """Update a service."""
        self.pairing.testing.update_named_service(service, characteristics)
        await self.hass.async_block_till_done()

    async def poll_and_get_state(self):
        """Trigger a time based poll and return the current entity state."""
        await time_changed(self.hass, 60)

        state = self.hass.states.get(self.entity_id)
        assert state is not None
        return state


async def time_changed(hass, seconds):
    """Trigger time changed."""
    next_update = dt_util.utcnow() + timedelta(seconds)
    async_fire_time_changed(hass, next_update)
    await hass.async_block_till_done()


async def setup_accessories_from_file(hass, path):
    """Load an collection of accessory defs from JSON data."""
    accessories_fixture = await hass.async_add_executor_job(
        load_fixture, os.path.join("homekit_controller", path)
    )
    accessories_json = json.loads(accessories_fixture)
    accessories = Accessories.from_list(accessories_json)
    return accessories


async def setup_platform(hass):
    """Load the platform but with a fake Controller API."""
    config = {"discovery": {}}

    with mock.patch("aiohomekit.Controller") as controller:
        fake_controller = controller.return_value = FakeController()
        await async_setup_component(hass, DOMAIN, config)

    return fake_controller


async def setup_test_accessories(hass, accessories):
    """Load a fake homekit device based on captured JSON profile."""
    fake_controller = await setup_platform(hass)

    pairing_id = "00:00:00:00:00:00"

    accessories_obj = Accessories()
    for accessory in accessories:
        accessories_obj.add_accessory(accessory)
    pairing = await fake_controller.add_paired_device(accessories_obj, pairing_id)

    config_entry = MockConfigEntry(
        version=1,
        domain="homekit_controller",
        entry_id="TestData",
        data={"AccessoryPairingID": pairing_id},
        title="test",
    )
    config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    return config_entry, pairing


async def device_config_changed(hass, accessories):
    """Discover new devices added to Home Assistant at runtime."""
    # Update the accessories our FakePairing knows about
    controller = hass.data[CONTROLLER]
    pairing = controller.pairings["00:00:00:00:00:00"]

    accessories_obj = Accessories()
    for accessory in accessories:
        accessories_obj.add_accessory(accessory)
    pairing.accessories = accessories_obj

    discovery_info = zeroconf.ZeroconfServiceInfo(
        host="127.0.0.1",
        hostname="mock_hostname",
        name="TestDevice",
        port=8080,
        properties={
            "md": "TestDevice",
            "id": "00:00:00:00:00:00",
            "c#": "2",
            "sf": "0",
        },
        type="mock_type",
    )

    # Config Flow will abort and notify us if the discovery event is of
    # interest - in this case c# has incremented
    flow = config_flow.HomekitControllerFlowHandler()
    flow.hass = hass
    flow.context = {}
    result = await flow.async_step_zeroconf(discovery_info)
    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"

    # Wait for services to reconfigure
    await hass.async_block_till_done()
    await hass.async_block_till_done()


async def setup_test_component(hass, setup_accessory, capitalize=False, suffix=None):
    """Load a fake homekit accessory based on a homekit accessory model.

    If capitalize is True, property names will be in upper case.

    If suffix is set, entityId will include the suffix
    """
    accessory = Accessory.create_with_info(
        "TestDevice", "example.com", "Test", "0001", "0.1"
    )
    setup_accessory(accessory)

    domain = None
    for service in accessory.services:
        service_name = ServicesTypes.get_short(service.type)
        if service_name in HOMEKIT_ACCESSORY_DISPATCH:
            domain = HOMEKIT_ACCESSORY_DISPATCH[service_name]
            break

    assert domain, "Cannot map test homekit services to Home Assistant domain"

    config_entry, pairing = await setup_test_accessories(hass, [accessory])
    entity = "testdevice" if suffix is None else f"testdevice_{suffix}"
    return Helper(hass, ".".join((domain, entity)), pairing, accessory, config_entry)


def assert_devices_and_entities_created(hass: HomeAssistant, expected: DeviceTestInfo):
    """Check that all expected devices and entities are loaded and enumerated as expected."""
    entity_registry = er.async_get(hass)
    device_registry = dr.async_get(hass)

    def _do_assertions(expected: DeviceTestInfo) -> dr.DeviceEntry:
        # Note: homekit_controller currently uses a 3-tuple for device identifiers
        # The current standard is a 2-tuple (hkc was not migrated when this change was brought in)

        # There are currently really 3 cases here:
        # - We can match exactly one device by serial number. This wont work for devices like the Ryse.
        #   These have nlank or broken serial numbers.
        # - The device unique id is "00:00:00:00:00:00" - this is the pairing id. This is only set for
        #   the root (bridge) device.
        # - The device unique id is "00:00:00:00:00:00-X", where X is a HAP aid. This is only set when
        #   we have detected broken serial numbers (and serial number is not used as an identifier).

        device = device_registry.async_get_device(
            {
                (DOMAIN, IDENTIFIER_SERIAL_NUMBER, expected.serial_number),
                (DOMAIN, IDENTIFIER_ACCESSORY_ID, expected.unique_id),
            }
        )

        logger.debug("Comparing device %r to %r", device, expected)

        assert device
        assert device.name == expected.name
        assert device.model == expected.model
        assert device.manufacturer == expected.manufacturer
        assert device.hw_version == expected.hw_version
        assert device.sw_version == expected.sw_version

        # We might have matched the device by one identifier only
        # Lets check that the other one is correct. Otherwise the test might silently be wrong.
        for _, key, value in device.identifiers:
            if key == IDENTIFIER_SERIAL_NUMBER:
                assert value == expected.serial_number
            elif key == IDENTIFIER_ACCESSORY_ID:
                assert value == expected.unique_id

        for entity_info in expected.entities:
            entity = entity_registry.async_get(entity_info.entity_id)
            logger.debug("Comparing entity %r to %r", entity, entity_info)

            assert entity
            assert entity.device_id == device.id
            assert entity.unique_id == entity_info.unique_id
            assert entity.supported_features == entity_info.supported_features

            state = hass.states.get(entity_info.entity_id)
            logger.debug("Comparing state %r to %r", state, entity_info)

            assert state is not None
            assert state.state == entity_info.state
            assert state.attributes["friendly_name"] == entity_info.friendly_name

        for child in expected.devices:
            child_device = _do_assertions(child)
            assert child_device.via_device_id == device.id
            assert child_device.id != device.id

        return device

    root_device = _do_assertions(expected)

    # Root device must not have a via, otherwise its not the device
    assert root_device.via_device_id is None
