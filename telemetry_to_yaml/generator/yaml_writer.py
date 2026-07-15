"""Build and serialize dbt semantic YAML."""

from __future__ import annotations

from pathlib import Path

import yaml

from telemetry_to_yaml.generator.schemas import DbtSemanticManifest, Dimension, Measure, SemanticModel
from telemetry_to_yaml.parser.analyzer import ParsedTelemetry
from telemetry_to_yaml.providers.base import TableMetadata

TIME_TYPES = {"date", "datetime", "timestamp", "timestamptz", "time"}
NUMERIC_TYPES = {
    "smallint",
    "integer",
    "bigint",
    "int",
    "int2",
    "int4",
    "int8",
    "numeric",
    "decimal",
    "real",
    "float",
    "float4",
    "float8",
    "double precision",
}


def build_manifest(table_metadata: list[TableMetadata], telemetry: ParsedTelemetry) -> DbtSemanticManifest:
    semantic_models: list[SemanticModel] = []

    for table in table_metadata:
        dimensions = [
            Dimension(name=column.name, type="time" if _is_time_type(column.data_type) else "categorical")
            for column in table.columns
        ]

        measures: list[Measure] = []
        for metric_name in telemetry.potential_metrics:
            if metric_name == "count":
                measures.append(Measure(name=f"{table.name}_count", agg="count", expr="*"))
            else:
                numeric_columns = [
                    column.name
                    for column in table.columns
                    if _is_numeric_type(column.data_type)
                ]
                if numeric_columns:
                    measures.append(
                        Measure(name=f"{table.name}_{metric_name}", agg=metric_name, expr=numeric_columns[0])
                    )

        semantic_models.append(
            SemanticModel(
                name=table.name,
                model=f"ref('{table.name}')",
                dimensions=dimensions,
                measures=measures,
            )
        )

    return DbtSemanticManifest(semantic_models=semantic_models)


def write_manifest_yaml(manifest: DbtSemanticManifest, output_path: str) -> None:
    payload = manifest.model_dump(exclude_none=True)
    yaml_text = yaml.safe_dump(payload, sort_keys=False)
    Path(output_path).write_text(yaml_text, encoding="utf-8")


def _canonical_data_type(data_type: str) -> str:
    return data_type.strip().lower().split("(", 1)[0].strip()


def _is_time_type(data_type: str) -> bool:
    return _canonical_data_type(data_type) in TIME_TYPES


def _is_numeric_type(data_type: str) -> bool:
    return _canonical_data_type(data_type) in NUMERIC_TYPES
