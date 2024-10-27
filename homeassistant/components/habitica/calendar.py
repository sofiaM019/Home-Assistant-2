"""Calendar platform for Habitica integration."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from enum import StrEnum

from homeassistant.components.calendar import (
    CalendarEntity,
    CalendarEntityDescription,
    CalendarEvent,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from . import HabiticaConfigEntry
from .coordinator import HabiticaDataUpdateCoordinator
from .entity import HabiticaBase
from .types import HabiticaTaskType
from .util import build_rrule, get_recurrence_rule


class HabiticaCalendar(StrEnum):
    """Habitica calendars."""

    DAILIES = "dailys"
    TODOS = "todos"


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: HabiticaConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the calendar platform."""
    coordinator = config_entry.runtime_data

    async_add_entities(
        [
            HabiticaTodosCalendarEntity(coordinator),
            HabiticaDailiesCalendarEntity(coordinator),
        ]
    )


class HabiticaCalendarEntity(HabiticaBase, CalendarEntity):
    """Base Habitica calendar entity."""

    def __init__(
        self,
        coordinator: HabiticaDataUpdateCoordinator,
    ) -> None:
        """Initialize calendar entity."""
        super().__init__(coordinator, self.entity_description)


class HabiticaTodosCalendarEntity(HabiticaCalendarEntity):
    """Habitica todos calendar entity."""

    entity_description = CalendarEntityDescription(
        key=HabiticaCalendar.TODOS,
        translation_key=HabiticaCalendar.TODOS,
    )

    def dated_todos(self) -> list[CalendarEvent]:
        """Get all dated todos."""

        return sorted(
            [
                CalendarEvent(
                    start=start,
                    end=start + timedelta(days=1),
                    summary=task["text"],
                    description=task["notes"],
                    uid=task["id"],
                )
                for task in self.coordinator.data.tasks
                if task["type"] == HabiticaTaskType.TODO
                and not task["completed"]
                and task.get("date")
                and (
                    start := dt_util.as_local(
                        datetime.fromisoformat(task["date"])
                    ).date()
                )
            ],
            key=lambda event: (
                event.start,
                self.coordinator.data.user["tasksOrder"]["todos"].index(event.uid),
            ),
        )

    @property
    def event(self) -> CalendarEvent | None:
        """Return the current or next upcoming event."""

        return next(
            (
                e
                for e in self.dated_todos()
                if dt_util.start_of_local_day(e.start)
                <= (now := dt_util.now())
                < dt_util.start_of_local_day(e.end)
                or dt_util.start_of_local_day(e.start) > now
            ),
            None,
        )

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        """Return calendar events within a datetime range."""

        return [
            event
            for event in self.dated_todos()
            if dt_util.start_of_local_day(event.start) < end_date
            and dt_util.start_of_local_day(event.end) > start_date
        ]


class HabiticaDailiesCalendarEntity(HabiticaCalendarEntity):
    """Habitica dailies calendar entity."""

    entity_description = CalendarEntityDescription(
        key=HabiticaCalendar.DAILIES,
        translation_key=HabiticaCalendar.DAILIES,
    )

    @property
    def today(self) -> datetime:
        """Habitica daystart."""
        return dt_util.start_of_local_day(
            datetime.fromisoformat(self.coordinator.data.user["lastCron"])
        )

    def calculate_end_date(self, next_recurrence: datetime) -> date:
        """Calculate the end date for a yesterdaily."""
        return (
            dt_util.start_of_local_day()
            if next_recurrence == self.today
            else next_recurrence
        ).date() + timedelta(days=1)

    @property
    def event(self) -> CalendarEvent | None:
        """Return the next upcoming event."""

        events = [
            CalendarEvent(
                start=next_recurrence.date(),
                end=self.calculate_end_date(next_recurrence),
                summary=task["text"],
                description=task["notes"],
                uid=task["id"],
            )
            for task in self.coordinator.data.tasks
            if task["type"] == HabiticaTaskType.DAILY and task["everyX"]
            if (
                next_recurrence := self.today
                if not task["completed"] and task["isDue"]
                else build_rrule(task).after(self.today, inc=True)
            )
        ]
        events_sorted = sorted(
            events,
            key=lambda event: (
                event.start,
                self.coordinator.data.user["tasksOrder"]["dailys"].index(event.uid),
            ),
        )

        return next(iter(events_sorted), None)

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        """Return calendar events within a datetime range."""

        # returns only todays and future dailies.
        # If a daily is completed it will not be shown for today but still future recurrences
        # If the cron hasn't run, not completed dailies are yesterdailies and displayed yesterday
        return sorted(
            [
                CalendarEvent(
                    start=start,
                    end=start + timedelta(days=1),
                    summary=task["text"],
                    description=task["notes"],
                    uid=task["id"],
                    rrule=get_recurrence_rule(recurrences),
                )
                for task in self.coordinator.data.tasks
                if task["type"] == HabiticaTaskType.DAILY
                and task["everyX"]
                and (recurrences := build_rrule(task))
                for recurrence in recurrences.between(
                    start_date, end_date - timedelta(days=1), inc=True
                )
                # return only future events and due current events
                if (start := recurrence) > self.today
                or (start == self.today and not task["completed"])
            ],
            key=lambda event: (
                event.start,
                self.coordinator.data.user["tasksOrder"]["dailys"].index(event.uid),
            ),
        )

    @property
    def extra_state_attributes(self) -> dict[str, bool | None] | None:
        """Return entity specific state attributes."""
        return {
            "yesterdaily": self.event.start < self.today.date() if self.event else None
        }
