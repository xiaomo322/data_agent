import os
import unittest
import warnings
from pathlib import Path
from unittest.mock import patch

from omegaconf import OmegaConf


class AppConfigTests(unittest.TestCase):
    def test_missing_api_keys_resolve_to_empty_strings_without_warnings(self):
        config_path = Path(__file__).parents[1] / "conf" / "app_config.yaml"

        with (
            patch.dict(os.environ, {}, clear=True),
            warnings.catch_warnings(record=True) as caught_warnings,
        ):
            warnings.simplefilter("always")
            config = OmegaConf.load(config_path)
            resolved = OmegaConf.to_container(config, resolve=True)

        self.assertEqual("", resolved["text_llm"]["api_key"])
        self.assertEqual("", resolved["code_llm"]["api_key"])
        self.assertEqual([], [str(item.message) for item in caught_warnings])


if __name__ == "__main__":
    unittest.main()
