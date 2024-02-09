"""Test ZHA device discovery."""
from collections.abc import Callable
import re
from typing import Any
from unittest import mock
from unittest.mock import AsyncMock, Mock, patch

import pytest
from zhaquirks.ikea import PowerConfig1CRCluster, ScenesCluster
from zigpy.const import SIG_ENDPOINTS, SIG_MANUFACTURER, SIG_MODEL, SIG_NODE_DESC
import zigpy.profiles.zha
import zigpy.quirks
from zigpy.quirks.v2 import add_to_registry_v2
import zigpy.types
from zigpy.zcl import ClusterType
import zigpy.zcl.clusters.closures
import zigpy.zcl.clusters.general
import zigpy.zcl.clusters.security
import zigpy.zcl.foundation as zcl_f

import homeassistant.components.zha.core.cluster_handlers as cluster_handlers
import homeassistant.components.zha.core.const as zha_const
from homeassistant.components.zha.core.device import ZHADevice
import homeassistant.components.zha.core.discovery as disc
from homeassistant.components.zha.core.endpoint import Endpoint
from homeassistant.components.zha.core.helpers import get_zha_gateway
import homeassistant.components.zha.core.registries as zha_regs
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import EntityPlatform

from .conftest import SIG_EP_INPUT, SIG_EP_OUTPUT, SIG_EP_PROFILE, SIG_EP_TYPE
from .zha_devices_list import (
    DEV_SIG_ATTRIBUTES,
    DEV_SIG_CLUSTER_HANDLERS,
    DEV_SIG_ENT_MAP,
    DEV_SIG_ENT_MAP_CLASS,
    DEV_SIG_ENT_MAP_ID,
    DEV_SIG_EVT_CLUSTER_HANDLERS,
    DEVICES,
)

from tests.components.zha.common import find_entity_id, update_attribute_cache

NO_TAIL_ID = re.compile("_\\d$")
UNIQUE_ID_HD = re.compile(r"^(([\da-fA-F]{2}:){7}[\da-fA-F]{2}-\d{1,3})", re.X)

IGNORE_SUFFIXES = [
    zigpy.zcl.clusters.general.OnOff.StartUpOnOff.__name__,
    "on_off_transition_time",
    "on_level",
    "on_transition_time",
    "off_transition_time",
    "default_move_rate",
    "start_up_current_level",
    "counter",
]


def contains_ignored_suffix(unique_id: str) -> bool:
    """Return true if the unique_id ends with an ignored suffix."""
    for suffix in IGNORE_SUFFIXES:
        if suffix.lower() in unique_id.lower():
            return True
    return False


