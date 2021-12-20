"""Tests for the pvpc_hourly_pricing integration."""
import pytest

from homeassistant.components.pvpc_hourly_pricing import ATTR_TARIFF, DOMAIN
from homeassistant.const import (
    ATTR_UNIT_OF_MEASUREMENT,
    CURRENCY_EURO,
    ENERGY_KILO_WATT_HOUR,
)

from tests.common import load_fixture
from tests.test_util.aiohttp import AiohttpClientMocker

FIXTURE_JSON_DATA_2021_10_31 = "PVPC_DATA_2021_10_31.json"
FIXTURE_JSON_DATA_2021_10_30 = "PVPC_DATA_2021_10_30.json"
FIXTURE_JSON_DATA_2021_06_01 = "PVPC_DATA_2021_06_01.json"


def check_valid_state(state, tariff: str, value=None, key_attr=None):
    """Ensure that sensor has a valid state and attributes."""
    assert state
    assert (
        state.attributes[ATTR_UNIT_OF_MEASUREMENT]
        == f"{CURRENCY_EURO}/{ENERGY_KILO_WATT_HOUR}"
    )
    try:
        _ = float(state.state)
        # safety margins for current electricity price (it shouldn't be out of [0, 0.2])
        assert -0.1 < float(state.state) < 0.5
        assert state.attributes[ATTR_TARIFF] == tariff
    except ValueError:
        pass

    if value is not None and isinstance(value, str):
        assert state.state == value
    elif value is not None:
        assert abs(float(state.state) - value) < 1e-6
    if key_attr is not None:
        assert abs(float(state.state) - state.attributes[key_attr]) < 1e-6


@pytest.fixture
def pvpc_aioclient_mock(aioclient_mock: AiohttpClientMocker):
    """Create a mock config entry."""
    mask_url = "https://apidatos.ree.es/es/datos/mercados/precios-mercados-tiempo-real"
    mask_url += "?time_trunc=hour&geo_ids={0}&start_date={1}T00:00&end_date={1}T23:59"
    # new format for prices >= 2021-06-01
    aioclient_mock.get(
        mask_url.format(8741, "2021-06-01"),
        text=load_fixture(f"{DOMAIN}/{FIXTURE_JSON_DATA_2021_06_01}"),
    )
    # tariff variant with different geo_ids=8744
    aioclient_mock.get(
        mask_url.format(8744, "2021-06-01"),
        text=load_fixture(f"{DOMAIN}/{FIXTURE_JSON_DATA_2021_06_01}"),
    )
    # dst change
    aioclient_mock.get(
        mask_url.format(8741, "2021-10-30"),
        text=load_fixture(f"{DOMAIN}/{FIXTURE_JSON_DATA_2021_10_30}"),
    )
    aioclient_mock.get(
        mask_url.format(8741, "2021-10-31"),
        text=load_fixture(f"{DOMAIN}/{FIXTURE_JSON_DATA_2021_10_31}"),
    )
    # simulate missing day
    aioclient_mock.get(
        mask_url.format(8741, "2021-11-01"),
        text='{"message":"No values for specified archive"}',
    )
    aioclient_mock.get(
        mask_url.format(8741, "2021-11-02"),
        text=(
            load_fixture(f"{DOMAIN}/{FIXTURE_JSON_DATA_2021_10_30}")
            .replace("10-30", "11-02")
            .replace("+02:00", "+01:00")
        ),
    )

    return aioclient_mock
