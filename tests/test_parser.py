import unittest

from telemetry_to_yaml.parser.analyzer import analyze_telemetry
from telemetry_to_yaml.providers.base import ColumnMetadata, QueryLogEntry, TableMetadata


class TestAnalyzer(unittest.TestCase):
    def test_analyze_telemetry_extracts_join_usage_and_metrics(self) -> None:
        tables = [
            TableMetadata(
                schema="public",
                name="orders",
                columns=[
                    ColumnMetadata(name="id", data_type="integer"),
                    ColumnMetadata(name="customer_id", data_type="integer"),
                ],
            ),
            TableMetadata(
                schema="public",
                name="customers",
                columns=[ColumnMetadata(name="id", data_type="integer")],
            ),
        ]

        logs = [
            QueryLogEntry(
                query_text=(
                    "SELECT COUNT(*) FROM public.orders JOIN public.customers "
                    "ON orders.customer_id = customers.id AND orders.id = customers.id"
                ),
                execution_count=3,
            ),
            QueryLogEntry(
                query_text='SELECT * FROM "public"."orders" WHERE "orders"."customer_id" > 0',
                execution_count=2,
            ),
        ]

        parsed = analyze_telemetry(tables, logs)
        self.assertEqual(parsed.join_conditions["orders.customer_id = customers.id"], 3)
        self.assertEqual(parsed.join_conditions["orders.id = customers.id"], 3)
        self.assertEqual(parsed.column_access_frequency["orders.customer_id"], 5)
        self.assertEqual(parsed.potential_metrics["count"], 3)
