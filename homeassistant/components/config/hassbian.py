"""Component to interact with Hassbian tools."""
import asyncio
import json
import os

from aiohttp import web

from homeassistant.components.http import HomeAssistantView


SAMPLE_OUTPUT = """
{
  "suites": [
    {
      "openzwave": [
        {
          "state": "installed"
        },
        {
          "description": "This is the description of the Open Z-Wave suite."
        }
      ]
    },
    {
      "openelec": [
        {
          "state": "not_installed"
        },
        {
          "description":
          "OpenElec is amazing. It allows you to control the TV."
        }
      ]
    },
    {
      "mosquitto": [
        {
          "state": "installing"
        },
        {
          "description":
          "Mosquitto is an MQTT broker."
        }
      ]
    }
  ]
}
"""


@asyncio.coroutine
def async_setup(hass):
    """Setup the hassbian config."""
    # TODO: Test if is hassbian
    is_hassbian = 'FORCE_HASSBIAN' in os.environ

    if not is_hassbian:
        return

    hass.http.register_view(HassbianSuitesView)
    hass.http.register_view(HassbianSuiteInstallView)


@asyncio.coroutine
def hassbian_status(hass):
    """Query for the Hassbian status."""
    # TODO: fetch real output
    cmd = ['echo', SAMPLE_OUTPUT]
    tool = yield from asyncio.create_subprocess_exec(
        *cmd,
        loop=hass.loop,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL
    )

    stdout, _ = yield from tool.communicate()

    try:
        return json.loads(str(stdout, 'utf-8'))
    except ValueError:
        return web.Response(status=400)


class HassbianSuitesView(HomeAssistantView):
    """Hassbian packages endpoint."""

    url = '/api/hassbian/suites'
    name = 'api:hassbian:suites'

    @asyncio.coroutine
    def get(self, request):
        """Request suite status."""
        inp = yield from hassbian_status(request.app['hass'])

        # Flatten the structure a bit
        suites = {}

        for suite in inp['suites']:
            key = next(iter(suite))
            info = suites[key] = {}

            for item in suite[key]:
                item_key = next(iter(item))
                info[item_key] = item[item_key]

        return self.json(suites)


class HassbianSuiteInstallView(HomeAssistantView):
    """Hassbian packages endpoint."""

    url = '/api/hassbian/suites/{suite}/install'
    name = 'api:hassbian:suite'

    @asyncio.coroutine
    def post(self, request, suite):
        """Request suite status."""
        # TODO
        return self.json({"status": "ok"})
