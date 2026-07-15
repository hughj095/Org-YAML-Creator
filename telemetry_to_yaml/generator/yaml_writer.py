"""Build and serialize dbt semantic YAML."""

from __future__ import annotations

from pathlib import Path

from telemetry_to_yaml.generator.schemas import DbtSemanticManifest, Dimension, Measure, SemanticModel
from telemetry_to_yaml.parser.analyzer import ParsedTelemetry
from telemetry_to_yaml.providers.base import TableMetadata


def build_manifest(table_metadata: list[TableMetadata], telemetry: ParsedTelemetry) -> DbtSemanticManifest:
    semantic_models: list[SemanticModel] = []

    for table in table_metadata:
        dimensions = [
            Dimension(name=column.name, type="time" if "time" in column.data_type else "categorical")
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
                    if any(token in column.data_type for token in ("int", "numeric", "decimal", "float", "double"))
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
    yaml_text = "\n".join(_to_yaml_lines(payload)) + "\n"
    Path(output_path).write_text(yaml_text, encoding="utf-8")


def _to_yaml_lines(value: object, indent: int = 0) -> list[str]:
    prefix = " " * indent

    if isinstance(value, dict):
        lines: list[str] = []
        for key, nested in value.items():
            if isinstance(nested, (dict, list)):
                lines.append(f"{prefix}{key}:")
                lines.extend(_to_yaml_lines(nested, indent + 2))
            else:
                lines.append(f"{prefix}{key}: {_format_scalar(nested)}")
        return lines

    if isinstance(value, list):
        lines = []
        for item in value:
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}-")
                lines.extend(_to_yaml_lines(item, indent + 2))
            else:
                lines.append(f"{prefix}- {_format_scalar(item)}")
        return lines

    return [f"{prefix}{_format_scalar(value)}"]


def _format_scalar(value: object) -> str:
    if isinstance(value, str):
        if not value or any(ch in value for ch in (":", "#", "'", '"', " ")):
            escaped = value.replace("'", "''")
            return f"'{escaped}'"
        return value
    if value is True:
        return "true"
    if value is False:
        return "false"
    if value is None:
        return "null"
    return str(value)
