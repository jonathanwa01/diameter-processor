AGENTS.md — Projektwerkstatt context for diameter-processor
Purpose and evidence boundaries

This document gives coding agents the wider project context, not just the processor's implementation details. 
Check the working tree before making changes. This document does not claim access to every past project conversation.

1. Overall project

Projektwerkstatt is developing and validating a non-contact optical sensor for 3D-printer filament diameter. The system should record diameter variation and support filament quality assessment. Future integration into an extrusion or production process is a longer-term goal, not the current processor's responsibility.

The proposed measurement principle is optical shadow measurement:

    A light source illuminates the filament from one side.

    A detector on the opposite side captures its silhouette.

    Software identifies the two filament edges.

    Their separation is converted into a calibrated diameter measurement.

The intended prototype follows a linear-sensor approach. Prior photo-based discussions mentioned an existing light source with beam expansion/collimation and a linear sensor board. Exact light-source and detector models, pixel pitch, electronics, and optical geometry are not verified here. Do not turn those earlier hardware inferences into specifications.

A single measurement axis measures projected width; do not label it as a complete cross-sectional shape or ovality measurement.
2. Working constraints and priorities

Prior discussions described a small educational/scientific, open-source DIY project with three people, approximately four hours per person per week over ten weeks. Treat this as planning context, not a newly confirmed schedule.

The latest retrieved scope clarification prioritizes:

    Live diameter calculation as measurements arrive.

    Container-deployable software.

    Reusing the functioning monitoring stack.

    Minimal additional infrastructure; advanced processing and extras can follow.

    Python for processing; controller software was described as using Rust libraries.

    A laboratory PC and one sensor initially, without unnecessarily blocking later expansion.

Earlier discussions mentioned snapshots every 50–100 ms and later approximately 10 frames per second. Use 10 frames/s as an initial benchmark scenario, not a verified sensor limit or measured processor capacity. An earlier payload estimate of "20 kb" was ambiguous: do not assume bytes versus bits, pixel count, or sample bit depth.
3. System boundary

This repository is ONLY the processor component. It is not the complete optical instrument or the owner of the full deployment stack.

Conceptual integration path, combining the discussed stack with the current processor interface:

Optical sensor + controller
-> raw sensor frames over MQTT / Ethernet
-> Eclipse Mosquitto
-> diameter-processor (this repository)
-> processed measurements over MQTT
-> Telegraf
-> InfluxDB
-> Grafana

The complete end-to-end wiring above has not been verified from this repository. Mosquitto, Telegraf, InfluxDB, and Grafana were reported as existing components in project discussions. Their deployed versions, configurations, and ownership are not established here.

Processor responsibilities:

    Consume raw sensor payloads.

    Validate and decode the agreed sensor message format.

    Calculate filament diameter using a defined calibration.

    Publish an agreed derived-measurement payload.

    Provide useful diagnostics and testable processing logic.

Outside this repository's default scope:

    Firmware, physical acquisition, optics, alignment, and mechanical transport.

    Owning or rebuilding the broker, database, and dashboard stack.

    Production/extrusion feedback control.

    Automatic deployment of new databases or distributed-processing infrastructure.

Coordinate interface changes with the producers and consumers rather than silently changing topics, units, or payload schemas.
4. Current repository state — verified at the reviewed commit

This is an MQTT subscriber/publisher scaffold, NOT a validated diameter-measurement implementation.

    README.md documents configuration, execution, tests, and the placeholder calculation.

    main.py is the documented repository-root entry point.

    src/cli.py contains CLI code.

    src/config.py loads and validates YAML configuration according to the README; its implementation was not inspected for this context document.

    src/mqtt_client.py receives bytes, calls an injected transform, and publishes the returned bytes.

    src/calculator.py defines calculate_diameter(raw_payload: bytes) -> bytes.

    The calculation currently ignores its input and always returns b"0.0". This is a placeholder, not a real measurement, calibration, or safe invalid-value convention.

    MQTT subscription and publication use QoS 1 in the inspected client.

    The transform runs synchronously inside the message callback.

    Processing/publish exceptions are logged. No durable raw-event store or replay mechanism is established by the inspected code.

    Publish return codes are checked; do not equate this with an end-to-end durability guarantee.

    config/config.example.yaml uses localhost:1883, keepalive_seconds: 60, client_id: diameter-processor, input topic sensors/raw, and output topic sensors/diameter. These are example settings, not a confirmed production contract.

    Authentication is documented through MQTT_USERNAME and MQTT_PASSWORD, supplied together through the environment. Real config/config.yaml is documented as git-ignored.

    pyproject.toml requires Python >=3.13, paho-mqtt >=2.1,<3, and PyYAML >=6,<7. A uv.lock file is present.

    tests/ is present, and README describes broker-independent unit tests. Tests were not executed for this review.

    No Dockerfile or Compose file was present in the inspected repository root. Container deployment remains a requirement, not a verified implemented feature.

Documented commands, run from the repository root:

python main.py --config config/config.yaml
python -m unittest discover -s tests

Packaging caveat: pyproject.toml declares diameter-processor = "diameter_processor.cli:main", whereas the inspected source listing contains flat src/cli.py and related modules. src/mqtt_client.py imports AppConfig via "from config import AppConfig". Inspect and test module resolution and installed CLI behavior before relying on the package entry point. Do not assert it works based only on configuration.
5. Architecture discussion history — do not mistake options for decisions

