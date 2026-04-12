from __future__ import annotations

from pathlib import Path

from sqlalchemy import text

from .db import engine
from .models import Base


REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_FILES = [
    REPO_ROOT / "sql" / "schema" / "001_raw.sql",
    REPO_ROOT / "sql" / "schema" / "002_analytics.sql",
]


def initialize_database() -> None:
    with engine.begin() as connection:
        raw_connection = connection.connection
        with raw_connection.cursor() as cursor:
            for schema_file in SCHEMA_FILES:
                sql = schema_file.read_text(encoding="utf-8")
                cursor.execute(sql)
        connection.execute(text("CREATE SCHEMA IF NOT EXISTS app"))
    Base.metadata.create_all(bind=engine)
