"""Config flow for NMBS integration."""

from typing import Any

from pyrail import iRail
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.selector import (
    BooleanSelector,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    CONF_EXCLUDE_VIAS,
    CONF_SHOW_ON_MAP,
    CONF_STATION_FROM,
    CONF_STATION_TO,
    DOMAIN,
)


class NMBSConfigFlow(ConfigFlow, domain=DOMAIN):
    """NMBS config flow."""

    def __init__(self) -> None:
        """Initialize."""
        self.api_client = iRail()
        self.stations: dict[str, Any] | None = None

    async def _fetch_stations_choices(self):
        """Fetch the stations."""

        self.hass.data.setdefault(DOMAIN, {})
        if "stations" not in self.hass.data[DOMAIN]:
            stations = await self.hass.async_add_executor_job(
                self.api_client.get_stations
            )
            self.hass.data[DOMAIN]["stations"] = stations["station"]
        self.stations = self.hass.data[DOMAIN]["stations"]

        return [
            SelectOptionDict(
                value=station["standardname"], label=station["standardname"]
            )
            for station in self.stations
        ]

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the step to setup a connection between 2 stations."""

        errors: dict = {}
        if user_input is not None:
            await self.async_set_unique_id(
                f"{user_input[CONF_STATION_FROM]}-{user_input[CONF_STATION_TO]}"
            )
            self._abort_if_unique_id_configured()

            config_entry_name = f"Train from {user_input[CONF_STATION_FROM]} to {user_input[CONF_STATION_TO]}"
            return self.async_create_entry(
                title=config_entry_name,
                data=user_input,
            )

        choices = await self._fetch_stations_choices()
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_STATION_FROM): SelectSelector(
                        SelectSelectorConfig(
                            options=choices,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Required(CONF_STATION_TO): SelectSelector(
                        SelectSelectorConfig(
                            options=choices,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Optional(CONF_EXCLUDE_VIAS, default=False): BooleanSelector(),
                    vol.Optional(CONF_SHOW_ON_MAP, default=False): BooleanSelector(),
                },
            ),
            errors=errors,
        )

    async def async_step_import(self, user_input: dict[str, Any]) -> ConfigFlowResult:
        """Import configuration from yaml."""
        return await self.async_step_user(user_input)
