import argparse
import logging
from collections.abc import Sequence
from pathlib import Path

from .config import load_config
from .mqtt_client import run_mqtt


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Process diameter sensor MQTT messages."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/config.example.yaml"),
        help="Path to the YAML configuration file.",
    )
    args = parser.parse_args(argv)
    print(f"Using configuration file: {args.config}")
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    config = load_config(args.config)
    try:
        run_mqtt(config)
    except ConnectionRefusedError as e:
        logging.exception("Could not connect to MQTT broker: %s", e)
        raise SystemExit(1) from e
