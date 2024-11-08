"""Trigger entity."""

from __future__ import annotations

from homeassistant.core import Context, HomeAssistant, callback
from homeassistant.helpers.script import Script, _VarsType
from homeassistant.helpers.template import TemplateStateFromEntityId
from homeassistant.helpers.trigger_template_entity import TriggerBaseEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import TriggerUpdateCoordinator


class TriggerEntity(  # pylint: disable=hass-enforce-class-module
    TriggerBaseEntity, CoordinatorEntity[TriggerUpdateCoordinator]
):
    """Template entity based on trigger data."""

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: TriggerUpdateCoordinator,
        config: dict,
    ) -> None:
        """Initialize the entity."""
        CoordinatorEntity.__init__(self, coordinator)
        TriggerBaseEntity.__init__(self, hass, config)

    async def async_added_to_hass(self) -> None:
        """Handle being added to Home Assistant."""
        await super().async_added_to_hass()
        if self.coordinator.data is not None:
            self._process_data()

    def _set_unique_id(self, unique_id: str | None) -> None:
        """Set unique id."""
        if unique_id and self.coordinator.unique_id:
            self._unique_id = f"{self.coordinator.unique_id}-{unique_id}"
        else:
            self._unique_id = unique_id

    @callback
    def _process_data(self) -> None:
        """Process new data."""

        this = None
        if state := self.hass.states.get(self.entity_id):
            this = state.as_dict()
        run_variables = self.coordinator.data["run_variables"]
        variables = {"this": this, **(run_variables or {})}

        self._render_templates(variables)

        self.async_set_context(self.coordinator.data["context"])

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._process_data()
        self.async_write_ha_state()

    async def async_run_script(
        self,
        script: Script,
        *,
        run_variables: _VarsType | None = None,
        context: Context | None = None,
    ) -> None:
        """Run an action script."""
        if run_variables is None:
            run_variables = {}
        await script.async_run(
            run_variables={
                "this": TemplateStateFromEntityId(self.hass, self.entity_id),
                **run_variables,
            },
            context=context,
        )
