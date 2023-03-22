"""Events schema repairs."""
from __future__ import annotations

from typing import TYPE_CHECKING

from ...db_schema import EventData, Events
from ..schema import (
    correct_db_schema_precision,
    correct_db_schema_utf8,
    validate_db_schema_precision,
    validate_table_schema_supports_utf8,
)

if TYPE_CHECKING:
    from ... import Recorder

TABLE_UTF8_COLUMNS = {
    EventData: (EventData.shared_data,),
}


def validate_db_schema(instance: Recorder) -> set[str]:
    """Do some basic checks for common schema errors caused by manual migration."""
    schema_errors: set[str] = set()
    schema_errors |= validate_table_schema_supports_utf8(
        instance, EventData, (EventData.shared_data,)
    )
    schema_errors |= validate_db_schema_precision(instance, Events)
    return schema_errors


def correct_db_schema(
    instance: Recorder,
    schema_errors: set[str],
) -> None:
    """Correct issues detected by validate_db_schema."""
    for table in (Events, EventData):
        correct_db_schema_utf8(instance, table, schema_errors)
    correct_db_schema_precision(instance, Events, schema_errors)
