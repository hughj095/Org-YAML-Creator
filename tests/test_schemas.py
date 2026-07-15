import unittest

from pydantic import ValidationError

from telemetry_to_yaml.generator.schemas import DbtSemanticManifest, Dimension, Measure, SemanticModel


class TestSchema(unittest.TestCase):
    def test_semantic_manifest_serialization(self) -> None:
        manifest = DbtSemanticManifest(
            semantic_models=[
                SemanticModel(
                    name="orders",
                    model="ref('orders')",
                    dimensions=[Dimension(name="ordered_at", type="time")],
                    measures=[Measure(name="orders_count", agg="count", expr="*")],
                )
            ]
        )

        dumped = manifest.model_dump()
        self.assertEqual(dumped["version"], 2)
        self.assertEqual(dumped["semantic_models"][0]["name"], "orders")

    def test_schema_rejects_unexpected_fields(self) -> None:
        with self.assertRaises(ValidationError):
            Dimension.model_validate({"name": "foo", "type": "categorical", "unknown": "value"})
