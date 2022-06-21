"""The tests for the Home Assistant HTTP component."""
from datetime import timedelta
from http import HTTPStatus
from ipaddress import ip_network
from unittest.mock import Mock, patch

from aiohttp import BasicAuth, web
from aiohttp.web_exceptions import HTTPUnauthorized
import jwt
import pytest
import yarl

from homeassistant.auth.const import GROUP_ID_READ_ONLY
from homeassistant.auth.models import User
from homeassistant.auth.providers import trusted_networks
from homeassistant.components import websocket_api
from homeassistant.components.http.auth import (
    CONTENT_USER_NAME,
    DATA_SIGN_SECRET,
    SIGN_QUERY_PARAM,
    STORAGE_KEY,
    async_setup_auth,
    async_sign_path,
    async_user_not_allowed_do_auth,
)
from homeassistant.components.http.const import KEY_AUTHENTICATED
from homeassistant.components.http.forwarded import async_setup_forwarded
from homeassistant.components.http.request_context import (
    current_request,
    setup_request_context,
)
from homeassistant.core import callback
from homeassistant.setup import async_setup_component

from . import HTTP_HEADER_HA_AUTH, mock_real_ip

API_PASSWORD = "test-password"

# Don't add 127.0.0.1/::1 as trusted, as it may interfere with other test cases
TRUSTED_NETWORKS = [
    ip_network("192.0.2.0/24"),
    ip_network("2001:DB8:ABCD::/48"),
    ip_network("100.64.0.1"),
    ip_network("FD01:DB8::1"),
]
TRUSTED_ADDRESSES = ["100.64.0.1", "192.0.2.100", "FD01:DB8::1", "2001:DB8:ABCD::1"]
EXTERNAL_ADDRESSES = ["198.51.100.1", "2001:DB8:FA1::1"]
UNTRUSTED_ADDRESSES = [*EXTERNAL_ADDRESSES, "127.0.0.1", "::1"]


async def mock_handler(request):
    """Return if request was authenticated."""
    if not request[KEY_AUTHENTICATED]:
        raise HTTPUnauthorized

    user = request.get("hass_user")
    user_id = user.id if user else None

    return web.json_response(data={"user_id": user_id})


async def get_legacy_user(auth):
    """Get the user in legacy_api_password auth provider."""
    provider = auth.get_auth_provider("legacy_api_password", None)
    return await auth.async_get_or_create_user(
        await provider.async_get_or_create_credentials({})
    )


@pytest.fixture
def app(hass):
    """Fixture to set up a web.Application."""
    app = web.Application()
    app["hass"] = hass
    app.router.add_get("/", mock_handler)
    async_setup_forwarded(app, True, [])
    return app


@pytest.fixture
def app2(hass):
    """Fixture to set up a web.Application without real_ip middleware."""
    app = web.Application()
    app["hass"] = hass
    app.router.add_get("/", mock_handler)
    return app


@pytest.fixture
def trusted_networks_auth(hass):
    """Load trusted networks auth provider."""
    prv = trusted_networks.TrustedNetworksAuthProvider(
        hass,
        hass.auth._store,
        {"type": "trusted_networks", "trusted_networks": TRUSTED_NETWORKS},
    )
    hass.auth._providers[(prv.type, prv.id)] = prv
    return prv


async def test_auth_middleware_loaded_by_default(hass):
    """Test accessing to server from banned IP when feature is off."""
    with patch("homeassistant.components.http.async_setup_auth") as mock_setup:
        await async_setup_component(hass, "http", {"http": {}})

    assert len(mock_setup.mock_calls) == 1


async def test_cant_access_with_password_in_header(
    app, aiohttp_client, legacy_auth, hass
):
    """Test access with password in header."""
    await async_setup_auth(hass, app)
    client = await aiohttp_client(app)

    req = await client.get("/", headers={HTTP_HEADER_HA_AUTH: API_PASSWORD})
    assert req.status == HTTPStatus.UNAUTHORIZED

    req = await client.get("/", headers={HTTP_HEADER_HA_AUTH: "wrong-pass"})
    assert req.status == HTTPStatus.UNAUTHORIZED


