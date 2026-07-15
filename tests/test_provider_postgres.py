import unittest

from telemetry_to_yaml.providers.postgres import PostgresProvider


class TestPostgresProvider(unittest.TestCase):
    def test_extract_query_logs_rejects_non_positive_limit(self) -> None:
        provider = PostgresProvider(
            host="localhost",
            port=5432,
            database="postgres",
            user="postgres",
            password="",
            connect_fn=lambda **_: None,
        )

        with self.assertRaises(ValueError):
            provider.extract_query_logs(limit=0)
