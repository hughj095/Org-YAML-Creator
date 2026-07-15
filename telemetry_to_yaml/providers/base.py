"""Abstract data-provider contracts for metadata and telemetry extraction."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class ColumnMetadata:
    """Physical column definition."""

    name: str
    data_type: str


@dataclass(slots=True, frozen=True)
class TableMetadata:
    """Physical table definition."""

    schema: str
    name: str
    columns: list[ColumnMetadata]


@dataclass(slots=True, frozen=True)
class QueryLogEntry:
    """Minimal query telemetry payload."""

    query_text: str
    execution_count: int = 1
    total_time_ms: float | None = None


class BaseProvider(ABC):
    """Provider abstraction used by the pipeline."""

    @abstractmethod
    def extract_table_metadata(self) -> list[TableMetadata]:
        """Return physical table/column metadata."""

    @abstractmethod
    def extract_query_logs(self, limit: int = 1_000) -> list[QueryLogEntry]:
        """Return active query telemetry logs."""
