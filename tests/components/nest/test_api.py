"""Tests for the Nest integration API glue library.

There are two interesting cases to exercise that have different strategies
for token refresh and for testing:
- API based requests, tested using aioclient_mock
- Pub/sub subcriber initialization, intercepted with patch()

The tests below exercise both cases during integration setup.
"""
import time
from unittest.mock import patch

import pytest

from homeassistant.components.nest import DOMAIN
from homeassistant.components.nest.const import API_URL, OAUTH2_TOKEN, SDM_SCOPES
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util import dt

from .common import (
    CLIENT_ID,
    CLIENT_SECRET,
    CONFIG,
    FAKE_REFRESH_TOKEN,
    FAKE_TOKEN,
    PROJECT_ID,
    TEST_CONFIGFLOW_YAML_ONLY,
    create_config_entry,
)

from tests.test_util.aiohttp import AiohttpClientMocker

FAKE_UPDATED_TOKEN = "fake-updated-token"


async def async_setup_sdm(hass):
    """Set up the integration."""
    assert await async_setup_component(hass, DOMAIN, CONFIG)
    await hass.async_block_till_done()


@pytest.mark.parametrize("nest_test_config", [TEST_CONFIGFLOW_YAML_ONLY])
async def test_auth(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    """Exercise authentication library creates valid credentials."""

    expiration_time = time.time() + 86400
    create_config_entry(expiration_time).add_to_hass(hass)

    # Prepare to capture credentials in API request.  Empty payloads just mean
    # no devices or structures are loaded.
    aioclient_mock.get(f"{API_URL}/enterprises/{PROJECT_ID}/structures", json={})
    aioclient_mock.get(f"{API_URL}/enterprises/{PROJECT_ID}/devices", json={})

    # Prepare to capture credentials for Subscriber
    captured_creds = None

    async def async_new_subscriber(
        creds, subscription_name, event_loop, async_callback
    ):
        """Capture credentials for tests."""
        nonlocal captured_creds
        captured_creds = creds
        return None  # GoogleNestSubscriber

    with patch(
        "google_nest_sdm.google_nest_subscriber.DefaultSubscriberFactory.async_new_subscriber",
        side_effect=async_new_subscriber,
    ) as new_subscriber_mock:
        await async_setup_sdm(hass)

    # Verify API requests are made with the correct credentials
    calls = aioclient_mock.mock_calls
    assert len(calls) == 2
    (method, url, data, headers) = calls[0]
    assert headers == {"Authorization": f"Bearer {FAKE_TOKEN}"}
    (method, url, data, headers) = calls[1]
    assert headers == {"Authorization": f"Bearer {FAKE_TOKEN}"}

    # Verify the susbcriber was created with the correct credentials
    assert len(new_subscriber_mock.mock_calls) == 1
    assert captured_creds
    creds = captured_creds
    assert creds.token == FAKE_TOKEN
    assert creds.refresh_token == FAKE_REFRESH_TOKEN
    assert int(dt.as_timestamp(creds.expiry)) == int(expiration_time)
    assert creds.valid
    assert not creds.expired
    assert creds.token_uri == OAUTH2_TOKEN
    assert creds.client_id == CLIENT_ID
    assert creds.client_secret == CLIENT_SECRET
    assert creds.scopes == SDM_SCOPES


@pytest.mark.parametrize("nest_test_config", [TEST_CONFIGFLOW_YAML_ONLY])
async def test_auth_expired_token(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Verify behavior of an expired token."""

    expiration_time = time.time() - 86400
    create_config_entry(expiration_time).add_to_hass(hass)

    # Prepare a token refresh response
    aioclient_mock.post(
        OAUTH2_TOKEN,
        json={
            "access_token": FAKE_UPDATED_TOKEN,
            "expires_at": time.time() + 86400,
            "expires_in": 86400,
        },
    )
    # Prepare to capture credentials in API request.  Empty payloads just mean
    # no devices or structures are loaded.
    aioclient_mock.get(f"{API_URL}/enterprises/{PROJECT_ID}/structures", json={})
    aioclient_mock.get(f"{API_URL}/enterprises/{PROJECT_ID}/devices", json={})

    # Prepare to capture credentials for Subscriber
    captured_creds = None

    async def async_new_subscriber(
        creds, subscription_name, event_loop, async_callback
    ):
        """Capture credentials for tests."""
        nonlocal captured_creds
        captured_creds = creds
        return None  # GoogleNestSubscriber

    with patch(
        "google_nest_sdm.google_nest_subscriber.DefaultSubscriberFactory.async_new_subscriber",
        side_effect=async_new_subscriber,
    ) as new_subscriber_mock:
        await async_setup_sdm(hass)

    calls = aioclient_mock.mock_calls
    assert len(calls) == 3
    # Verify refresh token call to get an updated token
    (method, url, data, headers) = calls[0]
    assert data == {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": FAKE_REFRESH_TOKEN,
    }
    # Verify API requests are made with the new token
    (method, url, data, headers) = calls[1]
    assert headers == {"Authorization": f"Bearer {FAKE_UPDATED_TOKEN}"}
    (method, url, data, headers) = calls[2]
    assert headers == {"Authorization": f"Bearer {FAKE_UPDATED_TOKEN}"}

    # The subscriber is created with a token that is expired.  Verify that the
    # credential is expired so the subscriber knows it needs to refresh it.
    assert len(new_subscriber_mock.mock_calls) == 1
    assert captured_creds
    creds = captured_creds
    assert creds.token == FAKE_TOKEN
    assert creds.refresh_token == FAKE_REFRESH_TOKEN
    assert int(dt.as_timestamp(creds.expiry)) == int(expiration_time)
    assert not creds.valid
    assert creds.expired
    assert creds.token_uri == OAUTH2_TOKEN
    assert creds.client_id == CLIENT_ID
    assert creds.client_secret == CLIENT_SECRET
    assert creds.scopes == SDM_SCOPES