async def test_cant_access_with_password_in_query(
    app, aiohttp_client, legacy_auth, hass
):
    """Test access with password in URL."""
    await async_setup_auth(hass, app)
    client = await aiohttp_client(app)

    resp = await client.get("/", params={"api_password": API_PASSWORD})
    assert resp.status == HTTPStatus.UNAUTHORIZED

    resp = await client.get("/")
    assert resp.status == HTTPStatus.UNAUTHORIZED

    resp = await client.get("/", params={"api_password": "wrong-password"})
    assert resp.status == HTTPStatus.UNAUTHORIZED


async def test_basic_auth_does_not_work(app, aiohttp_client, hass, legacy_auth):
    """Test access with basic authentication."""
    await async_setup_auth(hass, app)
    client = await aiohttp_client(app)

    req = await client.get("/", auth=BasicAuth("homeassistant", API_PASSWORD))
    assert req.status == HTTPStatus.UNAUTHORIZED

    req = await client.get("/", auth=BasicAuth("wrong_username", API_PASSWORD))
    assert req.status == HTTPStatus.UNAUTHORIZED

    req = await client.get("/", auth=BasicAuth("homeassistant", "wrong password"))
    assert req.status == HTTPStatus.UNAUTHORIZED

    req = await client.get("/", headers={"authorization": "NotBasic abcdefg"})
    assert req.status == HTTPStatus.UNAUTHORIZED


async def test_cannot_access_with_trusted_ip(
    hass, app2, trusted_networks_auth, aiohttp_client, hass_owner_user
):
    """Test access with an untrusted ip address."""
    await async_setup_auth(hass, app2)

    set_mock_ip = mock_real_ip(app2)
    client = await aiohttp_client(app2)

    for remote_addr in UNTRUSTED_ADDRESSES:
        set_mock_ip(remote_addr)
        resp = await client.get("/")
        assert (
            resp.status == HTTPStatus.UNAUTHORIZED
        ), f"{remote_addr} shouldn't be trusted"

    for remote_addr in TRUSTED_ADDRESSES:
        set_mock_ip(remote_addr)
        resp = await client.get("/")
        assert (
            resp.status == HTTPStatus.UNAUTHORIZED
        ), f"{remote_addr} shouldn't be trusted"


async def test_auth_active_access_with_access_token_in_header(
    hass, app, aiohttp_client, hass_access_token
):
    """Test access with access token in header."""
    token = hass_access_token
    await async_setup_auth(hass, app)
    client = await aiohttp_client(app)
    refresh_token = await hass.auth.async_validate_access_token(hass_access_token)

    req = await client.get("/", headers={"Authorization": f"Bearer {token}"})
    assert req.status == HTTPStatus.OK
    assert await req.json() == {"user_id": refresh_token.user.id}

    req = await client.get("/", headers={"AUTHORIZATION": f"Bearer {token}"})
    assert req.status == HTTPStatus.OK
    assert await req.json() == {"user_id": refresh_token.user.id}

    req = await client.get("/", headers={"authorization": f"Bearer {token}"})
    assert req.status == HTTPStatus.OK
    assert await req.json() == {"user_id": refresh_token.user.id}

    req = await client.get("/", headers={"Authorization": token})
    assert req.status == HTTPStatus.UNAUTHORIZED

    req = await client.get("/", headers={"Authorization": f"BEARER {token}"})
    assert req.status == HTTPStatus.UNAUTHORIZED

    refresh_token = await hass.auth.async_validate_access_token(hass_access_token)
    refresh_token.user.is_active = False
    req = await client.get("/", headers={"Authorization": f"Bearer {token}"})
    assert req.status == HTTPStatus.UNAUTHORIZED


