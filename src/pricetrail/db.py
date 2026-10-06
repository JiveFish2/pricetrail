"""Database connection and the SQL migration runner.

Migrations are plain SQL files in `migrations/`, applied in name order and
recorded in `schema_migrations` so each one runs exactly once.
"""

from __future__ import annotations

import os
from pathlib import Path

import psycopg

MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "migrations"


def connect() -> psycopg.Connection:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise SystemExit("DATABASE_URL is not set (see .env.example)")
    return psycopg.connect(url)


def migrate(conn: psycopg.Connection) -> list[str]:
    """Apply pending migrations and return the names of the ones applied."""
    with conn.cursor() as cur:
        cur.execute(
            "create table if not exists schema_migrations ("
            " name text primary key, applied_at timestamptz not null default now())"
        )
        cur.execute("select name from schema_migrations")
        applied = {row[0] for row in cur.fetchall()}

        done: list[str] = []
        for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
            if path.name in applied:
                continue
            cur.execute(path.read_text())
            cur.execute("insert into schema_migrations (name) values (%s)", (path.name,))
            done.append(path.name)
    conn.commit()
    return done
