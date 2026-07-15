"""Telemetry parser that extracts joins, usage frequency, and candidate metrics."""

from __future__ import annotations

import re
from dataclasses import dataclass

from telemetry_to_yaml.providers.base import QueryLogEntry, TableMetadata

JOIN_PATTERN = re.compile(r"\bjoin\b\s+\S+\s+\bon\b\s+([\w\.]+\s*=\s*[\w\.]+)", re.IGNORECASE)
COLUMN_PATTERN = re.compile(r"([A-Za-z_][\w]*)\.([A-Za-z_][\w]*)")
COUNT_PATTERN = re.compile(r"\bcount\s*\(", re.IGNORECASE)
SUM_PATTERN = re.compile(r"\bsum\s*\(", re.IGNORECASE)
AVG_PATTERN = re.compile(r"\bavg\s*\(", re.IGNORECASE)


@dataclass(slots=True)
class ParsedTelemetry:
    """Derived semantic candidates from metadata and query logs."""

    join_conditions: dict[str, int]
    column_access_frequency: dict[str, int]
    potential_metrics: dict[str, int]


def analyze_telemetry(
    table_metadata: list[TableMetadata],
    query_logs: list[QueryLogEntry],
) -> ParsedTelemetry:
    known_columns = {
        f"{table.name}.{column.name}"
        for table in table_metadata
        for column in table.columns
    }

    join_conditions: dict[str, int] = {}
    column_access_frequency: dict[str, int] = {}
    potential_metrics: dict[str, int] = {"count": 0, "sum": 0, "avg": 0}

    for log in query_logs:
        query = log.query_text
        weight = max(log.execution_count, 1)

        for join_match in JOIN_PATTERN.findall(query):
            normalized = " ".join(join_match.split())
            join_conditions[normalized] = join_conditions.get(normalized, 0) + weight

        for table_name, column_name in COLUMN_PATTERN.findall(query):
            key = f"{table_name}.{column_name}"
            if key in known_columns:
                column_access_frequency[key] = column_access_frequency.get(key, 0) + weight

        potential_metrics["count"] += len(COUNT_PATTERN.findall(query)) * weight
        potential_metrics["sum"] += len(SUM_PATTERN.findall(query)) * weight
        potential_metrics["avg"] += len(AVG_PATTERN.findall(query)) * weight

    return ParsedTelemetry(
        join_conditions=join_conditions,
        column_access_frequency=column_access_frequency,
        potential_metrics={name: value for name, value in potential_metrics.items() if value > 0},
    )
