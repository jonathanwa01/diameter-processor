import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class MqttSettings:
    host: str
    port: int
    keepalive_seconds: int
    client_id: str
    username: str | None
    password: str | None
    


@dataclass(frozen=True)
class TopicSettings:
    input: str
    output: str


@dataclass(frozen=True)
class MeasurementSettings:
    mm_per_pixel: float


@dataclass(frozen=True)
class AppConfig:
    mqtt: MqttSettings
    topics: TopicSettings
    measurement: MeasurementSettings


def _mapping(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"Configuration section '{name}' must be a mapping.")
    return value


def _required_string(section: dict[str, Any], key: str, section_name: str) -> str:
    value = section.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"'{section_name}.{key}' must be a non-empty string.")
    return value


def _required_integer(section: dict[str, Any], key: str, section_name: str) -> int:
    value = section.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"'{section_name}.{key}' must be an integer.")
    return value


def _required_scale(section: dict[str, Any], key: str, section_name: str) -> float:
    value = section.get(key)
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value <= 0
    ):
        raise ValueError(
            f"'{section_name}.{key}' must be a finite value greater than zero; "
            "set it from an object-plane calibration."
        )
    return float(value)


def load_config(path: Path) -> AppConfig:
    """Load and validate broker, topic, and measurement settings from YAML."""
    with path.open(encoding="utf-8") as config_file:
        raw_config = _mapping(yaml.safe_load(config_file), "root")

    mqtt_config = _mapping(raw_config.get("mqtt"), "mqtt")
    topic_config = _mapping(raw_config.get("topics"), "topics")
    measurement_config = _mapping(raw_config.get("measurement"), "measurement")

    port = _required_integer(mqtt_config, "port", "mqtt")
    keepalive = _required_integer(mqtt_config, "keepalive_seconds", "mqtt")
    mm_per_pixel = _required_scale(measurement_config, "mm_per_pixel", "measurement")
    if not 1 <= port <= 65535:
        raise ValueError("'mqtt.port' must be between 1 and 65535.")
    if keepalive <= 0:
        raise ValueError("'mqtt.keepalive_seconds' must be greater than zero.")

    username = os.environ.get("MQTT_USERNAME")
    password = os.environ.get("MQTT_PASSWORD")
    if (username is None) != (password is None):
        raise ValueError("Set both MQTT_USERNAME and MQTT_PASSWORD, or neither.")

    return AppConfig(
        mqtt=MqttSettings(
            host=_required_string(mqtt_config, "host", "mqtt"),
            port=port,
            keepalive_seconds=keepalive,
            client_id=_required_string(mqtt_config, "client_id", "mqtt"),
            username=username,
            password=password,
        ),
        topics=TopicSettings(
            input=_required_string(topic_config, "input", "topics"),
            output=_required_string(topic_config, "output", "topics"),
        ),
        measurement=MeasurementSettings(mm_per_pixel=mm_per_pixel),
    )
