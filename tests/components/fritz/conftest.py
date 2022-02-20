"""Common stuff for AVM Fritz!Box tests."""
from unittest.mock import patch

from fritzconnection.core.processor import Service
from fritzconnection.lib.fritzhosts import FritzHosts
import pytest

from .const import MOCK_FB_SERVICES, MOCK_MESH_DATA


class FritzServiceMock(Service):
    """Service mocking."""

    def __init__(self, serviceId: str, actions: dict) -> None:
        """Init Service mock."""
        super().__init__()
        self._actions = actions
        self.serviceId = serviceId


class FritzConnectionMock:  # pylint: disable=too-few-public-methods
    """FritzConnection mocking."""

    MODELNAME = "FRITZ!Box 7490"

    def __init__(self, services):
        """Inint Mocking class."""
        self.modelname = self.MODELNAME
        self.call_action = self._call_action
        self._services = services
        self.services = {
            srv: FritzServiceMock(serviceId=srv, actions=actions)
            for srv, actions in services.items()
        }

    def _call_action(self, service: str, action: str, **kwargs):
        if ":" in service:
            service, number = service.split(":", 1)
            service = service + number
        elif not service[-1].isnumeric():
            service = service + "1"

        if kwargs:

            if (index := kwargs.get("NewIndex")) is None:
                index = next(iter(kwargs.values()))

            return self._services[service][action][index]
        return self._services[service][action]


class FritzHostMock(FritzHosts):
    """FritzHosts mocking."""

    def get_mesh_topology(self, raw=False):
        """Retrurn mocked mesh data."""
        return MOCK_MESH_DATA


@pytest.fixture()
def fc_class_mock():
    """Fixture that sets up a mocked FritzConnection class."""
    with patch("fritzconnection.FritzConnection", autospec=True) as result:
        result.return_value = FritzConnectionMock(MOCK_FB_SERVICES)
        yield result


@pytest.fixture()
def fh_class_mock():
    """Fixture that sets up a mocked FritzHosts class."""
    with patch("fritzconnection.lib.fritzhosts.FritzHosts", autospec=True) as result:
        result.return_value = FritzHostMock
        yield result