@patch(
    "zigpy.zcl.clusters.general.Identify.request",
    new=AsyncMock(return_value=[mock.sentinel.data, zcl_f.Status.SUCCESS]),
)
# We do this here because we are testing ZHA discovery logic. Point being we want to ensure that
# all discovered entities are dispatched for creation. In order to test this we need the entities
# added to HA. So we ensure that they are all enabled even though they won't necessarily be in reality
# at runtime
@patch(
    "homeassistant.components.zha.entity.ZhaEntity.entity_registry_enabled_default",
    new=Mock(return_value=True),
)
@pytest.mark.parametrize("device", DEVICES)
async def test_devices(
    device,
    hass_disable_services,
    zigpy_device_mock,
    zha_device_joined_restored,
) -> None:
    """Test device discovery."""
    zigpy_device = zigpy_device_mock(
        endpoints=device[SIG_ENDPOINTS],
        ieee="00:11:22:33:44:55:66:77",
        manufacturer=device[SIG_MANUFACTURER],
        model=device[SIG_MODEL],
        node_descriptor=device[SIG_NODE_DESC],
        attributes=device.get(DEV_SIG_ATTRIBUTES),
        patch_cluster=False,
    )

    cluster_identify = _get_first_identify_cluster(zigpy_device)
    if cluster_identify:
        cluster_identify.request.reset_mock()

    with patch(
        "homeassistant.helpers.entity_platform.EntityPlatform._async_schedule_add_entities_for_entry",
        side_effect=EntityPlatform._async_schedule_add_entities_for_entry,
        autospec=True,
    ) as mock_add_entities:
        zha_dev = await zha_device_joined_restored(zigpy_device)
        await hass_disable_services.async_block_till_done()

    if cluster_identify:
        # We only identify on join
        should_identify = (
            zha_device_joined_restored.name == "zha_device_joined"
            and not zigpy_device.skip_configuration
        )

        if should_identify:
            assert cluster_identify.request.mock_calls == [
                mock.call(
                    False,
                    cluster_identify.commands_by_name["trigger_effect"].id,
                    cluster_identify.commands_by_name["trigger_effect"].schema,
                    effect_id=zigpy.zcl.clusters.general.Identify.EffectIdentifier.Okay,
                    effect_variant=(
                        zigpy.zcl.clusters.general.Identify.EffectVariant.Default
                    ),
                    expect_reply=True,
                    manufacturer=None,
                    tsn=None,
                )
            ]
        else:
            assert cluster_identify.request.mock_calls == []

    event_cluster_handlers = {
        ch.id
        for endpoint in zha_dev._endpoints.values()
        for ch in endpoint.client_cluster_handlers.values()
    }
    assert event_cluster_handlers == set(device[DEV_SIG_EVT_CLUSTER_HANDLERS])

    # Keep track of unhandled entities: they should always be ones we explicitly ignore
    created_entities = {
        entity.entity_id: entity
        for mock_call in mock_add_entities.mock_calls
        for entity in mock_call.args[1]
    }
    unhandled_entities = set(created_entities.keys())
    entity_registry = er.async_get(hass_disable_services)

    for (platform, unique_id), ent_info in device[DEV_SIG_ENT_MAP].items():
        no_tail_id = NO_TAIL_ID.sub("", ent_info[DEV_SIG_ENT_MAP_ID])
        ha_entity_id = entity_registry.async_get_entity_id(platform, "zha", unique_id)
        assert (
            ha_entity_id is not None
        ), f"No entity found for platform[{platform}] unique_id[{unique_id}] no_tail_id[{no_tail_id}] with entity_id[{ha_entity_id}]"
        assert ha_entity_id.startswith(no_tail_id)

        entity = created_entities[ha_entity_id]
        unhandled_entities.remove(ha_entity_id)

        assert entity.platform.domain == platform
        assert type(entity).__name__ == ent_info[DEV_SIG_ENT_MAP_CLASS]
        # unique_id used for discover is the same for "multi entities"
        assert unique_id == entity.unique_id
        assert {ch.name for ch in entity.cluster_handlers.values()} == set(
            ent_info[DEV_SIG_CLUSTER_HANDLERS]
        )

    # All unhandled entities should be ones we explicitly ignore
    for entity_id in unhandled_entities:
        domain = entity_id.split(".")[0]
        assert domain in zha_const.PLATFORMS
        assert contains_ignored_suffix(entity_id)


def _get_first_identify_cluster(zigpy_device):
    for endpoint in list(zigpy_device.endpoints.values())[1:]:
        if hasattr(endpoint, "identify"):
            return endpoint.identify


@mock.patch(
    "homeassistant.components.zha.core.discovery.ProbeEndpoint.discover_by_device_type"
)
@mock.patch(
    "homeassistant.components.zha.core.discovery.ProbeEndpoint.discover_by_cluster_id"
)
def test_discover_entities(m1, m2) -> None:
    """Test discover endpoint class method."""
    endpoint = mock.MagicMock()
    disc.PROBE.discover_entities(endpoint)
    assert m1.call_count == 1
    assert m1.call_args[0][0] is endpoint
    assert m2.call_count == 1
    assert m2.call_args[0][0] is endpoint


@pytest.mark.parametrize(
    ("device_type", "platform", "hit"),
    [
        (zigpy.profiles.zha.DeviceType.ON_OFF_LIGHT, Platform.LIGHT, True),
        (zigpy.profiles.zha.DeviceType.ON_OFF_BALLAST, Platform.SWITCH, True),
        (zigpy.profiles.zha.DeviceType.SMART_PLUG, Platform.SWITCH, True),
        (0xFFFF, None, False),
    ],
)
def test_discover_by_device_type(device_type, platform, hit) -> None:
    """Test entity discovery by device type."""

    endpoint = mock.MagicMock(spec_set=Endpoint)
    ep_mock = mock.PropertyMock()
    ep_mock.return_value.profile_id = 0x0104
    ep_mock.return_value.device_type = device_type
    type(endpoint).zigpy_endpoint = ep_mock

    get_entity_mock = mock.MagicMock(
        return_value=(mock.sentinel.entity_cls, mock.sentinel.claimed)
    )
    with mock.patch(
        "homeassistant.components.zha.core.registries.ZHA_ENTITIES.get_entity",
        get_entity_mock,
    ):
        disc.PROBE.discover_by_device_type(endpoint)
    if hit:
        assert get_entity_mock.call_count == 1
        assert endpoint.claim_cluster_handlers.call_count == 1
        assert endpoint.claim_cluster_handlers.call_args[0][0] is mock.sentinel.claimed
        assert endpoint.async_new_entity.call_count == 1
        assert endpoint.async_new_entity.call_args[0][0] == platform
        assert endpoint.async_new_entity.call_args[0][1] == mock.sentinel.entity_cls


