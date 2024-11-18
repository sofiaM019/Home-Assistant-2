"""Tests for GPM manager."""

from pathlib import Path
from unittest.mock import patch

import pytest

from homeassistant.components.gpm._manager import (
    NotClonedError,
    RepositoryManager,
    UpdateStrategy,
)


async def test_is_cloned(manager: RepositoryManager) -> None:
    """Test is_cloned method."""
    with patch.object(Path, "exists", return_value=True):
        assert await manager.is_cloned() is True

    with patch.object(Path, "exists", return_value=False):
        assert await manager.is_cloned() is False

    with patch.object(Path, "exists", side_effect=OSError):
        assert await manager.is_cloned() is False


async def test_not_ensure_cloned(manager: RepositoryManager) -> None:
    """Test ensure_cloned decorator raises error when repository is not cloned."""
    manager.is_cloned.return_value = False
    with pytest.raises(NotClonedError):
        await manager.get_current_version()


@pytest.mark.parametrize(
    ("repo_url", "unique_id"),
    [
        ("https://github.com/user/foo.git", "github_com.user.foo"),
        ("https://github.com/another-user/bar", "github_com.another_user.bar"),
        (
            "https://gitlab.com/YETanotherUser123/baz/",
            "gitlab_com.yetanotheruser123.baz",
        ),
        ("http://user:pass@example.com:1234/abc/", "example_com.abc"),
    ],
)
def test_unique_id(manager: RepositoryManager, repo_url: str, unique_id: str) -> None:
    """Test generating of unique_id for given repo_url."""
    manager.repo_url = repo_url
    assert manager.unique_id == unique_id


async def test_update_strategy_tag(manager: RepositoryManager) -> None:
    """Test failed update installation."""
    manager.update_strategy = UpdateStrategy.LATEST_TAG
    await manager.install()
    assert await manager.get_current_version() == "v1.0.0"


async def test_update_strategy_unstable_tag(manager: RepositoryManager) -> None:
    """Test failed update installation."""
    manager.update_strategy = UpdateStrategy.LATEST_UNSTABLE_TAG
    await manager.install()
    assert await manager.get_current_version() == "v2.0.0beta2"


async def test_update_strategy_commit(manager: RepositoryManager) -> None:
    """Test failed update installation."""
    manager.update_strategy = UpdateStrategy.LATEST_COMMIT
    await manager.install()
    assert len(await manager.get_current_version()) == 40
