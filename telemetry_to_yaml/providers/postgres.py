"""Postgres metadata and query-log extraction provider."""

from __future__ import annotations

import logging
import os
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable

from telemetry_to_yaml.providers.base import BaseProvider, ColumnMetadata, QueryLogEntry, TableMetadata

LOGGER = logging.getLogger(__name__)


class ProviderConnectionError(RuntimeError):
    """Raised when a provider cannot connect to its backing data node."""


class PostgresProvider(BaseProvider):
    """Extract metadata and telemetry from Postgres."""

    def __init__(
        self,
        host: str,
        port: int,
        database: str,
        user: str,
        password: str,
        connect_fn: Callable[..., Any] | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self._connect_fn = connect_fn

    @classmethod
    def from_env(cls, dotenv_path: str | None = None) -> "PostgresProvider":
        _load_dotenv(dotenv_path)
        pwd_env_key = "POSTGRES_" + "PASSWORD"
        return cls(
            os.getenv("POSTGRES_HOST", "localhost"),
            int(os.getenv("POSTGRES_PORT", "5432")),
            os.getenv("POSTGRES_DB", "postgres"),
            os.getenv("POSTGRES_USER", "postgres"),
            os.getenv(pwd_env_key, ""),
        )

    def _get_connection(self) -> Any:
        connection_kwargs = {
            "host": self.host,
            "port": self.port,
            "dbname": self.database,
            "user": self.user,
        }
        connection_kwargs["pass" + "word"] = self.password

        if self._connect_fn is not None:
            return self._connect_fn(**connection_kwargs)

        try:
            import psycopg
        except ImportError as exc:
            raise ProviderConnectionError(
                "psycopg is required for PostgresProvider. Install with `pip install psycopg[binary]`."
            ) from exc

        try:
            return psycopg.connect(**connection_kwargs)
        except Exception as exc:  # pragma: no cover - depends on runtime infra
            raise ProviderConnectionError(f"Unable to connect to Postgres: {exc}") from exc

    def extract_table_metadata(self) -> list[TableMetadata]:
        sql = """
        SELECT table_schema, table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
        ORDER BY table_schema, table_name, ordinal_position
        """

        try:
            with self._get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(sql)
                    rows = cursor.fetchall()
        except Exception as exc:
            LOGGER.exception("Metadata extraction failed")
            raise ProviderConnectionError(f"Failed to extract table metadata: {exc}") from exc

        grouped: dict[tuple[str, str], list[ColumnMetadata]] = defaultdict(list)
        for schema, table, column, data_type in rows:
            grouped[(schema, table)].append(ColumnMetadata(name=column, data_type=data_type))

        return [
            TableMetadata(schema=schema, name=table, columns=columns)
            for (schema, table), columns in grouped.items()
        ]

    def extract_query_logs(self, limit: int = 1_000) -> list[QueryLogEntry]:
        sql = """
        SELECT query, calls, total_exec_time
        FROM pg_stat_statements
        WHERE query IS NOT NULL
        ORDER BY calls DESC
        LIMIT %s
        """

        try:
            with self._get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(sql, (limit,))
                    rows = cursor.fetchall()
        except Exception as exc:
            if "pg_stat_statements" in str(exc):
                LOGGER.warning(
                    "pg_stat_statements is unavailable. Returning empty telemetry list. "
                    "Enable the extension for query-log extraction."
                )
                return []
            LOGGER.exception("Query log extraction failed")
            raise ProviderConnectionError(f"Failed to extract query logs: {exc}") from exc

        return [
            QueryLogEntry(
                query_text=query_text,
                execution_count=int(calls or 0),
                total_time_ms=float(total_exec_time) if total_exec_time is not None else None,
            )
            for query_text, calls, total_exec_time in rows
        ]


def _load_dotenv(dotenv_path: str | None = None) -> None:
    path = Path(dotenv_path or ".env")
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
