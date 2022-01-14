"""Make the component configurable via the UI."""
from __future__ import annotations
import logging
from typing import Any
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components.rki_covid.coordinator import RkiCovidDataUpdateCoordinator


from .const import ATTR_COUNTY, DOMAIN

_LOGGER = logging.getLogger(__name__)


class RKICovidNumbersConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """RKI Covid numbers config flow."""

    VERSION = 1

    _options: dict[str, Any] | None = None

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Invoke when a user initiates a flow via the user interface."""
        _LOGGER.debug(f"User triggered configuration flow: {user_input}")

        errors: dict[str, str] = {}

        if self._options is None:
            self._options = {}

            # add items from coordinator
            coordinator = RkiCovidDataUpdateCoordinator(self.hass)
            await coordinator.async_config_entry_first_refresh()

            _LOGGER.debug(f"Coordinator: {coordinator}")

            for case in sorted(coordinator.data.values(), key=lambda case: case.name):
                if case.county:
                    self._options[case.county] = case.county
                else:
                    self._options[case.name] = case.name

        if user_input is not None:
            await self.async_set_unique_id(user_input[ATTR_COUNTY])
            self._abort_if_unique_id_configured()

            # User is done adding sensors, create the config entry.
            _LOGGER.debug("Create entry from Configuration UI")
            return self.async_create_entry(
                title=self._options[user_input[ATTR_COUNTY]], data=user_input
            )

        # Show user input for adding sensors.
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(ATTR_COUNTY): vol.In(self._options)}),
            errors=errors,
        )
