"""Test the Google Sheets config flow."""

from collections.abc import Generator
from types import MappingProxyType
from unittest.mock import Mock, patch

from gspread import GSpreadException
import oauth2client
import pytest

from homeassistant import config_entries
from homeassistant.components.application_credentials import (
    ClientCredential,
    async_import_client_credential,
)
from homeassistant.components.google_sheets.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.setup import async_setup_component

from tests.common import MockConfigEntry

CLIENT_ID = "1234"
CLIENT_SECRET = "5678"
SHEET_ID = "google-sheet-id"
TITLE = "Google Sheets"


@pytest.fixture
async def setup_credentials(hass: HomeAssistant) -> None:
    """Fixture to setup credentials."""
    assert await async_setup_component(hass, "application_credentials", {})
    await async_import_client_credential(
        hass,
        DOMAIN,
        ClientCredential(CLIENT_ID, CLIENT_SECRET),
    )


@pytest.fixture(autouse=True)
async def mock_client() -> Generator[Mock, None, None]:
    """Fixture to setup a fake spreadsheet client library."""
    with patch(
        "homeassistant.components.google_sheets.config_flow.Client"
    ) as mock_client:
        yield mock_client


async def test_full_flow(
    hass: HomeAssistant,
    hass_client_no_auth,
    aioclient_mock,
    current_request_with_host,
    setup_credentials,
    mock_client,
) -> None:
    """Check full flow."""
    result = await hass.config_entries.flow.async_init(
        "google_sheets", context={"source": config_entries.SOURCE_USER}
    )
    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )

    assert result["url"] == (
        f"{oauth2client.GOOGLE_AUTH_URI}?response_type=code&client_id={CLIENT_ID}"
        "&redirect_uri=https://example.com/auth/external/callback"
        f"&state={state}&scope=https://www.googleapis.com/auth/drive.file"
        "+https://www.googleapis.com/auth/spreadsheets.readonly"
        "&access_type=offline&prompt=consent"
    )

    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    assert resp.status == 200
    assert resp.headers["content-type"] == "text/html; charset=utf-8"

    # Prepare fake client library response when creating the sheet
    mock_create = Mock()
    mock_create.return_value.id = SHEET_ID
    mock_client.return_value.create = mock_create

    aioclient_mock.post(
        oauth2client.GOOGLE_TOKEN_URI,
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "type": "Bearer",
            "expires_in": 60,
        },
    )

    with patch(
        "homeassistant.components.google_sheets.async_setup_entry", return_value=True
    ) as mock_setup:
        result = await hass.config_entries.flow.async_configure(result["flow_id"])

    assert len(hass.config_entries.async_entries(DOMAIN)) == 1
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_client.mock_calls) == 2

    assert result.get("type") == "create_entry"
    assert result.get("title") == TITLE
    assert "result" in result
    assert result.get("result").unique_id == SHEET_ID
    assert "token" in result.get("result").data
    assert result.get("result").data["token"].get("access_token") == "mock-access-token"
    assert (
        result.get("result").data["token"].get("refresh_token") == "mock-refresh-token"
    )


async def test_create_sheet_error(
    hass: HomeAssistant,
    hass_client_no_auth,
    aioclient_mock,
    current_request_with_host,
    setup_credentials,
    mock_client,
) -> None:
    """Test case where creating the spreadsheet fails."""
    result = await hass.config_entries.flow.async_init(
        "google_sheets", context={"source": config_entries.SOURCE_USER}
    )
    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )

    assert result["url"] == (
        f"{oauth2client.GOOGLE_AUTH_URI}?response_type=code&client_id={CLIENT_ID}"
        "&redirect_uri=https://example.com/auth/external/callback"
        f"&state={state}&scope=https://www.googleapis.com/auth/drive.file"
        "+https://www.googleapis.com/auth/spreadsheets.readonly"
        "&access_type=offline&prompt=consent"
    )

    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    assert resp.status == 200
    assert resp.headers["content-type"] == "text/html; charset=utf-8"

    # Prepare fake exception creating the spreadsheet
    mock_create = Mock()
    mock_create.side_effect = GSpreadException()
    mock_client.return_value.create = mock_create

    aioclient_mock.post(
        oauth2client.GOOGLE_TOKEN_URI,
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "type": "Bearer",
            "expires_in": 60,
        },
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    assert result.get("type") == "abort"
    assert result.get("reason") == "create_spreadsheet_failure"


