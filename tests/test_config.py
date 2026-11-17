import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from config import load_config

VALID_CONFIG = """\
mqtt:
  host: localhost
  port: 1883
  keepalive_seconds: 60
  client_id: test-client
topics:
  input: sensors/raw
  output: sensors/diameter
measurement:
  mm_per_pixel: 0.01
"""


class LoadConfigTests(unittest.TestCase):
    def load_yaml(self, content: str):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.yaml"
            path.write_text(content, encoding="utf-8")
            return load_config(path)

    def test_loads_broker_and_topic_settings(self):
        with patch.dict(os.environ, {}, clear=True):
            config = self.load_yaml(VALID_CONFIG)

        self.assertEqual(config.mqtt.host, "localhost")
        self.assertEqual(config.mqtt.port, 1883)
        self.assertEqual(config.topics.input, "sensors/raw")
        self.assertEqual(config.topics.output, "sensors/diameter")
        self.assertEqual(config.measurement.mm_per_pixel, 0.01)

    def test_rejects_invalid_port(self):
        invalid_config = VALID_CONFIG.replace("port: 1883", "port: 70000")
        with (
            patch.dict(os.environ, {}, clear=True),
            self.assertRaisesRegex(ValueError, "between 1 and 65535"),
        ):
            self.load_yaml(invalid_config)

    def test_requires_credentials_as_a_pair(self):
        with (
            patch.dict(os.environ, {"MQTT_USERNAME": "user"}, clear=True),
            self.assertRaisesRegex(ValueError, "Set both MQTT_USERNAME"),
        ):
            self.load_yaml(VALID_CONFIG)

    def test_requires_positive_calibrated_scale(self):
        invalid_config = VALID_CONFIG.replace("mm_per_pixel: 0.01", "mm_per_pixel: 0")
        with (
            patch.dict(os.environ, {}, clear=True),
            self.assertRaisesRegex(ValueError, "object-plane calibration"),
        ):
            self.load_yaml(invalid_config)


if __name__ == "__main__":
    unittest.main()