def test_discover_by_device_type_override() -> None:
    """Test entity discovery by device type overriding."""

    endpoint = mock.MagicMock(spec_set=Endpoint)
    ep_mock = mock.PropertyMock()
    ep_mock.return_value.profile_id = 0x0104
    ep_mock.return_value.device_type = 0x0100
    type(endpoint).zigpy_endpoint = ep_mock

    overrides = {endpoint.unique_id: {"type": Platform.SWITCH}}
    get_entity_mock = mock.MagicMock(
        return_value=(mock.sentinel.entity_cls, mock.sentinel.claimed)
    )
    with mock.patch(
        "homeassistant.components.zha.core.registries.ZHA_ENTITIES.get_entity",
        get_entity_mock,
    ), mock.patch.dict(disc.PROBE._device_configs, overrides, clear=True):
        disc.PROBE.discover_by_device_type(endpoint)
        assert get_entity_mock.call_count == 1
        assert endpoint.claim_cluster_handlers.call_count == 1
        assert endpoint.claim_cluster_handlers.call_args[0][0] is mock.sentinel.claimed
        assert endpoint.async_new_entity.call_count == 1
        assert endpoint.async_new_entity.call_args[0][0] == Platform.SWITCH
        assert endpoint.async_new_entity.call_args[0][1] == mock.sentinel.entity_cls


def test_discover_probe_single_cluster() -> None:
    """Test entity discovery by single cluster."""

    endpoint = mock.MagicMock(spec_set=Endpoint)
    ep_mock = mock.PropertyMock()
    ep_mock.return_value.profile_id = 0x0104
    ep_mock.return_value.device_type = 0x0100
    type(endpoint).zigpy_endpoint = ep_mock

    get_entity_mock = mock.MagicMock(
        return_value=(mock.sentinel.entity_cls, mock.sentinel.claimed)
    )
    cluster_handler_mock = mock.MagicMock(spec_set=cluster_handlers.ClusterHandler)
    with mock.patch(
        "homeassistant.components.zha.core.registries.ZHA_ENTITIES.get_entity",
        get_entity_mock,
    ):
        disc.PROBE.probe_single_cluster(Platform.SWITCH, cluster_handler_mock, endpoint)

    assert get_entity_mock.call_count == 1
    assert endpoint.claim_cluster_handlers.call_count == 1
    assert endpoint.claim_cluster_handlers.call_args[0][0] is mock.sentinel.claimed
    assert endpoint.async_new_entity.call_count == 1
    assert endpoint.async_new_entity.call_args[0][0] == Platform.SWITCH
    assert endpoint.async_new_entity.call_args[0][1] == mock.sentinel.entity_cls
    assert endpoint.async_new_entity.call_args[0][3] == mock.sentinel.claimed