async def test_reauth(
    hass: HomeAssistant,
    config_entry_with_options: MockConfigEntry,
    hass_client_no_auth,
    aioclient_mock,
    current_request_with_host,
    setup_credentials,
    mock_client,
) -> None:
    """Test the reauthentication case updates the existing config entry."""
    config_entry_with_options.add_to_hass(hass)

    config_entry_with_options.async_start_reauth(hass)
    await hass.async_block_till_done()

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1
    result = flows[0]
    assert result["step_id"] == "reauth_confirm"

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )
    assert result["url"] == (
        f"{oauth2client.GOOGLE_AUTH_URI}?response_type=code&client_id={CLIENT_ID}"
        "&redirect_uri=https://example.com/auth/external/callback"
        f"&state={state}&scope=https://www.googleapis.com/auth/drive.file"
        "+https://www.googleapis.com/auth/spreadsheets.readonly"
        "&access_type=offline&prompt=consent"
    )
    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    assert resp.status == 200
    assert resp.headers["content-type"] == "text/html; charset=utf-8"

    # Config flow will lookup existing key to make sure it still exists
    mock_open = Mock()
    mock_open.return_value.id = SHEET_ID
    mock_client.return_value.open_by_key = mock_open

    aioclient_mock.post(
        oauth2client.GOOGLE_TOKEN_URI,
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "updated-access-token",
            "type": "Bearer",
            "expires_in": 60,
        },
    )

    with patch(
        "homeassistant.components.google_sheets.async_setup_entry", return_value=True
    ) as mock_setup:
        result = await hass.config_entries.flow.async_configure(result["flow_id"])

    assert len(hass.config_entries.async_entries(DOMAIN)) == 1
    assert len(mock_setup.mock_calls) == 1

    assert result.get("type") == "abort"
    assert result.get("reason") == "reauth_successful"

    assert config_entry_with_options.unique_id == SHEET_ID
    assert "token" in config_entry_with_options.data
    # Verify access token is refreshed
    assert (
        config_entry_with_options.data["token"].get("access_token")
        == "updated-access-token"
    )
    assert (
        config_entry_with_options.data["token"].get("refresh_token")
        == "mock-refresh-token"
    )


async def test_reauth_abort(
    hass: HomeAssistant,
    config_entry_with_options: MockConfigEntry,
    hass_client_no_auth,
    aioclient_mock,
    current_request_with_host,
    setup_credentials,
    mock_client,
) -> None:
    """Test failure case during reauth."""
    config_entry_with_options.add_to_hass(hass)

    config_entry_with_options.async_start_reauth(hass)
    await hass.async_block_till_done()

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1
    result = flows[0]
    assert result["step_id"] == "reauth_confirm"

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )
    assert result["url"] == (
        f"{oauth2client.GOOGLE_AUTH_URI}?response_type=code&client_id={CLIENT_ID}"
        "&redirect_uri=https://example.com/auth/external/callback"
        f"&state={state}&scope=https://www.googleapis.com/auth/drive.file"
        "+https://www.googleapis.com/auth/spreadsheets.readonly"
        "&access_type=offline&prompt=consent"
    )
    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    assert resp.status == 200
    assert resp.headers["content-type"] == "text/html; charset=utf-8"

    # Simulate failure looking up existing spreadsheet
    mock_open = Mock()
    mock_open.return_value.id = SHEET_ID
    mock_open.side_effect = GSpreadException()
    mock_client.return_value.open_by_key = mock_open

    aioclient_mock.post(
        oauth2client.GOOGLE_TOKEN_URI,
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "updated-access-token",
            "type": "Bearer",
            "expires_in": 60,
        },
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    assert result.get("type") == "abort"
    assert result.get("reason") == "open_spreadsheet_failure"