async def test_auth_active_access_with_trusted_ip(
    hass, app2, trusted_networks_auth, aiohttp_client, hass_owner_user
):
    """Test access with an untrusted ip address."""
    await async_setup_auth(hass, app2)

    set_mock_ip = mock_real_ip(app2)
    client = await aiohttp_client(app2)

    for remote_addr in UNTRUSTED_ADDRESSES:
        set_mock_ip(remote_addr)
        resp = await client.get("/")
        assert (
            resp.status == HTTPStatus.UNAUTHORIZED
        ), f"{remote_addr} shouldn't be trusted"

    for remote_addr in TRUSTED_ADDRESSES:
        set_mock_ip(remote_addr)
        resp = await client.get("/")
        assert (
            resp.status == HTTPStatus.UNAUTHORIZED
        ), f"{remote_addr} shouldn't be trusted"


async def test_auth_legacy_support_api_password_cannot_access(
    app, aiohttp_client, legacy_auth, hass
):
    """Test access using api_password if auth.support_legacy."""
    await async_setup_auth(hass, app)
    client = await aiohttp_client(app)

    req = await client.get("/", headers={HTTP_HEADER_HA_AUTH: API_PASSWORD})
    assert req.status == HTTPStatus.UNAUTHORIZED

    resp = await client.get("/", params={"api_password": API_PASSWORD})
    assert resp.status == HTTPStatus.UNAUTHORIZED

    req = await client.get("/", auth=BasicAuth("homeassistant", API_PASSWORD))
    assert req.status == HTTPStatus.UNAUTHORIZED


async def test_auth_access_signed_path_with_refresh_token(
    hass, app, aiohttp_client, hass_access_token
):
    """Test access with signed url."""
    app.router.add_post("/", mock_handler)
    app.router.add_get("/another_path", mock_handler)
    await async_setup_auth(hass, app)
    client = await aiohttp_client(app)

    refresh_token = await hass.auth.async_validate_access_token(hass_access_token)

    signed_path = async_sign_path(
        hass, "/", timedelta(seconds=5), refresh_token_id=refresh_token.id
    )

    req = await client.get(signed_path)
    assert req.status == HTTPStatus.OK
    data = await req.json()
    assert data["user_id"] == refresh_token.user.id

    # Use signature on other path
    req = await client.get("/another_path?{}".format(signed_path.split("?")[1]))
    assert req.status == HTTPStatus.UNAUTHORIZED

    # We only allow GET
    req = await client.post(signed_path)
    assert req.status == HTTPStatus.UNAUTHORIZED

    # Never valid as expired in the past.
    expired_signed_path = async_sign_path(
        hass, "/", timedelta(seconds=-5), refresh_token_id=refresh_token.id
    )

    req = await client.get(expired_signed_path)
    assert req.status == HTTPStatus.UNAUTHORIZED

    # refresh token gone should also invalidate signature
    await hass.auth.async_remove_refresh_token(refresh_token)
    req = await client.get(signed_path)
    assert req.status == HTTPStatus.UNAUTHORIZED


async def test_auth_access_signed_path_with_query_param(
    hass, app, aiohttp_client, hass_access_token
):
    """Test access with signed url and query params."""
    app.router.add_post("/", mock_handler)
    app.router.add_get("/another_path", mock_handler)
    await async_setup_auth(hass, app)
    client = await aiohttp_client(app)

    refresh_token = await hass.auth.async_validate_access_token(hass_access_token)

    signed_path = async_sign_path(
        hass, "/?test=test", timedelta(seconds=5), refresh_token_id=refresh_token.id
    )

    req = await client.get(signed_path)
    assert req.status == HTTPStatus.OK
    data = await req.json()
    assert data["user_id"] == refresh_token.user.id


