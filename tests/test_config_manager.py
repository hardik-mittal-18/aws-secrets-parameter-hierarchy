import unittest
from unittest.mock import MagicMock

from backend.config_manager import ConfigManager


class TestConfigManager(unittest.TestCase):

    def test_cache(self):
        manager = ConfigManager("dev", ttl=60)

        manager._load_from_ssm = MagicMock(
            return_value={"app/port": "5000"}
        )

        first = manager.get_config()
        second = manager.get_config()

        self.assertEqual(first, second)
        self.assertEqual(
            manager._load_from_ssm.call_count,
            1
        )

    def test_clear_cache(self):
        manager = ConfigManager("dev", ttl=60)

        manager._load_from_ssm = MagicMock(
            return_value={"app/port": "5000"}
        )

        manager.get_config()
        manager.clear_cache()
        manager.get_config()

        self.assertEqual(
            manager._load_from_ssm.call_count,
            2
        )


if __name__ == "__main__":
    unittest.main()
