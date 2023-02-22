"""Test fixtures for mqtt component."""
from collections.abc import Generator

import pytest

from tests.components.blueprint.conftest import stub_blueprint_populate  # noqa: F401
from tests.components.light.conftest import mock_light_profiles  # noqa: F401


@pytest.fixture(autouse=True)
def patch_hass_config(mock_hass_config: None) -> Generator[None, None, None]:
    """Patch configuration.yaml."""
    return