@pytest.mark.parametrize("device_info", DEVICES)
async def test_discover_endpoint(
    device_info: dict[str, Any],
    zha_device_mock: Callable[..., ZHADevice],
    hass: HomeAssistant,
) -> None:
    """Test device discovery."""

    with mock.patch(
        "homeassistant.components.zha.core.endpoint.Endpoint.async_new_entity"
    ) as new_ent:
        device = zha_device_mock(
            device_info[SIG_ENDPOINTS],
            manufacturer=device_info[SIG_MANUFACTURER],
            model=device_info[SIG_MODEL],
            node_desc=device_info[SIG_NODE_DESC],
            patch_cluster=True,
        )

    assert device_info[DEV_SIG_EVT_CLUSTER_HANDLERS] == sorted(
        ch.id
        for endpoint in device._endpoints.values()
        for ch in endpoint.client_cluster_handlers.values()
    )

    # build a dict of entity_class -> (platform, unique_id, cluster_handlers) tuple
    ha_ent_info = {}
    for call in new_ent.call_args_list:
        platform, entity_cls, unique_id, cluster_handlers = call[0]
        if not contains_ignored_suffix(unique_id):
            unique_id_head = UNIQUE_ID_HD.match(unique_id).group(
                0
            )  # ieee + endpoint_id
            ha_ent_info[(unique_id_head, entity_cls.__name__)] = (
                platform,
                unique_id,
                cluster_handlers,
            )

    for platform_id, ent_info in device_info[DEV_SIG_ENT_MAP].items():
        platform, unique_id = platform_id

        test_ent_class = ent_info[DEV_SIG_ENT_MAP_CLASS]
        test_unique_id_head = UNIQUE_ID_HD.match(unique_id).group(0)
        assert (test_unique_id_head, test_ent_class) in ha_ent_info

        entity_platform, entity_unique_id, entity_cluster_handlers = ha_ent_info[
            (test_unique_id_head, test_ent_class)
        ]
        assert platform is entity_platform.value
        # unique_id used for discover is the same for "multi entities"
        assert unique_id.startswith(entity_unique_id)
        assert {ch.name for ch in entity_cluster_handlers} == set(
            ent_info[DEV_SIG_CLUSTER_HANDLERS]
        )

    device.async_cleanup_handles()


def _ch_mock(cluster):
    """Return mock of a cluster_handler with a cluster."""
    cluster_handler = mock.MagicMock()
    type(cluster_handler).cluster = mock.PropertyMock(
        return_value=cluster(mock.MagicMock())
    )
    return cluster_handler


@mock.patch(
    (
        "homeassistant.components.zha.core.discovery.ProbeEndpoint"
        ".handle_on_off_output_cluster_exception"
    ),
    new=mock.MagicMock(),
)
@mock.patch(
    "homeassistant.components.zha.core.discovery.ProbeEndpoint.probe_single_cluster"
)
def _test_single_input_cluster_device_class(probe_mock):
    """Test SINGLE_INPUT_CLUSTER_DEVICE_CLASS matching by cluster id or class."""

    door_ch = _ch_mock(zigpy.zcl.clusters.closures.DoorLock)
    cover_ch = _ch_mock(zigpy.zcl.clusters.closures.WindowCovering)
    multistate_ch = _ch_mock(zigpy.zcl.clusters.general.MultistateInput)

    class QuirkedIAS(zigpy.quirks.CustomCluster, zigpy.zcl.clusters.security.IasZone):
        pass

    ias_ch = _ch_mock(QuirkedIAS)

    class _Analog(zigpy.quirks.CustomCluster, zigpy.zcl.clusters.general.AnalogInput):
        pass

    analog_ch = _ch_mock(_Analog)

    endpoint = mock.MagicMock(spec_set=Endpoint)
    endpoint.unclaimed_cluster_handlers.return_value = [
        door_ch,
        cover_ch,
        multistate_ch,
        ias_ch,
    ]

    disc.ProbeEndpoint().discover_by_cluster_id(endpoint)
    assert probe_mock.call_count == len(endpoint.unclaimed_cluster_handlers())
    probes = (
        (Platform.LOCK, door_ch),
        (Platform.COVER, cover_ch),
        (Platform.SENSOR, multistate_ch),
        (Platform.BINARY_SENSOR, ias_ch),
        (Platform.SENSOR, analog_ch),
    )
    for call, details in zip(probe_mock.call_args_list, probes):
        platform, ch = details
        assert call[0][0] == platform
        assert call[0][1] == ch


def test_single_input_cluster_device_class_by_cluster_class() -> None:
    """Test SINGLE_INPUT_CLUSTER_DEVICE_CLASS matching by cluster id or class."""
    mock_reg = {
        zigpy.zcl.clusters.closures.DoorLock.cluster_id: Platform.LOCK,
        zigpy.zcl.clusters.closures.WindowCovering.cluster_id: Platform.COVER,
        zigpy.zcl.clusters.general.AnalogInput: Platform.SENSOR,
        zigpy.zcl.clusters.general.MultistateInput: Platform.SENSOR,
        zigpy.zcl.clusters.security.IasZone: Platform.BINARY_SENSOR,
    }

    with mock.patch.dict(
        zha_regs.SINGLE_INPUT_CLUSTER_DEVICE_CLASS, mock_reg, clear=True
    ):
        _test_single_input_cluster_device_class()


