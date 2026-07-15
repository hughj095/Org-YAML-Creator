import unittest

from telemetry_to_yaml.generator.yaml_writer import build_manifest
from telemetry_to_yaml.parser.analyzer import ParsedTelemetry
from telemetry_to_yaml.providers.base import ColumnMetadata, TableMetadata


class TestYamlWriter(unittest.TestCase):
    def test_build_manifest_uses_precise_type_detection(self) -> None:
        table = TableMetadata(
            schema="public",
            name="events",
            columns=[
                ColumnMetadata(name="runtime_config", data_type="varchar"),
                ColumnMetadata(name="event_time", data_type="timestamp"),
                ColumnMetadata(name="printed_output", data_type="text"),
                ColumnMetadata(name="amount", data_type="numeric(12,2)"),
            ],
        )
        telemetry = ParsedTelemetry(join_conditions={}, column_access_frequency={}, potential_metrics={"sum": 1})

        manifest = build_manifest([table], telemetry)
        model = manifest.semantic_models[0]

        dimensions = {dim.name: dim.type for dim in model.dimensions}
        self.assertEqual(dimensions["event_time"], "time")
        self.assertEqual(dimensions["runtime_config"], "categorical")
        self.assertEqual(dimensions["printed_output"], "categorical")

        self.assertEqual(len(model.measures), 1)
        self.assertEqual(model.measures[0].expr, "amount")
