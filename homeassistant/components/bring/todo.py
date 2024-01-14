"""Todo platform for the Bring! integration."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import TYPE_CHECKING

from python_bring_api.exceptions import BringRequestException
from python_bring_api.types import BringList

from homeassistant import config_entries, core
from homeassistant.components.todo import (
    TodoItem,
    TodoItemStatus,
    TodoListEntity,
    TodoListEntityFeature,
)
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import BringDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=90)


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor from a config entry created in the integrations UI."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    unique_id = config_entry.unique_id

    if TYPE_CHECKING:
        assert unique_id

    for _list in coordinator.data:
        async_add_entities(
            [
                BringTodoListEntity(
                    coordinator,
                    name=f"Bring! {_list['name']}",
                    unique_id=f"{unique_id} {_list['listUuid']}",
                )
            ],
        )


class BringTodoListEntity(
    CoordinatorEntity[BringDataUpdateCoordinator], TodoListEntity
):
    """A To-do List representation of the Bring! Shopping List."""

    _attr_has_entity_name = True
    _attr_supported_features = (
        TodoListEntityFeature.CREATE_TODO_ITEM
        | TodoListEntityFeature.UPDATE_TODO_ITEM
        | TodoListEntityFeature.DELETE_TODO_ITEM
        | TodoListEntityFeature.SET_DESCRIPTION_ON_ITEM
    )
    _attr_should_poll = False

    def __init__(
        self,
        coordinator: BringDataUpdateCoordinator,
        name: str,
        unique_id: str,
    ) -> None:
        """Initialize BringTodoListEntity."""
        super().__init__(coordinator)
        self._attr_icon = "mdi:cart"
        self._attr_name = name
        self._attr_unique_id = unique_id

    async def async_added_to_hass(self) -> None:
        """Populate the todo list at start."""
        self._populate_list()
        await super().async_added_to_hass()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle the state update and prepare the todo list items."""
        self._populate_list()
        return super()._handle_coordinator_update()

    @property
    def list_(self) -> BringList | None:
        """Return the bring list."""
        return next(
            (
                _list
                for _list in self.coordinator.data
                if _list["listUuid"] == self.unique_id
            ),
            None,
        )

    def _populate_list(self) -> None:
        """Populate the todo list using the coordinator data."""

        _list = self.list_
        if _list is not None:
            self._attr_todo_items = [
                TodoItem(
                    uid=item["name"],
                    summary=item["name"],
                    description=item["specification"] or "",
                    status=TodoItemStatus.NEEDS_ACTION,
                )
                for item in _list["items"]
            ]
        else:
            self._attr_todo_items = None

    async def async_create_todo_item(self, item: TodoItem) -> None:
        """Add an item to the To-do list."""
        try:

            def _sync():
                return self.coordinator.bring.saveItem(
                    self.unique_id, item.summary, item.description or ""
                )

            await self.hass.async_add_executor_job(_sync)
        except BringRequestException as e:
            _LOGGER.warning("Unable to save todo item for bring")
            raise HomeAssistantError from e

        await self.async_update_ha_state(force_refresh=True)

    async def async_update_todo_item(self, item: TodoItem) -> None:
        """Update an item to the To-do list.

        Bring has an internal 'recent' list which we want to use instead of a todo list status, therefore completed todo list items will directly be deleted

        This results in following behaviour:

        - Completed items will move to the "completed" section in home assistant todo list and get deleted in bring, which will remove them from the home assistant todo list completely after a short delay
        - Bring items do not have unique identifiers and are using the name/summery/title. Therefore the name is not to be changed! Should a name be changed anyway, a new item will be created instead and no update for this item is performed and on the next cloud pull update, it will get cleared
        """

        if TYPE_CHECKING:
            assert item.uid

        if item.status == TodoItemStatus.COMPLETED:
            await self.async_delete_todo_items([item.uid])

        elif item.summary == item.uid:
            try:

                def _sync():
                    return self.coordinator.bring.updateItem(
                        self.unique_id, item.uid, item.description or ""
                    )

                await self.hass.async_add_executor_job(_sync)
            except BringRequestException as e:
                _LOGGER.warning("Unable to update todo item for bring")
                raise HomeAssistantError from e
        else:
            await self.async_delete_todo_items([item.uid])
            await self.async_create_todo_item(item)

        await self.async_update_ha_state(force_refresh=True)

    async def async_delete_todo_items(self, uids: list[str]) -> None:
        """Delete an item from the To-do list."""
        for uid in uids:
            try:

                def _sync():
                    return self.coordinator.bring.removeItem(self.unique_id, uid)  # noqa: B023

                await self.hass.async_add_executor_job(_sync)
            except BringRequestException as e:
                _LOGGER.warning("Unable to delete todo item for bring")
                raise HomeAssistantError from e

        await self.async_update_ha_state(force_refresh=True)