@pytest.mark.parametrize(
    ("override", "entity_id"),
    [
        (None, "light.manufacturer_model_light"),
        ("switch", "switch.manufacturer_model_switch"),
    ],
)
async def test_device_override(
    hass_disable_services, zigpy_device_mock, setup_zha, override, entity_id
) -> None:
    """Test device discovery override."""

    zigpy_device = zigpy_device_mock(
        {
            1: {
                SIG_EP_TYPE: zigpy.profiles.zha.DeviceType.COLOR_DIMMABLE_LIGHT,
                "endpoint_id": 1,
                SIG_EP_INPUT: [0, 3, 4, 5, 6, 8, 768, 2821, 64513],
                SIG_EP_OUTPUT: [25],
                SIG_EP_PROFILE: 260,
            }
        },
        "00:11:22:33:44:55:66:77",
        "manufacturer",
        "model",
        patch_cluster=False,
    )

    if override is not None:
        override = {"device_config": {"00:11:22:33:44:55:66:77-1": {"type": override}}}

    await setup_zha(override)
    assert hass_disable_services.states.get(entity_id) is None
    zha_gateway = get_zha_gateway(hass_disable_services)
    await zha_gateway.async_device_initialized(zigpy_device)
    await hass_disable_services.async_block_till_done()
    assert hass_disable_services.states.get(entity_id) is not None


async def test_group_probe_cleanup_called(
    hass_disable_services, setup_zha, config_entry
) -> None:
    """Test cleanup happens when ZHA is unloaded."""
    await setup_zha()
    disc.GROUP_PROBE.cleanup = mock.Mock(wraps=disc.GROUP_PROBE.cleanup)
    await config_entry.async_unload(hass_disable_services)
    await hass_disable_services.async_block_till_done()
    disc.GROUP_PROBE.cleanup.assert_called()


async def test_quirks_v2_entity_discovery(
    hass,
    zigpy_device_mock,
    zha_device_joined,
) -> None:
    """Test quirks v2 discovery."""

    zigpy_device = zigpy_device_mock(
        {
            1: {
                SIG_EP_INPUT: [
                    zigpy.zcl.clusters.general.PowerConfiguration.cluster_id,
                    zigpy.zcl.clusters.general.Groups.cluster_id,
                    zigpy.zcl.clusters.general.OnOff.cluster_id,
                ],
                SIG_EP_OUTPUT: [
                    zigpy.zcl.clusters.general.Scenes.cluster_id,
                ],
                SIG_EP_TYPE: zigpy.profiles.zha.DeviceType.NON_COLOR_CONTROLLER,
            }
        },
        ieee="01:2d:6f:00:0a:90:69:e8",
        manufacturer="Ikea of Sweden",
        model="TRADFRI remote control",
    )

    add_to_registry_v2(
        "Ikea of Sweden", "TRADFRI remote control", zigpy.quirks._DEVICE_REGISTRY
    ).replaces(PowerConfig1CRCluster).replaces(
        ScenesCluster, cluster_type=ClusterType.Client
    ).number(
        zigpy.zcl.clusters.general.OnOff.AttributeDefs.off_wait_time.name,
        zigpy.zcl.clusters.general.OnOff.cluster_id,
    )

    zigpy_device = zigpy.quirks._DEVICE_REGISTRY.get_device(zigpy_device)
    zigpy_device.endpoints[1].power.PLUGGED_ATTR_READS = {
        "battery_voltage": 3,
        "battery_percentage_remaining": 100,
    }
    update_attribute_cache(zigpy_device.endpoints[1].power)
    zigpy_device.endpoints[1].on_off.PLUGGED_ATTR_READS = {
        zigpy.zcl.clusters.general.OnOff.AttributeDefs.off_wait_time.name: 3,
    }
    update_attribute_cache(zigpy_device.endpoints[1].on_off)

    zha_device = await zha_device_joined(zigpy_device)
    zha_device.available = True
    await hass.async_block_till_done()

    entity_id = find_entity_id(
        Platform.NUMBER,
        zha_device,
        hass,
    )
    assert entity_id is not None

    state = hass.states.get(entity_id)
    assert state is not None