async def test_auth_access_signed_path_with_query_param_order(
    hass, app, aiohttp_client, hass_access_token
):
    """Test access with signed url and query params different order."""
    app.router.add_post("/", mock_handler)
    app.router.add_get("/another_path", mock_handler)
    await async_setup_auth(hass, app)
    client = await aiohttp_client(app)

    refresh_token = await hass.auth.async_validate_access_token(hass_access_token)

    signed_path = async_sign_path(
        hass,
        "/?test=test&foo=bar",
        timedelta(seconds=5),
        refresh_token_id=refresh_token.id,
    )
    url = yarl.URL(signed_path)
    signed_path = f"{url.path}?{SIGN_QUERY_PARAM}={url.query.get(SIGN_QUERY_PARAM)}&foo=bar&test=test"

    req = await client.get(signed_path)
    assert req.status == HTTPStatus.OK
    data = await req.json()
    assert data["user_id"] == refresh_token.user.id


@pytest.mark.parametrize(
    "base_url,test_url",
    [
        ("/?test=test", "/?test=test&foo=bar"),
        ("/", "/?test=test"),
        ("/?test=test&foo=bar", "/?test=test&foo=baz"),
        ("/?test=test&foo=bar", "/?test=test"),
    ],
)
async def test_auth_access_signed_path_with_query_param_tamper(
    hass, app, aiohttp_client, hass_access_token, base_url: str, test_url: str
):
    """Test access with signed url and query params that have been tampered with."""
    app.router.add_post("/", mock_handler)
    app.router.add_get("/another_path", mock_handler)
    await async_setup_auth(hass, app)
    client = await aiohttp_client(app)

    refresh_token = await hass.auth.async_validate_access_token(hass_access_token)

    signed_path = async_sign_path(
        hass, base_url, timedelta(seconds=5), refresh_token_id=refresh_token.id
    )
    url = yarl.URL(signed_path)
    token = url.query.get(SIGN_QUERY_PARAM)

    req = await client.get(f"{test_url}&{SIGN_QUERY_PARAM}={token}")
    assert req.status == HTTPStatus.UNAUTHORIZED


async def test_auth_access_signed_path_via_websocket(
    hass, app, hass_ws_client, hass_read_only_access_token
):
    """Test signed url via websockets uses connection user."""

    @websocket_api.websocket_command({"type": "diagnostics/list"})
    @callback
    def get_signed_path(hass, connection, msg):
        connection.send_result(
            msg["id"], {"path": async_sign_path(hass, "/", timedelta(seconds=5))}
        )

    websocket_api.async_register_command(hass, get_signed_path)

    # We use hass_read_only_access_token to make sure the connection WS is used.
    client = await hass_ws_client(access_token=hass_read_only_access_token)

    await client.send_json({"id": 5, "type": "diagnostics/list"})

    msg = await client.receive_json()

    assert msg["id"] == 5
    assert msg["success"]

    refresh_token = await hass.auth.async_validate_access_token(
        hass_read_only_access_token
    )
    signature = yarl.URL(msg["result"]["path"]).query["authSig"]
    claims = jwt.decode(
        signature,
        hass.data[DATA_SIGN_SECRET],
        algorithms=["HS256"],
        options={"verify_signature": False},
    )
    assert claims["iss"] == refresh_token.id


async def test_auth_access_signed_path_with_http(
    hass, app, aiohttp_client, hass_access_token
):
    """Test signed url via HTTP uses HTTP user."""
    setup_request_context(app, current_request)

    async def mock_handler(request):
        """Return signed path."""
        return web.json_response(
            data={"path": async_sign_path(hass, "/", timedelta(seconds=-5))}
        )

    app.router.add_get("/hello", mock_handler)
    await async_setup_auth(hass, app)
    client = await aiohttp_client(app)

    refresh_token = await hass.auth.async_validate_access_token(hass_access_token)

    req = await client.get(
        "/hello", headers={"Authorization": f"Bearer {hass_access_token}"}
    )
    assert req.status == HTTPStatus.OK
    data = await req.json()
    signature = yarl.URL(data["path"]).query["authSig"]
    claims = jwt.decode(
        signature,
        hass.data[DATA_SIGN_SECRET],
        algorithms=["HS256"],
        options={"verify_signature": False},
    )
    assert claims["iss"] == refresh_token.id


