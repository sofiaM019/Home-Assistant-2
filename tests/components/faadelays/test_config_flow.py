"""Test the FAA Delays config flow."""
from aiohttp import ClientConnectionError
import faadelays

from homeassistant import config_entries, setup
from homeassistant.components.faadelays.const import DOMAIN
from homeassistant.const import CONF_ID
from homeassistant.exceptions import HomeAssistantError

from tests.async_mock import patch


async def mock_valid_airport(self, *args, **kwargs):
    """Return a valid airport."""
    self.name = "Test airport"


async def test_form(hass):
    """Test we get the form."""
    await setup.async_setup_component(hass, "persistent_notification", {})
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    with patch.object(faadelays.Airport, "update", new=mock_valid_airport), patch(
        "homeassistant.components.faadelays.async_setup", return_value=True
    ) as mock_setup, patch(
        "homeassistant.components.faadelays.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "id": "test",
            },
        )

    assert result2["type"] == "create_entry"
    assert result2["title"] == "Test airport"
    assert result2["data"] == {
        "id": "test",
    }
    await hass.async_block_till_done()
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_invalid_airport(hass):
    """Test we handle invalid airport."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "faadelays.Airport.update",
        side_effect=faadelays.InvalidAirport,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "id": "test",
            },
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {CONF_ID: "invalid_airport"}


async def test_form_cannot_connect(hass):
    """Test we handle a connection error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch("faadelays.Airport.update", side_effect=ClientConnectionError):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "id": "test",
            },
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_form_unexpected_exception(hass):
    """Test we handle an unexpected exception."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch("faadelays.Airport.update", side_effect=HomeAssistantError):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "id": "test",
            },
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "unknown"}
