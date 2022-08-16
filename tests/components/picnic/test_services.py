"""Tests for the Picnic services."""

from unittest.mock import MagicMock, patch

import pytest

from homeassistant.components.picnic import CONF_COUNTRY_CODE, DOMAIN
from homeassistant.components.picnic.const import CONF_API, SERVICE_ADD_PRODUCT_TO_CART
from homeassistant.components.picnic.services import PicnicServiceException
from homeassistant.const import CONF_ACCESS_TOKEN
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry


@pytest.fixture
def picnic_api_client():
    """Create PicnicAPI mock with set response data."""
    with patch(
        "homeassistant.components.picnic.create_picnic_client"
    ) as create_picnic_client_mock:

        def picnic_api_generator(entry: MockConfigEntry):
            auth_token = "af3wh738j3fa28l9fa23lhiufahu7l"
            auth_data = {
                "user_id": entry.unique_id,
                "address": {
                    "street": "Teststreet",
                    "house_number": 123,
                    "house_number_ext": "b",
                },
            }
            picnic_mock = MagicMock()
            picnic_mock.session.auth_token = auth_token
            picnic_mock.get_user.return_value = auth_data

            return picnic_mock

        create_picnic_client_mock.side_effect = picnic_api_generator

        yield create_picnic_client_mock


@pytest.fixture
def generate_config_entry(hass: HomeAssistant, picnic_api_client):
    """Generate Picnic config entries."""

    async def config_entry_generator(unique_id="295-6y3-1nf4"):
        # Create/setup a config entry
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_ACCESS_TOKEN: "x-original-picnic-auth-token",
                CONF_COUNTRY_CODE: "NL",
            },
            unique_id=unique_id,
        )
        config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        return config_entry

    return config_entry_generator


def _get_picnic_api_mock(hass: HomeAssistant, entry: MockConfigEntry):
    """Return the Picnic api client from the HASS data for the config entry."""
    return hass.data[DOMAIN][entry.entry_id][CONF_API]


async def test_add_product_using_id(hass: HomeAssistant, generate_config_entry):
    """Test adding a product by id."""
    config_entry = await generate_config_entry()
    picnic_api = _get_picnic_api_mock(hass, config_entry)

    # Call the add_product service
    await hass.services.async_call(
        DOMAIN,
        SERVICE_ADD_PRODUCT_TO_CART,
        {"product_id": "5109348572", "amount": 3},
        blocking=True,
    )

    # Check that the right method is called on the api
    picnic_api.add_product.assert_called_with("5109348572", 3)


async def test_add_product_using_name(hass: HomeAssistant, generate_config_entry):
    """Test adding a product by name."""
    config_entry = await generate_config_entry()
    picnic_api = _get_picnic_api_mock(hass, config_entry)

    # Set the return value of the search api endpoint
    picnic_api.search.return_value = [
        {
            "items": [
                {
                    "id": "2525404",
                    "name": "Best tea",
                    "display_price": 321,
                    "unit_quantity": "big bags",
                },
                {
                    "id": "2525500",
                    "name": "Cheap tea",
                    "display_price": 100,
                    "unit_quantity": "small bags",
                },
            ]
        }
    ]

    # Call the add_product service
    await hass.services.async_call(
        DOMAIN,
        SERVICE_ADD_PRODUCT_TO_CART,
        {"product_name": "Tea"},
        blocking=True,
    )

    # Check that the right method is called on the api
    picnic_api.add_product.assert_called_with("2525404", 1)


async def test_add_product_using_name_no_results(
    hass: HomeAssistant, generate_config_entry
):
    """Test adding a product by name that can't be found."""
    config_entry = await generate_config_entry()
    picnic_api = _get_picnic_api_mock(hass, config_entry)

    # Set the return value of the search api endpoint
    picnic_api.search.return_value = []

    # Call the add_product service
    with pytest.raises(PicnicServiceException):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_ADD_PRODUCT_TO_CART,
            {"product_name": "Random non existing product"},
            blocking=True,
        )


async def test_add_product_multiple_config_entries(
    hass: HomeAssistant, generate_config_entry
):
    """Test adding a product for a specific Picnic service while multiple are configured."""
    config_entry_1 = await generate_config_entry("158g-ahf7-aks")
    config_entry_2 = await generate_config_entry("3fj9-9gju-236")

    device_registry = hass.helpers.device_registry.async_get(hass)
    picnic_service = device_registry.async_get_device(
        identifiers={(DOMAIN, "3fj9-9gju-236")}
    )

    # Call the add_product service
    await hass.services.async_call(
        DOMAIN,
        SERVICE_ADD_PRODUCT_TO_CART,
        {"product_id": "5109348572", "device_id": picnic_service.id},
        blocking=True,
    )

    # Check that the right method is called on the api
    _get_picnic_api_mock(hass, config_entry_1).add_product.assert_not_called()
    _get_picnic_api_mock(hass, config_entry_2).add_product.assert_called_with(
        "5109348572", 1
    )


async def test_add_product_config_entry_doesnt_exist(
    hass: HomeAssistant, generate_config_entry
):
    """Test adding a product for a specific Picnic service, which doesn't exist."""
    config_entry = await generate_config_entry("158g-ahf7-aks")

    with pytest.raises(PicnicServiceException):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_ADD_PRODUCT_TO_CART,
            {"product_id": "5109348572", "device_id": 12345},
            blocking=True,
        )

    # Check that the right method is called on the api
    _get_picnic_api_mock(hass, config_entry).add_product.assert_not_called()


async def test_add_product_config_entry_malformed(
    hass: HomeAssistant, generate_config_entry
):
    """Test adding a product for a specific Picnic service, which has no data set."""
    config_entry = await generate_config_entry("158g-ahf7-aks")
    device_registry = hass.helpers.device_registry.async_get(hass)
    picnic_service = device_registry.async_get_device(
        identifiers={(DOMAIN, config_entry.unique_id)}
    )

    hass.data[DOMAIN][config_entry.entry_id] = {}

    with pytest.raises(PicnicServiceException):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_ADD_PRODUCT_TO_CART,
            {"product_id": "5109348572", "device_id": picnic_service.id},
            blocking=True,
        )
