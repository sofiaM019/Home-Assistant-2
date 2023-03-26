"""Test the myStrom config flow."""
from unittest.mock import patch

from homeassistant import config_entries
from homeassistant.components.mystrom.const import DOMAIN
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from .conftest import ResponseMock

DEVICE_NAME = "test-myStrom Device"


async def test_form(hass: HomeAssistant) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {}

    with patch("pymystrom.switch.MyStromSwitch.get_state") as mock_switch, patch(
        "aiohttp.ClientSession.get", return_value=ResponseMock({"type": 101}, 200)
    ) as mock_session:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "1.1.1.1",
                "name": DEVICE_NAME,
            },
        )
        await hass.async_block_till_done()

        assert result2["type"] == FlowResultType.CREATE_ENTRY
        assert result2["title"] == DEVICE_NAME
        assert result2["data"] == {
            "host": "1.1.1.1",
            "name": DEVICE_NAME,
        }
    assert len(mock_session.mock_calls) == 1
    assert len(mock_switch.mock_calls) == 1


async def test_form_invalid_host(hass: HomeAssistant) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "host": "1.1.1.$",
            "name": DEVICE_NAME,
        },
    )

    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_step_import(hass: HomeAssistant) -> None:
    """Test the import step."""
    conf = {
        CONF_HOST: "1.1.1.1",
        CONF_NAME: DEVICE_NAME,
    }
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_IMPORT}, data=conf
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == DEVICE_NAME
    assert result["data"] == {
        CONF_HOST: "1.1.1.1",
        CONF_NAME: DEVICE_NAME,
    }
