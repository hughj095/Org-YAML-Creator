"""Telemetry parser that extracts joins, usage frequency, and candidate metrics."""

from __future__ import annotations

import re
from dataclasses import dataclass

from telemetry_to_yaml.providers.base import QueryLogEntry, TableMetadata

IDENTIFIER_PATTERN = r'(?:"(?:[^"]|"")+"|[A-Za-z_][A-Za-z0-9_]*)'
QUALIFIED_IDENTIFIER_PATTERN = rf"{IDENTIFIER_PATTERN}(?:\.{IDENTIFIER_PATTERN}){{1,2}}"
JOIN_CLAUSE_PATTERN = re.compile(
    r"\bjoin\b\s+\S+\s+\bon\b\s+(.+?)(?=\bjoin\b|\bwhere\b|\bgroup\b|\border\b|\blimit\b|$)",
    re.IGNORECASE | re.DOTALL,
)
EQUALITY_PATTERN = re.compile(
    rf"{QUALIFIED_IDENTIFIER_PATTERN}\s*=\s*{QUALIFIED_IDENTIFIER_PATTERN}",
    re.IGNORECASE,
)
COLUMN_PATTERN = re.compile(QUALIFIED_IDENTIFIER_PATTERN)
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
        f"{table.name}.{column.name}".lower()
        for table in table_metadata
        for column in table.columns
    }

    join_conditions: dict[str, int] = {}
    column_access_frequency: dict[str, int] = {}
    potential_metrics: dict[str, int] = {"count": 0, "sum": 0, "avg": 0}

    for log in query_logs:
        query = log.query_text
        weight = max(log.execution_count, 1)

        for clause in JOIN_CLAUSE_PATTERN.findall(query):
            for join_match in EQUALITY_PATTERN.findall(clause):
                normalized = _normalize_join_condition(join_match)
                join_conditions[normalized] = join_conditions.get(normalized, 0) + weight

        for reference in COLUMN_PATTERN.findall(query):
            key = _normalize_reference(reference)
            if key and key in known_columns:
                column_access_frequency[key] = column_access_frequency.get(key, 0) + weight

        potential_metrics["count"] += len(COUNT_PATTERN.findall(query)) * weight
        potential_metrics["sum"] += len(SUM_PATTERN.findall(query)) * weight
        potential_metrics["avg"] += len(AVG_PATTERN.findall(query)) * weight

    return ParsedTelemetry(
        join_conditions=join_conditions,
        column_access_frequency=column_access_frequency,
        potential_metrics={name: value for name, value in potential_metrics.items() if value > 0},
    )


def _normalize_reference(reference: str) -> str | None:
    clean = reference.replace('"', "")
    parts = clean.split(".")
    if len(parts) < 2:
        return None
    table_name, column_name = parts[-2], parts[-1]
    return f"{table_name.lower()}.{column_name.lower()}"


def _normalize_join_condition(condition: str) -> str:
    return " ".join(condition.replace('"', "").split()).lower()
