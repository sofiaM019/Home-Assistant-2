"""Test OpenZWave Websocket API."""
from openzwavemqtt.const import ValueType

from homeassistant.components.ozw.const import (
    ATTR_CONFIG_PARAMETER,
    ATTR_OPTIONS,
    ATTR_VALUE,
)
from homeassistant.components.ozw.websocket_api import (
    ATTR_IS_AWAKE,
    ATTR_IS_BEAMING,
    ATTR_IS_FAILED,
    ATTR_IS_FLIRS,
    ATTR_IS_ROUTING,
    ATTR_IS_SECURITYV1,
    ATTR_IS_ZWAVE_PLUS,
    ATTR_NEIGHBORS,
    ATTR_NODE_BASIC_STRING,
    ATTR_NODE_BAUD_RATE,
    ATTR_NODE_GENERIC_STRING,
    ATTR_NODE_QUERY_STAGE,
    ATTR_NODE_SPECIFIC_STRING,
    ID,
    NODE_ID,
    OZW_INSTANCE,
    PARAMETER,
    TYPE,
    VALUE,
)
from homeassistant.components.websocket_api.const import ERR_NOT_FOUND

from .common import MQTTMessage, setup_ozw

from tests.async_mock import patch


async def test_websocket_api(hass, generic_data, hass_ws_client):
    """Test the ozw websocket api."""
    await setup_ozw(hass, fixture=generic_data)
    client = await hass_ws_client(hass)

    # Test instance list
    await client.send_json({ID: 4, TYPE: "ozw/get_instances"})
    msg = await client.receive_json()
    assert len(msg["result"]) == 1
    result = msg["result"][0]
    assert result[OZW_INSTANCE] == 1
    assert result["Status"] == "driverAllNodesQueried"
    assert result["OpenZWave_Version"] == "1.6.1008"

    # Test network status
    await client.send_json({ID: 5, TYPE: "ozw/network_status"})
    msg = await client.receive_json()
    result = msg["result"]

    assert result["Status"] == "driverAllNodesQueried"
    assert result[OZW_INSTANCE] == 1

    # Test node status
    await client.send_json({ID: 6, TYPE: "ozw/node_status", NODE_ID: 32})
    msg = await client.receive_json()
    result = msg["result"]

    assert result[OZW_INSTANCE] == 1
    assert result[NODE_ID] == 32
    assert result[ATTR_NODE_QUERY_STAGE] == "Complete"
    assert result[ATTR_IS_ZWAVE_PLUS]
    assert result[ATTR_IS_AWAKE]
    assert not result[ATTR_IS_FAILED]
    assert result[ATTR_NODE_BAUD_RATE] == 100000
    assert result[ATTR_IS_BEAMING]
    assert not result[ATTR_IS_FLIRS]
    assert result[ATTR_IS_ROUTING]
    assert not result[ATTR_IS_SECURITYV1]
    assert result[ATTR_NODE_BASIC_STRING] == "Routing Slave"
    assert result[ATTR_NODE_GENERIC_STRING] == "Binary Switch"
    assert result[ATTR_NODE_SPECIFIC_STRING] == "Binary Power Switch"
    assert result[ATTR_NEIGHBORS] == [1, 33, 36, 37, 39]

    await client.send_json({ID: 7, TYPE: "ozw/node_status", NODE_ID: 999})
    msg = await client.receive_json()
    result = msg["error"]
    assert result["code"] == ERR_NOT_FOUND

    # Test node statistics
    await client.send_json({ID: 8, TYPE: "ozw/node_statistics", NODE_ID: 39})
    msg = await client.receive_json()
    result = msg["result"]

    assert result[OZW_INSTANCE] == 1
    assert result[NODE_ID] == 39
    assert result["send_count"] == 57
    assert result["sent_failed"] == 0
    assert result["retries"] == 1
    assert result["last_request_rtt"] == 26
    assert result["last_response_rtt"] == 38
    assert result["average_request_rtt"] == 29
    assert result["average_response_rtt"] == 37
    assert result["received_packets"] == 3594
    assert result["received_dup_packets"] == 12
    assert result["received_unsolicited"] == 3546

    # Test node metadata
    await client.send_json({ID: 9, TYPE: "ozw/node_metadata", NODE_ID: 39})
    msg = await client.receive_json()
    result = msg["result"]
    assert result["metadata"]["ProductPic"] == "images/aeotec/zwa002.png"

    await client.send_json({ID: 10, TYPE: "ozw/node_metadata", NODE_ID: 999})
    msg = await client.receive_json()
    result = msg["error"]
    assert result["code"] == ERR_NOT_FOUND

    # Test network statistics
    await client.send_json({ID: 11, TYPE: "ozw/network_statistics"})
    msg = await client.receive_json()
    result = msg["result"]
    assert result["readCnt"] == 92220
    assert result[OZW_INSTANCE] == 1
    assert result["node_count"] == 5

    # Test get nodes
    await client.send_json({ID: 12, TYPE: "ozw/get_nodes"})
    msg = await client.receive_json()
    result = msg["result"]
    assert len(result) == 5
    assert result[2][ATTR_IS_AWAKE]
    assert not result[1][ATTR_IS_FAILED]

    # Test get config parameters
    await client.send_json({ID: 13, TYPE: "ozw/get_config_parameters", NODE_ID: 39})
    msg = await client.receive_json()
    result = msg["result"]
    assert len(result) == 8
    for config_param in result:
        assert config_param["type"] in (
            ValueType.LIST.value,
            ValueType.BOOL.value,
            ValueType.STRING.value,
            ValueType.INT.value,
            ValueType.BYTE.value,
            ValueType.SHORT.value,
        )

    # Test set config parameter
    config_param = result[0]
    current_val = config_param[ATTR_VALUE]
    new_val = next(
        option["Value"]
        for option in config_param[ATTR_OPTIONS]
        if option["Label"] != current_val
    )
    new_label = next(
        option["Label"]
        for option in config_param[ATTR_OPTIONS]
        if option["Label"] != current_val and option["Value"] != new_val
    )
    await client.send_json(
        {
            ID: 14,
            TYPE: "ozw/set_config_parameter",
            NODE_ID: 39,
            PARAMETER: config_param[ATTR_CONFIG_PARAMETER],
            VALUE: new_val,
        }
    )
    msg = await client.receive_json()
    assert msg["success"]
    await client.send_json(
        {
            ID: 15,
            TYPE: "ozw/set_config_parameter",
            NODE_ID: 39,
            PARAMETER: config_param[ATTR_CONFIG_PARAMETER],
            VALUE: new_label,
        }
    )
    msg = await client.receive_json()
    assert msg["success"]

    # Test OZW Instance not found error
    await client.send_json(
        {ID: 16, TYPE: "ozw/get_config_parameters", OZW_INSTANCE: 999, NODE_ID: 1}
    )
    msg = await client.receive_json()
    result = msg["error"]
    assert result["code"] == ERR_NOT_FOUND

    # Test OZW Node configuration class not found when setting config parameter
    await client.send_json(
        {
            ID: 18,
            TYPE: "ozw/set_config_parameter",
            NODE_ID: 999,
            PARAMETER: 0,
            VALUE: "test",
        }
    )
    msg = await client.receive_json()
    result = msg["error"]
    assert result["code"] == ERR_NOT_FOUND


