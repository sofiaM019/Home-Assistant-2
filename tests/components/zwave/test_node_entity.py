"""Test Z-Wave node entity."""
import asyncio
import unittest
from unittest.mock import patch
from unittest.mock import patch, MagicMock
from tests.common import get_test_home_assistant
import tests.mock.zwave as mock_zwave
import pytest
from homeassistant.components.zwave import node_entity


@asyncio.coroutine
def test_maybe_schedule_update(hass, mock_openzwave):
    """Test maybe schedule update."""
    base_entity = node_entity.ZWaveBaseEntity()
    base_entity.hass = hass

    with patch.object(hass.loop, 'call_later') as mock_call_later:
        base_entity._schedule_update()
        assert mock_call_later.called

        base_entity._schedule_update()
        assert len(mock_call_later.mock_calls) == 1

        do_update = mock_call_later.mock_calls[0][1][1]

        with patch.object(hass, 'async_add_job') as mock_add_job:
            do_update()
            assert mock_add_job.called

        base_entity._schedule_update()
        assert len(mock_call_later.mock_calls) == 2


@pytest.mark.usefixtures('mock_openzwave')
class TestZWaveNodeEntity(unittest.TestCase):
    """Class to test ZWaveNodeEntity."""

    def setUp(self):
        """Initialize values for this testcase class."""
        NETWORK = MagicMock()
        self.node = mock_zwave.MockNode(
            query_stage='Dynamic', is_awake=True, is_ready=False,
            is_failed=False, is_info_received=True, max_baud_rate=40000,
            is_zwave_plus=False, capabilities=[], neighbors=[], location=None)
        self.entity = node_entity.ZWaveNodeEntity(self.node, NETWORK)

    def test_network_node_changed_from_value(self):
        """Test for network_node_changed."""
        value = mock_zwave.MockValue(node=self.node)
        with patch.object(self.entity, 'maybe_schedule_update') as mock:
            mock_zwave.value_changed(value)
            mock.assert_called_once_with()

    def test_network_node_changed_from_node(self):
        """Test for network_node_changed."""
        with patch.object(self.entity, 'maybe_schedule_update') as mock:
            mock_zwave.node_changed(self.node)
            mock.assert_called_once_with()

    def test_network_node_changed_from_another_node(self):
        """Test for network_node_changed."""
        with patch.object(self.entity, 'maybe_schedule_update') as mock:
            node = mock_zwave.MockNode(node_id=1024)
            mock_zwave.node_changed(node)
            self.assertFalse(mock.called)

    def test_network_node_changed_from_notification(self):
        """Test for network_node_changed."""
        with patch.object(self.entity, 'maybe_schedule_update') as mock:
            mock_zwave.notification(node_id=self.node.node_id)
            mock.assert_called_once_with()

    def test_network_node_changed_from_another_notification(self):
        """Test for network_node_changed."""
        with patch.object(self.entity, 'maybe_schedule_update') as mock:
            mock_zwave.notification(node_id=1024)
            self.assertFalse(mock.called)

    def test_node_changed(self):
        """Test node_changed function."""
        self.maxDiff = None
        self.assertEqual({'node_id': self.node.node_id},
                         self.entity.device_state_attributes)

        self.node.get_values.return_value = {
            1: mock_zwave.MockValue(data=1800)
        }
        self.entity.node_changed()
        self.assertEqual(
            {'node_id': self.node.node_id,
             'query_stage': 'Dynamic',
             'is_awake': True,
             'is_ready': False,
             'is_failed': False,
             'is_info_received': True,
             'max_baud_rate': 40000,
             'is_zwave_plus': False,
             'battery_level': 42,
             'wake_up_interval': 1800,
             'averageRequestRTT': 1,
             'averageResponseRTT': 2,
             'lastRequestRTT': 3,
             'lastResponseRTT': 4,
             'receivedCnt': 5,
             'receivedDups': 6,
             'receivedTS': 7,
             'receivedUnsolicited': 8,
             'retries': 9,
             'sentCnt': 10,
             'sentFailed': 11,
             'sentTS': 12},
            self.entity.device_state_attributes)

        self.node.can_wake_up_value = False
        self.entity.node_changed()

        self.assertNotIn(
            'wake_up_interval', self.entity.device_state_attributes)

    def test_name(self):
        """Test name property."""
        self.assertEqual('Mock Node', self.entity.name)

    def test_state_before_update(self):
        """Test state before update was called."""
        self.assertIsNone(self.entity.state)

    def test_state_not_ready(self):
        """Test state property."""
        self.node.is_ready = False
        self.entity.node_changed()
        self.assertEqual('Dynamic', self.entity.state)

        self.node.is_failed = True
        self.entity.node_changed()
        self.assertEqual('Dead (Dynamic)', self.entity.state)

        self.node.is_failed = False
        self.node.is_awake = False
        self.entity.node_changed()
        self.assertEqual('Sleeping (Dynamic)', self.entity.state)

    def test_state_ready(self):
        """Test state property."""
        self.node.is_ready = True
        self.entity.node_changed()
        self.assertEqual('Ready', self.entity.state)

        self.node.is_failed = True
        self.entity.node_changed()
        self.assertEqual('Dead', self.entity.state)

        self.node.is_failed = False
        self.node.is_awake = False
        self.entity.node_changed()
        self.assertEqual('Sleeping', self.entity.state)

    def test_not_polled(self):
        """Test should_poll property."""
        self.assertFalse(self.entity.should_poll)


def test_sub_status():
    """Test sub_status function."""
    assert node_entity.sub_status('Status', 'Stage') == 'Status (Stage)'
    assert node_entity.sub_status('Status', '') == 'Status'
