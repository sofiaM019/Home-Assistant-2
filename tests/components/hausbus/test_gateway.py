"""Test the hausbus gateway class."""

from typing import cast
from unittest.mock import Mock, patch

from pyhausbus.ABusFeature import ABusFeature
from pyhausbus.BusDataMessage import BusDataMessage
from pyhausbus.de.hausbus.homeassistant.proxy.Controller import Controller
from pyhausbus.de.hausbus.homeassistant.proxy.controller.data.Configuration import (
    Configuration,
)
from pyhausbus.de.hausbus.homeassistant.proxy.controller.data.ModuleId import ModuleId
from pyhausbus.de.hausbus.homeassistant.proxy.controller.data.RemoteObjects import (
    RemoteObjects,
)
from pyhausbus.de.hausbus.homeassistant.proxy.controller.params.EFirmwareId import (
    EFirmwareId,
)
from pyhausbus.de.hausbus.homeassistant.proxy.Dimmer import Dimmer
from pyhausbus.HomeServer import HomeServer
from pyhausbus.ObjectId import ObjectId

from homeassistant.components.hausbus.device import HausbusDevice
from homeassistant.components.hausbus.gateway import HausbusGateway
from homeassistant.components.hausbus.light import HausbusLight
from homeassistant.components.light import ColorMode
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .helpers import add_channel_from_thread, create_gateway, setup_hausbus_integration


async def test_init(hass: HomeAssistant) -> None:
    """Test initialization of the hausbus gateway."""
    config_entry = await setup_hausbus_integration(hass)

    # Create a mock HomeServer
    mock_home_server = Mock(Spec=HomeServer)

    # Patch the HomeServer constructor to return the mock_home_server
    with patch(
        "homeassistant.components.hausbus.gateway.HomeServer",
        return_value=mock_home_server,
    ):
        # Create a HausbusGateway instance
        gateway = HausbusGateway(hass, config_entry)

    # Assert the initial state of the gateway
    assert gateway.hass == hass
    assert gateway.config_entry == config_entry
    assert not gateway.devices
    assert not gateway.channels
    assert gateway.home_server == mock_home_server
    assert not gateway._new_channel_listeners


async def test_add_device(hass: HomeAssistant) -> None:
    """Test adding a device to the hausbus gateway."""
    gateway = await create_gateway(hass)

    # Add a new device
    device_id = "device_1"
    module = ModuleId("module", 0, 1, 0, EFirmwareId.ESP32)
    gateway.add_device(device_id, module)

    # Assert that the device is added to the gateway's devices
    assert device_id in gateway.devices
    assert device_id in gateway.channels


async def test_get_device(hass: HomeAssistant) -> None:
    """Test getting a device from to the hausbus gateway."""
    gateway = await create_gateway(hass)

    # Add a new device
    device_id = "1"
    module = ModuleId("module", 0, 1, 0, EFirmwareId.ESP32)
    gateway.add_device(device_id, module)

    # Get the device by ObjectId
    object_id = ObjectId(65536)  # = 0x00 01 00 00
    device = gateway.get_device(object_id)

    # Assert that the correct device is retrieved
    assert device.device_id == device_id


async def test_get_channel_list(hass: HomeAssistant) -> None:
    """Test getting a channel list."""
    gateway = await create_gateway(hass)

    # Add a new device
    device_id = "1"
    module = ModuleId("module", 0, 1, 0, EFirmwareId.ESP32)
    gateway.add_device(device_id, module)

    # Get the device by ObjectId
    object_id = ObjectId(65536)  # = 0x00 01 00 00, with device_id = 0x00 01
    channel_list = gateway.get_channel_list(object_id)

    # Assert that the channel list is not None
    assert channel_list is not None


async def test_get_channel_id(hass: HomeAssistant) -> None:
    """Test getting a channel id."""
    gateway = await create_gateway(hass)

    # Get the device by ObjectId
    object_id = ObjectId(
        66051
    )  # = 0x00 01 02 03, with class_id = 0x02 and instance_id = 0x03
    channel_id = gateway.get_channel_id(object_id)

    # Assert that the channel list is not None
    assert channel_id == ("2", "3")


async def test_get_channel(hass: HomeAssistant) -> None:
    """Test adding and getting a Dimmer channel."""
    gateway = await create_gateway(hass)

    # get mock config entry with id "1"
    config_entry = hass.config_entries.async_get_entry("1")

    # setup light domain
    await hass.config_entries.async_forward_entry_setups(config_entry, [Platform.LIGHT])

    # Add a new device to hold the dimmer channel
    device_id = "1"
    module = ModuleId("module", 0, 1, 0, EFirmwareId.ESP32)
    gateway.add_device(device_id, module)

    dimmer = Dimmer.create(1, 1)

    # Add the dimmer channel to the gateways channel list
    with patch(
        "homeassistant.components.hausbus.light.Dimmer.getStatus", return_value=True
    ):
        await add_channel_from_thread(hass, dimmer, gateway)

    # retrieve the dimmer channel by using its objectId
    channel = cast(HausbusLight, gateway.get_channel(ObjectId(dimmer.getObjectId())))

    # Assert that the channel is setup correctly
    assert channel.color_mode == ColorMode.BRIGHTNESS
    assert channel.name == "Dimmer 1"