async def test_websocket_api_config_class_not_found(
    hass, cover_gdo_data, hass_ws_client
):
    """Test OZW Node configuration class not found error."""
    await setup_ozw(hass, fixture=cover_gdo_data)
    client = await hass_ws_client(hass)

    await client.send_json({ID: 1, TYPE: "ozw/get_config_parameters", NODE_ID: 6})
    msg = await client.receive_json()
    result = msg["error"]
    assert result["code"] == ERR_NOT_FOUND


async def test_refresh_node(hass, generic_data, sent_messages, hass_ws_client):
    """Test the ozw refresh node api."""
    receive_message = await setup_ozw(hass, fixture=generic_data)
    client = await hass_ws_client(hass)

    # Send the refresh_node_info command
    await client.send_json({ID: 9, TYPE: "ozw/refresh_node_info", NODE_ID: 39})
    msg = await client.receive_json()

    assert len(sent_messages) == 1
    assert msg["success"]

    # Receive a mock status update from OZW
    message = MQTTMessage(
        topic="OpenZWave/1/node/39/",
        payload={"NodeID": 39, "NodeQueryStage": "initializing"},
    )
    message.encode()
    receive_message(message)

    # Verify we got expected data on the websocket
    msg = await client.receive_json()
    result = msg["event"]
    assert result["type"] == "node_updated"
    assert result["node_query_stage"] == "initializing"

    # Send another mock status update from OZW
    message = MQTTMessage(
        topic="OpenZWave/1/node/39/",
        payload={"NodeID": 39, "NodeQueryStage": "versions"},
    )
    message.encode()
    receive_message(message)

    # Send a mock status update for a different node
    message = MQTTMessage(
        topic="OpenZWave/1/node/35/",
        payload={"NodeID": 35, "NodeQueryStage": "fake_shouldnt_be_received"},
    )
    message.encode()
    receive_message(message)

    # Verify we received the message for node 39 but not for node 35
    msg = await client.receive_json()
    result = msg["event"]
    assert result["type"] == "node_updated"
    assert result["node_query_stage"] == "versions"


async def test_refresh_node_unsubscribe(hass, generic_data, hass_ws_client):
    """Test unsubscribing the ozw refresh node api."""
    await setup_ozw(hass, fixture=generic_data)
    client = await hass_ws_client(hass)

    with patch("openzwavemqtt.OZWOptions.listen") as mock_listen:
        # Send the refresh_node_info command
        await client.send_json({ID: 9, TYPE: "ozw/refresh_node_info", NODE_ID: 39})
        await client.receive_json()

        # Send the unsubscribe command
        await client.send_json({ID: 10, TYPE: "unsubscribe_events", "subscription": 9})
        await client.receive_json()

        assert mock_listen.return_value.called
