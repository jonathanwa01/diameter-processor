# diameter-processor

An MQTT subscriber/publisher scaffold for processing diameter sensor readings.

## Project layout

- `config/config.example.yaml` documents broker and topic settings.
- `src/diameter_processor/config.py` loads and validates the YAML configuration.
- `src/diameter_processor/mqtt_client.py` subscribes to the input topic and publishes transformed payloads.
- `src/diameter_processor/calculator.py` is the isolated sensor-to-diameter calculation.
- `tests/` contains unit tests that do not require a live MQTT broker.

## Configure and run

Copy `config/config.example.yaml` to `config/config.yaml`, then set the broker
host and input/output topics. The real config file is git-ignored. For an
authenticated broker, provide both `MQTT_USERNAME` and `MQTT_PASSWORD` through
the environment rather than storing credentials in YAML.

Install the project's dependencies in your environment, then run from the
repository root:

```shell
python main.py --config config/config.yaml
```

Run the unit tests with:

```shell
python -m unittest discover -s tests
```

## Calculation integration needed

The MQTT flow passes each input message's raw bytes to
`calculate_diameter()` and publishes the returned bytes. The sensor payload
format and diameter formula were not specified, so that function deliberately
raises `NotImplementedError` until those details are implemented. This avoids
publishing a fabricated or misleading diameter.