async def test_auth_access_signed_path_with_content_user(hass, app, aiohttp_client):
    """Test access signed url uses content user."""
    await async_setup_auth(hass, app)
    signed_path = async_sign_path(hass, "/", timedelta(seconds=5))
    signature = yarl.URL(signed_path).query["authSig"]
    claims = jwt.decode(
        signature,
        hass.data[DATA_SIGN_SECRET],
        algorithms=["HS256"],
        options={"verify_signature": False},
    )
    assert claims["iss"] == hass.data[STORAGE_KEY]


async def test_local_only_user_rejected(hass, app, aiohttp_client, hass_access_token):
    """Test access with access token in header."""
    token = hass_access_token
    await async_setup_auth(hass, app)
    set_mock_ip = mock_real_ip(app)
    client = await aiohttp_client(app)
    refresh_token = await hass.auth.async_validate_access_token(hass_access_token)

    req = await client.get("/", headers={"Authorization": f"Bearer {token}"})
    assert req.status == HTTPStatus.OK
    assert await req.json() == {"user_id": refresh_token.user.id}

    refresh_token.user.local_only = True

    for remote_addr in EXTERNAL_ADDRESSES:
        set_mock_ip(remote_addr)
        req = await client.get("/", headers={"Authorization": f"Bearer {token}"})
        assert req.status == HTTPStatus.UNAUTHORIZED


async def test_async_user_not_allowed_do_auth(hass, app):
    """Test for not allowing auth."""
    user = await hass.auth.async_create_user("Hello")
    user.is_active = False

    # User not active
    assert async_user_not_allowed_do_auth(hass, user) == "User is not active"

    user.is_active = True
    user.local_only = True

    # No current request
    assert (
        async_user_not_allowed_do_auth(hass, user)
        == "No request available to validate local access"
    )

    trusted_request = Mock(remote="192.168.1.123")
    untrusted_request = Mock(remote=UNTRUSTED_ADDRESSES[0])

    # Is Remote IP and local only (cloud not loaded)
    assert async_user_not_allowed_do_auth(hass, user, trusted_request) is None
    assert (
        async_user_not_allowed_do_auth(hass, user, untrusted_request)
        == "User cannot authenticate remotely"
    )

    # Mimic cloud loaded and validate local IP again
    hass.config.components.add("cloud")
    assert async_user_not_allowed_do_auth(hass, user, trusted_request) is None
    assert (
        async_user_not_allowed_do_auth(hass, user, untrusted_request)
        == "User cannot authenticate remotely"
    )

    # Is Cloud request and local only, even a local IP will fail
    with patch(
        "hass_nabucasa.remote.is_cloud_request", Mock(get=Mock(return_value=True))
    ):
        assert (
            async_user_not_allowed_do_auth(hass, user, trusted_request)
            == "User is local only"
        )


async def test_create_user_once(hass):
    """Test that we reuse the user."""
    cur_users = len(await hass.auth.async_get_users())
    app = web.Application()
    await async_setup_auth(hass, app)
    users = await hass.auth.async_get_users()
    assert len(users) == cur_users + 1

    user: User = next((user for user in users if user.name == CONTENT_USER_NAME), None)
    assert user is not None, users

    assert len(user.groups) == 1
    assert user.groups[0].id == GROUP_ID_READ_ONLY
    assert len(user.refresh_tokens) == 1
    assert user.system_generated

    await async_setup_auth(hass, app)

    # test it did not create a user
    assert len(await hass.auth.async_get_users()) == cur_users + 1
