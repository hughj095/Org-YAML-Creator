import unittest

from telemetry_to_yaml.providers.base import BaseProvider


class TestBaseProvider(unittest.TestCase):
    def test_base_provider_is_abstract(self) -> None:
        with self.assertRaises(TypeError):
            BaseProvider()
