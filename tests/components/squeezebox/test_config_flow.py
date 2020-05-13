"""Test the Logitech Squeezebox config flow."""
from asynctest import patch

from homeassistant import config_entries, setup
from homeassistant.components.squeezebox.config_flow import CannotConnect, InvalidAuth
from homeassistant.components.squeezebox.const import DOMAIN
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME


async def test_form(hass):
    """Test user-initiated flow."""
    await setup.async_setup_component(hass, "persistent_notification", {})
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["step_id"] == "user"

    with patch(
        "homeassistant.components.squeezebox.config_flow.validate_input",
        return_value={
            "uuid": "test-uuid",
            CONF_HOST: "1.1.1.1",
            CONF_PORT: 9000,
            "ip": "1.1.1.1",
        },
    ), patch(
        "homeassistant.components.squeezebox.async_setup", return_value=True
    ) as mock_setup, patch(
        "homeassistant.components.squeezebox.async_setup_entry", return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_HOST: "1.1.1.1"}
        )
        assert result["type"] == "form"
        assert result["step_id"] == "edit"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.1.1.1",
                CONF_PORT: 9000,
                CONF_USERNAME: "",
                CONF_PASSWORD: "",
            },
        )
        assert result["type"] == "create_entry"
        assert result["title"] == "1.1.1.1"
        assert result["data"] == {
            CONF_HOST: "1.1.1.1",
            CONF_PORT: 9000,
            CONF_USERNAME: "",
            CONF_PASSWORD: "",
        }

        await hass.async_block_till_done()
        assert len(mock_setup.mock_calls) == 1
        assert len(mock_setup_entry.mock_calls) == 1


async def test_form_invalid_auth(hass):
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "edit"}
    )

    with patch(
        "homeassistant.components.squeezebox.config_flow.validate_input",
        side_effect=InvalidAuth,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.1.1.1",
                CONF_PORT: 9000,
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
            },
        )

    assert result["type"] == "form"
    assert result["errors"] == {"base": "invalid_auth"}


async def test_form_cannot_connect(hass):
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "edit"}
    )

    with patch(
        "homeassistant.components.squeezebox.config_flow.validate_input",
        side_effect=CannotConnect,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.1.1.1",
                CONF_PORT: 9000,
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
            },
        )

    assert result["type"] == "form"
    assert result["errors"] == {"base": "cannot_connect"}