Earlier discussions explored archiving raw frames before processing, including a PostgreSQL raw-event store and a separate Python processing service. Scientific replayability, batch/experiment metadata, and later reprocessing were motivations.

A later user clarification explicitly prioritized live diameter calculation and container deployment, questioned adding another Python job, and deferred extras. The resulting advice favored a minimal calculation stage within the existing Telegraf path rather than adding database-first infrastructure immediately.

The repository now provides a standalone Python MQTT input/output scaffold. That is the current code boundary, regardless of earlier Telegraf/Starlark/execd suggestions. Do not remove this component, move the algorithm into Telegraf, or add PostgreSQL merely because those options appeared in prior discussion. Ask for an explicit architectural decision before making such changes.

Durable raw capture and replay remain possible future work, not confirmed current requirements or implemented capabilities.
6. Measurement model and unresolved contracts

Conceptually, for a linear calibration:

width_px = right_edge_px - left_edge_px
diameter_mm = width_px * calibrated_mm_per_pixel

This is explanatory, not an approved production algorithm. Optical geometry, calibration method, edge convention, distortion, and sensor characteristics must be established before using it quantitatively. Do not substitute physical pixel pitch for calibrated object-space scale without justification.

Before implementing real decoding/calculation, obtain or explicitly agree:

    Representative MQTT payloads from the controller.

    Encoding, framing, pixel count, sample type, endianness if applicable, and intensity range.

    Whether one message contains one complete sensor frame.

    Source timestamps, clock semantics, device identifiers, and sequence numbers if provided.

    Detector orientation and expected shadow polarity.

    Sensor and optical geometry; calibration samples, units, and calibration procedure.

    Required diameter range, accuracy, repeatability, and acceptable latency.

    Behavior for no filament, partial shadows, multiple shadows, saturation, low contrast, malformed input, and missing/duplicate frames.

    Output schema, units, validity/quality representation, and compatibility with Telegraf.

    Deployment environment, broker settings, and supported recovery behavior.

Do not silently invent defaults for these physical and interface contracts. Schemas and algorithms can be proposed with synthetic tests, but must be labeled provisional until agreed and validated.
7. Time versus filament length

The overall goal includes recording variation along filament length. Timestamps alone establish diameter versus time, not measured diameter versus length.

A longitudinal coordinate requires a justified motion reference, such as measured feed displacement, or an explicitly stated speed assumption with its limitations. Position sensing and its protocol are not established in the retrieved context. Do not fabricate length coordinates or imply they are already available.
8. Guidance for coding agents — proposed working rules

These are practical guardrails for future work, not claims that the team previously approved every item.

    Read the current code and tests first; do not assume this snapshot remains current.

    Keep mathematical processing separable from MQTT, configuration, and persistence.

    Prefer a small, understandable implementation over speculative abstraction or infrastructure.

    Preserve existing interfaces unless an intentional migration is requested; document necessary changes.

    Never present placeholder output, failed calibration, or malformed input as a valid physical measurement.

    Keep credentials out of source control, fixtures, documentation, and logs.

    Make units and calibration provenance explicit when defining the output contract.

    Use synthetic frames for deterministic algorithm tests, and real recorded/reference measurements for validation. Synthetic success alone does not prove instrument accuracy.

    Test normal shadows, shifted and subpixel edges if supported, noise, malformed frames, no shadow, ambiguous shadows, and invalid calibration as relevant to the agreed method.

    Test MQTT transformation and error behavior without requiring a live broker where practical.

    Benchmark representative payloads around 10 frames/s. Current callback execution is synchronous; do not promise throughput or add worker pools without measurements.

    Treat container support as an explicit deliverable. Verify startup, configuration, broker addressing, and shutdown; do not describe deployment as complete before testing.

    Do not claim lossless delivery, durable replay, exact-once processing, a specific accuracy, or production readiness without implementation and evidence.

    Report exactly what changed, what was tested, what could not be tested, and which physical/interface assumptions remain open.

9. Suggested next implementation sequence — not an approved roadmap

    Obtain a representative raw frame and settle the input/output contract.

    Establish calibration and a simple, testable baseline edge detector.

    Replace the placeholder and define explicit invalid-measurement behavior.

    Validate against reference measurements and report error/repeatability.

    Verify packaging, tests, and container execution.

    Integrate the agreed output with the existing Telegraf/InfluxDB/Grafana stack and measure end-to-end latency.

    Revisit raw archiving, replay, experiment metadata, multiple sensors, longitudinal tracking, and production integration only when the milestone requires them.

10. Provenance and maintenance

Repository evidence was read through the authenticated GitHub connector, pinned to commit c0054547cd3c4efc047370d1601ce9422297f272:

    README.md

    pyproject.toml

    src/calculator.py

    src/mqtt_client.py

    config/config.example.yaml

    Repository root and src/ directory listings

Project context came from the Projektwerkstatt project description and retrieved discussions dated 2026-10-27 and 2026-11-03. Those discussions included both user requirements and assistant proposals; this document deliberately distinguishes them.

Update this file when message contracts, calibration, ownership, deployment, or accepted architecture changes. Keep historical alternatives labeled as historical. Implementation behavior should be checked against the current code; project goals should not be inferred solely from whatever code exists today.