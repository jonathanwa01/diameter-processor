# diameter-processor

An MQTT processor for converting TCD1304 sensor frames into calibrated
filament-diameter measurements.

## Project layout

- `config/config.example.yaml` documents broker and topic settings.
- `src/config.py` loads and validates the YAML configuration.
- `src/mqtt_client.py` subscribes to the input topic and publishes transformed payloads.
- `src/calculator.py` is the isolated sensor-to-diameter calculation.
- `tests/` contains unit tests that do not require a live MQTT broker.

## Setup

Install `uv` with the official installer:

```shell
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then sync the project's dependencies from the repository root:

```shell
uv sync
```

This will create a virtual environment under `.venv`.

## Configure and run

Configure the config file `config/config.example.yaml`, then set the broker host and input/output topics. Set `measurement mm_per_pixel` to a calibrated object-plane scale in millimeters per pixel; the application rejects a missing or non-positive value rather than emitting an uncalibrated diameter. The real config file is git-ignored. For an authenticated broker, provide both `MQTT_USERNAME` and `MQTT_PASSWORD` through the environment rather than storing credentials in YAML.

Run the processor from the repository root:

```shell
uv run main.py --config config/config.yaml
```

Run the unit tests with:

```shell
uv run -m unittest discover -s tests
```

Install the development tools and enable the Ruff pre-commit hooks with:

```shell
uv sync --group dev
uv run pre-commit install
```

Run the hooks against all files with:

```shell
uv run pre-commit run --all-files
```

## Security note

This project is a university prototype designed for a private local Ethernet network and is not intended to be run on a production network. It was developed locally for isolated lab use, and no passwords or similar security controls are configured for the MQTT broker or sensor connection. Do not expose this project on a shared, public, or production network.

## Run with Docker Compose

Start the diameter processor and its local Mosquitto broker with:

```shell
docker compose up --build
```

The broker is available on `localhost:1883`. The sensor publishes frames to `optical-diameter/frame`; the processor publishes an ASCII decimal diameter in millimeters to `sensors/diameter`. The included broker configuration allows anonymous connections and is intended only for local development; use an appropriately secured broker in production. If the broker requires credentials, export `MQTT_USERNAME` and `MQTT_PASSWORD` before starting Compose.

## Frame decoding and measurement

The processor validates the producer's 7422-byte `TCD2` frame, reads the little-endian output count and ADC samples, and uses active pixels S1–S3648 (outputs 32–3679). It estimates the bright-background and darker-shadow levels, sets the edge threshold halfway between them, interpolates the two threshold crossings, and multiplies their pixel separation by `measurement.mm_per_pixel`. The method assumes one contiguous darker filament shadow in the frame.

Malformed frames, missing contrast, multiple shadows, and shadows clipped by the sensor edge are logged and not published. This is an initial measurement method; validate it against recorded sensor frames and reference diameters before relying on its measurements. The firmware repository supplies the frame protocol but does not provide a diameter algorithm or optical calibration.
