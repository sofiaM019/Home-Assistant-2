"""Tests for the Stookwijzer config flow."""

from unittest.mock import patch

from homeassistant.components.stookwijzer.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import CONF_DATA, CONF_INPUT, mock_available, mock_transform_failure

from tests.test_util.aiohttp import AiohttpClientMocker


async def test_full_user_flow(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test the full user configuration flow."""
    mock_available(aioclient_mock)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "user"
    assert "flow_id" in result

    with patch(
        "homeassistant.components.stookwijzer.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=CONF_INPUT,
        )

    assert result2.get("type") == FlowResultType.CREATE_ENTRY
    assert result2.get("data") == CONF_DATA

    assert len(mock_setup_entry.mock_calls) == 1


async def test_flow_while_unavailable(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test the full user configuration flow while unavailable."""
    mock_transform_failure(aioclient_mock)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER, "version": 1}
    )

    with patch(
        "homeassistant.components.stookwijzer.async_setup_entry", return_value=True
    ):
        await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=CONF_INPUT,
        )