async def test_options_flow_no_changes(
    hass: HomeAssistant,
    scopes: list[str],
    config_entry_with_options: MockConfigEntry,
) -> None:
    """Test load and unload of a ConfigEntry."""
    config_entry_with_options.add_to_hass(hass)

    with patch(
        "homeassistant.components.google_sheets.async_setup_entry", return_value=True
    ) as mock_setup:
        await hass.config_entries.async_setup(config_entry_with_options.entry_id)
        mock_setup.assert_called_once()

    assert config_entry_with_options.state is config_entries.ConfigEntryState.LOADED
    assert config_entry_with_options.options == MappingProxyType(
        {"sheets_access": "read_only"}
    )

    result = await hass.config_entries.options.async_init(
        config_entry_with_options.entry_id
    )
    assert result["type"] == "form"
    assert result["step_id"] == "init"
    data_schema = result["data_schema"].schema
    assert set(data_schema) == {"sheets_access"}

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"sheets_access": "read_only"},
    )
    assert result["type"] == "create_entry"
    assert config_entry_with_options.options == {"sheets_access": "read_only"}


async def test_already_configured(
    hass: HomeAssistant,
    hass_client_no_auth,
    aioclient_mock,
    current_request_with_host,
    setup_credentials,
    mock_client,
) -> None:
    """Test case where config flow discovers unique id was already configured."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=SHEET_ID,
        data={
            "token": {
                "access_token": "mock-access-token",
            },
        },
    )
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        "google_sheets", context={"source": config_entries.SOURCE_USER}
    )
    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )

    assert result["url"] == (
        f"{oauth2client.GOOGLE_AUTH_URI}?response_type=code&client_id={CLIENT_ID}"
        "&redirect_uri=https://example.com/auth/external/callback"
        f"&state={state}&scope=https://www.googleapis.com/auth/drive.file"
        "+https://www.googleapis.com/auth/spreadsheets.readonly"
        "&access_type=offline&prompt=consent"
    )

    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    assert resp.status == 200
    assert resp.headers["content-type"] == "text/html; charset=utf-8"

    # Prepare fake client library response when creating the sheet
    mock_create = Mock()
    mock_create.return_value.id = SHEET_ID
    mock_client.return_value.create = mock_create

    aioclient_mock.post(
        oauth2client.GOOGLE_TOKEN_URI,
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "type": "Bearer",
            "expires_in": 60,
        },
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    assert result.get("type") == "abort"
    assert result.get("reason") == "already_configured"


async def test_options_flow(
    hass: HomeAssistant,
    scopes: list[str],
    config_entry_with_options: MockConfigEntry,
) -> None:
    """Test options flow."""
    config_entry_with_options.add_to_hass(hass)

    with patch(
        "homeassistant.components.google_sheets.async_setup_entry", return_value=True
    ) as mock_setup:
        await hass.config_entries.async_setup(config_entry_with_options.entry_id)
        mock_setup.assert_called_once()

    assert config_entry_with_options.state is config_entries.ConfigEntryState.LOADED
    assert config_entry_with_options.options == MappingProxyType(
        {"sheets_access": "read_only"}
    )

    result = await hass.config_entries.options.async_init(
        config_entry_with_options.entry_id
    )
    assert result["type"] == "form"
    assert result["step_id"] == "init"
    data_schema = result["data_schema"].schema
    assert set(data_schema) == {"sheets_access"}

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"sheets_access": "read_write"},
    )
    assert result["type"] == "create_entry"
    assert config_entry_with_options.options == {"sheets_access": "read_write"}
