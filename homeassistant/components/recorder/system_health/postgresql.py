"""Provide info to system health for postgresql."""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm.session import Session


def db_size_bytes(session: Session, database_name: str) -> float:
    """Get the mysql database size."""
    return float(
        session.execute(
            text("select pg_database_size(:database_name);"),
            {"database_name": database_name},
        ).first()[0]
    )
