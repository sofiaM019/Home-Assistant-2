"""Tests for the GPM update entity."""

import pytest

from homeassistant.components.gpm._manager import (
    IntegrationRepositoryManager,
    RepositoryManager,
    ResourceRepositoryManager,
)
from homeassistant.components.gpm.update import GPMUpdateEntity, UpdateStrategy
from homeassistant.exceptions import HomeAssistantError


async def test_integration_properties(
    integration_manager: IntegrationRepositoryManager,
) -> None:
    """Test properties of integration fetched during async_update."""
    await integration_manager.clone()
    entity = GPMUpdateEntity(integration_manager)
    await entity.async_update()
    assert entity.installed_version == "v0.9.9"
    assert entity.latest_version == "v1.0.0"
    assert entity.name == "awesome_component"
    assert entity.unique_id == "github_com.user.awesome_component"
    assert (
        entity.entity_picture
        == "https://brands.home-assistant.io/_/awesome_component/icon.png"
    )
    assert integration_manager.fetch.await_count == 1


async def test_resource_properties(resource_manager: ResourceRepositoryManager) -> None:
    """Test properties of resource fetched during async_update."""
    entity = GPMUpdateEntity(resource_manager)
    await entity.async_update()
    assert entity.installed_version == "v0.9.9"
    assert entity.latest_version == "v1.0.0"
    assert entity.name == "awesome_card"
    assert entity.unique_id == "github_com.user.awesome_card"
    assert entity.entity_picture is None
    assert resource_manager.fetch.await_count == 1


async def test_versions_substr(manager: RepositoryManager) -> None:
    """Test that GIT commit SHAs are shortened in UI."""
    await manager.clone()
    manager.update_strategy = UpdateStrategy.LATEST_COMMIT
    manager.get_current_version.return_value = (
        "d98061dd815fbf3ead679d9f744328f5217da68a"
    )
    manager.get_latest_version.return_value = "690a323d9a879eff007cc6f7f742293fd9464b20"
    entity = GPMUpdateEntity(manager)
    await entity.async_update()
    assert entity.installed_version == "d98061d"
    assert entity.latest_version == "690a323"


@pytest.mark.parametrize("version", ["0.8.8", "1.0.0", "2.0.0beta5", None])
async def test_install(
    manager: RepositoryManager, version: str | None, request: pytest.FixtureRequest
) -> None:
    """Test update installation."""
    await manager.clone()
    entity = GPMUpdateEntity(manager)
    await entity.async_update()
    await entity.async_install(version=version, backup=False)
    assert manager.checkout.await_count == 1


async def test_install_same_version(manager: RepositoryManager) -> None:
    """Test failed update installation."""
    await manager.clone()
    entity = GPMUpdateEntity(manager)
    await entity.async_update()
    with pytest.raises(HomeAssistantError):
        await entity.async_install(version="v0.9.9", backup=False)
    assert manager.checkout.await_count == 0
