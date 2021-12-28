"""Test the SenseME config flow."""
from unittest.mock import patch

from homeassistant import config_entries
from homeassistant.components.senseme.const import DOMAIN
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import RESULT_TYPE_CREATE_ENTRY, RESULT_TYPE_FORM

from . import MOCK_ADDRESS, MOCK_DEVICE, MOCK_UUID, _patch_discovery


async def test_form_user(hass: HomeAssistant) -> None:
    """Test we get the form as a user."""

    with _patch_discovery(), patch(
        "homeassistant.components.senseme.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] == RESULT_TYPE_FORM
        assert not result["errors"]

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "device": MOCK_UUID,
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] == RESULT_TYPE_CREATE_ENTRY
    assert result2["title"] == "Haiku Fan"
    assert result2["data"] == {
        "info": MOCK_DEVICE.get_device_info,
    }
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_user_manual_entry(hass: HomeAssistant) -> None:
    """Test we get the form as a user with a discovery but user chooses manual."""

    with _patch_discovery():
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] == RESULT_TYPE_FORM
        assert not result["errors"]

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "device": None,
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] == RESULT_TYPE_FORM
    assert result2["step_id"] == "manual"

    with patch(
        "homeassistant.components.senseme.config_flow.async_get_device_by_ip_address",
        return_value=MOCK_DEVICE,
    ), patch(
        "homeassistant.components.senseme.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: MOCK_ADDRESS,
            },
        )
        await hass.async_block_till_done()

    assert result3["title"] == "Haiku Fan"
    assert result3["data"] == {
        "info": MOCK_DEVICE.get_device_info,
    }
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_user_no_discovery(hass: HomeAssistant) -> None:
    """Test we get the form as a user with no discovery."""

    with _patch_discovery(no_device=True), patch(
        "homeassistant.components.senseme.config_flow.async_get_device_by_ip_address",
        return_value=MOCK_DEVICE,
    ), patch(
        "homeassistant.components.senseme.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] == RESULT_TYPE_FORM
        assert not result["errors"]

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: MOCK_ADDRESS,
            },
        )
        await hass.async_block_till_done()

    assert result2["title"] == "Haiku Fan"
    assert result2["data"] == {
        "info": MOCK_DEVICE.get_device_info,
    }
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_user_manual_entry_cannot_connect(hass: HomeAssistant) -> None:
    """Test we get the form as a user."""

    with _patch_discovery():
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] == RESULT_TYPE_FORM
        assert not result["errors"]

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "device": None,
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] == RESULT_TYPE_FORM
    assert result2["step_id"] == "manual"

    with patch(
        "homeassistant.components.senseme.config_flow.async_get_device_by_ip_address",
        return_value=None,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: MOCK_ADDRESS,
            },
        )
        await hass.async_block_till_done()

    assert result3["type"] == RESULT_TYPE_FORM
    assert result3["step_id"] == "manual"
    assert result3["errors"] == {CONF_HOST: "cannot_connect"}
