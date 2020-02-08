"""Configure py.test."""
from asynctest import patch
import pytest
from pyvizio.const import DEVICE_CLASS_SPEAKER, MAX_VOLUME

from .const import (
    ACCESS_TOKEN,
    CH_TYPE,
    CURRENT_INPUT,
    INPUT_LIST,
    MODEL,
    RESPONSE_TOKEN,
    UNIQUE_ID,
    VERSION,
    MockCompletePairingResponse,
    MockStartPairingResponse,
)


class MockInput:
    """Mock Vizio device input."""

    def __init__(self, name):
        """Initialize mock Vizio device input."""
        self.meta_name = name
        self.name = name


def get_mock_inputs(input_list):
    """Return list of MockInput."""
    return [MockInput(input) for input in input_list]


@pytest.fixture(name="skip_notifications", autouse=True)
def skip_notifications_fixture():
    """Skip notification calls."""
    with patch("homeassistant.components.persistent_notification.async_create"), patch(
        "homeassistant.components.persistent_notification.async_dismiss"
    ):
        yield


@pytest.fixture(name="vizio_connect_with_valid_auth")
def vizio_connect_with_valid_auth_fixture():
    """Mock valid vizio device and entry setup."""
    with patch(
        "homeassistant.components.vizio.config_flow.VizioAsync.validate_ha_config",
        return_value=True,
    ), patch(
        "homeassistant.components.vizio.config_flow.VizioAsync.can_connect_no_auth_check",
        return_value=True,
    ), patch(
        "homeassistant.components.vizio.config_flow.VizioAsync.get_unique_id",
        return_value=UNIQUE_ID,
    ):
        yield


@pytest.fixture(name="vizio_complete_pairing")
def vizio_complete_pairing_fixture():
    """Mock complete vizio pairing workflow."""
    with patch(
        "homeassistant.components.vizio.config_flow.VizioAsync.start_pair",
        return_value=MockStartPairingResponse(CH_TYPE, RESPONSE_TOKEN),
    ), patch(
        "homeassistant.components.vizio.config_flow.VizioAsync.pair",
        return_value=MockCompletePairingResponse(ACCESS_TOKEN),
    ):
        yield


@pytest.fixture(name="vizio_start_pairing_failure")
def vizio_start_pairing_failure_fixture():
    """Mock vizio start pairing failure."""
    with patch(
        "homeassistant.components.vizio.config_flow.VizioAsync.start_pair",
        return_value=None,
    ):
        yield


@pytest.fixture(name="vizio_invalid_pin_failure")
def vizio_invalid_pin_failure_fixture():
    """Mock vizio failure due to invalid pin."""
    with patch(
        "homeassistant.components.vizio.config_flow.VizioAsync.start_pair",
        return_value=MockStartPairingResponse(CH_TYPE, RESPONSE_TOKEN),
    ), patch(
        "homeassistant.components.vizio.config_flow.VizioAsync.pair", return_value=None,
    ):
        yield


@pytest.fixture(name="vizio_bypass_setup")
def vizio_bypass_setup_fixture():
    """Mock component setup."""
    with patch("homeassistant.components.vizio.async_setup_entry", return_value=True):
        yield


@pytest.fixture(name="vizio_bypass_update")
def vizio_bypass_update_fixture():
    """Mock component update."""
    with patch(
        "homeassistant.components.vizio.media_player.VizioAsync.can_connect_with_auth_check",
        return_value=True,
    ), patch("homeassistant.components.vizio.media_player.VizioDevice.async_update"):
        yield


@pytest.fixture(name="vizio_guess_device_type")
def vizio_guess_device_type_fixture():
    """Mock vizio async_guess_device_type function."""
    with patch(
        "homeassistant.components.vizio.config_flow.async_guess_device_type",
        return_value="speaker",
    ):
        yield


@pytest.fixture(name="vizio_cant_connect")
def vizio_cant_connect_fixture():
    """Mock vizio device can't connect with valid auth."""
    with patch(
        "homeassistant.components.vizio.config_flow.VizioAsync.validate_ha_config",
        return_value=False,
    ), patch(
        "homeassistant.components.vizio.config_flow.VizioAsync.can_connect_no_auth_check",
        return_value=False,
    ):
        yield


@pytest.fixture(name="vizio_update")
def vizio_update_fixture():
    """Mock valid updates to vizio device."""
    with patch(
        "homeassistant.components.vizio.media_player.VizioAsync.can_connect_with_auth_check",
        return_value=True,
    ), patch(
        "homeassistant.components.vizio.media_player.VizioAsync.get_current_volume",
        return_value=int(MAX_VOLUME[DEVICE_CLASS_SPEAKER] / 2),
    ), patch(
        "homeassistant.components.vizio.media_player.VizioAsync.get_current_input",
        return_value=CURRENT_INPUT,
    ), patch(
        "homeassistant.components.vizio.media_player.VizioAsync.get_inputs_list",
        return_value=get_mock_inputs(INPUT_LIST),
    ), patch(
        "homeassistant.components.vizio.media_player.VizioAsync.get_power_state",
        return_value=True,
    ), patch(
        "homeassistant.components.vizio.media_player.VizioAsync.get_model_name",
        return_value=MODEL,
    ), patch(
        "homeassistant.components.vizio.media_player.VizioAsync.get_version",
        return_value=VERSION,
    ):
        yield
