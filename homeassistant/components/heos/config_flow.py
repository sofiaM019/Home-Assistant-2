"""Config flow to configure Heos."""
from urllib.parse import urlparse

from pyheos import Heos, HeosError
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import ssdp
from homeassistant.const import CONF_HOST
from homeassistant.core import callback

from .const import DATA_DISCOVERED_HOSTS, DOMAIN


def format_title(host: str) -> str:
    """Format the title for config entries."""
    return f"Controller ({host})"


@config_entries.HANDLERS.register(DOMAIN)
class HeosFlowHandler(config_entries.ConfigFlow):
    """Define a flow for HEOS."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    async def async_step_ssdp(self, discovery_info):
        """Handle a discovered Heos device."""
        # Store discovered host
        hostname = urlparse(discovery_info[ssdp.ATTR_SSDP_LOCATION]).hostname
        friendly_name = f"{discovery_info[ssdp.ATTR_UPNP_FRIENDLY_NAME]} ({hostname})"
        self.hass.data.setdefault(DATA_DISCOVERED_HOSTS, {})
        self.hass.data[DATA_DISCOVERED_HOSTS][friendly_name] = hostname
        # Abort if other flows in progress or an entry already exists
        if self._async_in_progress() or self._async_current_entries():
            return self.async_abort(reason="already_setup")
        player_id = await _async_get_player_id(hostname)
        if player_id:
            await self.async_set_unique_id(str(player_id))
        # Show selection form
        return self.async_show_form(step_id="user")

    async def async_step_import(self, user_input=None):
        """Occurs when an entry is setup through config."""
        host = user_input[CONF_HOST]
        player_id = await _async_get_player_id(host)
        if player_id:
            await self.async_set_unique_id(str(player_id))
        return self.async_create_entry(title=format_title(host), data={CONF_HOST: host})

    async def async_step_user(self, user_input=None):
        """Obtain host and validate connection."""
        self.hass.data.setdefault(DATA_DISCOVERED_HOSTS, {})
        # Only a single entry is needed for all devices
        if self._async_current_entries():
            return self.async_abort(reason="already_setup")
        # Try connecting to host if provided
        errors = {}
        host = None
        if user_input is not None:
            host = user_input[CONF_HOST]
            # Map host from friendly name if in discovered hosts
            host = self.hass.data[DATA_DISCOVERED_HOSTS].get(host, host)
            heos = Heos(host)
            players = None
            try:
                await heos.connect()
                players = await heos.get_players()
                self.hass.data.pop(DATA_DISCOVERED_HOSTS)
            except HeosError:
                errors[CONF_HOST] = "connection_failure"
            finally:
                await heos.disconnect()
            if not errors:
                player_id = _async_find_player_id_in_players(players, host)
                if player_id:
                    await self.async_set_unique_id(str(player_id))
                return self.async_create_entry(
                    title=format_title(host), data={CONF_HOST: host}
                )

        # Return form
        host_type = (
            str
            if not self.hass.data[DATA_DISCOVERED_HOSTS]
            else vol.In(list(self.hass.data[DATA_DISCOVERED_HOSTS]))
        )
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_HOST, default=host): host_type}),
            errors=errors,
        )


async def _async_get_player_id(ip_address):
    """Fetch the player id."""
    heos = Heos(ip_address)
    try:
        await heos.connect()
        players = await heos.get_players()
    except HeosError:
        return None
    finally:
        await heos.disconnect()
    return _async_find_player_id_in_players(players, ip_address)


@callback
def _async_find_player_id_in_players(players, ip_address):
    """Look though players to find the player_id for an ip address."""
    if not players:
        return None
    for player_id, player in players.items():
        if player.ip_address == ip_address:
            return player_id
    return None