async def test_create_generic_light_channel(hass: HomeAssistant) -> None:
    """Test creating a light channel that is not supported."""
    gateway = await create_gateway(hass)
    device = HausbusDevice("device_id", "sw_version", "hw_version", EFirmwareId.ESP32)
    sender = 66051  # = 0x00 01 02 03, with class_id = 0x02 and instance_id = 0x03
    instance = ABusFeature(sender)

    light = gateway.create_light_entity(device, instance, sender)
    assert light is None


async def test_get_unknown_channel(hass: HomeAssistant) -> None:
    """Test getting a channel that is not defined."""
    gateway = await create_gateway(hass)

    # Get the device by ObjectId
    object_id = ObjectId(
        66051
    )  # = 0x00 01 02 03, with class_id = 0x02 and instance_id = 0x03
    # retrieve the channel by using its objectId
    channel = gateway.get_channel(object_id)
    assert not channel


async def test_own_bus_data_received(hass: HomeAssistant) -> None:
    """Test handling of own bus data."""
    gateway = await create_gateway(hass)

    mock_controller = Mock(Spec=Controller)

    sender = 0x270E0000  # own object id
    receiver = 0x270E0000  # own object id
    data = {}
    busDataMessage = BusDataMessage(sender, receiver, data)
    with patch(
        "homeassistant.components.hausbus.gateway.Controller",
        return_value=mock_controller,
    ):
        gateway.busDataReceived(busDataMessage)

    # controller should not be called, as own messages are not processed
    assert len(mock_controller.mock_calls) == 0


async def test_module_id_received(hass: HomeAssistant) -> None:
    """Test handling of own bus data."""
    gateway = await create_gateway(hass)

    mock_controller = Mock(Spec=Controller)

    module = ModuleId("module", 0, 1, 0, EFirmwareId.ESP32)

    sender = 66051  # = 0x00 01 02 03, with class_id = 0x02 and instance_id = 0x03
    receiver = 0x270E0000  # own object id
    data = module
    busDataMessage = BusDataMessage(sender, receiver, data)
    with patch(
        "homeassistant.components.hausbus.gateway.Controller",
        return_value=mock_controller,
    ):
        gateway.busDataReceived(busDataMessage)

    # after receiving a module id a device is added
    assert gateway.get_device(ObjectId(sender)) is not None
    # controller should call getConfiguration next
    mock_controller.getConfiguration.assert_called_once()


async def test_configuration_received(hass: HomeAssistant) -> None:
    """Test handling of own bus data."""
    gateway = await create_gateway(hass)

    # Add a new device
    device_id = "1"
    module = ModuleId("module", 0, 1, 0, EFirmwareId.ESP32)
    gateway.add_device(device_id, module)

    mock_controller = Mock(Spec=Controller)

    config = Configuration(
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        0x28,
    )

    sender = 66051  # = 0x00 01 02 03, with class_id = 0x02 and instance_id = 0x03
    receiver = 0x270E0000  # own object id
    data = config
    busDataMessage = BusDataMessage(sender, receiver, data)
    with patch(
        "homeassistant.components.hausbus.gateway.Controller",
        return_value=mock_controller,
    ):
        gateway.busDataReceived(busDataMessage)

    # after receiving a configuration a devices model_id is set
    assert gateway.get_device(ObjectId(sender)).model_id == "8-fach Dimmer"
    # controller should call getRemoteObjects next
    mock_controller.getRemoteObjects.assert_called_once()


async def test_remote_objects_received(hass: HomeAssistant) -> None:
    """Test handling of own bus data."""
    gateway = await create_gateway(hass)
    mock_controller = Mock(Spec=Controller)

    sender = 66051  # = 0x00 01 02 03, with class_id = 0x02 and instance_id = 0x03
    receiver = 0x270E0000  # own object id
    data = RemoteObjects(
        [0x02, 0x03]
    )  # list of class_id and instance_id per channel of the device
    busDataMessage = BusDataMessage(sender, receiver, data)

    feature = ABusFeature(sender)
    attrs = {"getDeviceInstances.return_value": [feature]}
    gateway.home_server.configure_mock(**attrs)

    with patch(
        "homeassistant.components.hausbus.gateway.Controller",
        return_value=mock_controller,
    ):
        gateway.busDataReceived(busDataMessage)

    # controller should not be called
    assert len(mock_controller.mock_calls) == 0
    gateway.home_server.getDeviceInstances.assert_called_with(sender, data)
