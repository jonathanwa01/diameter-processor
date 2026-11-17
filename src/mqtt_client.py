import logging
from collections.abc import Callable

import paho.mqtt.client as mqtt

from config import AppConfig

logger = logging.getLogger(__name__)
PayloadTransform = Callable[[bytes], bytes]


def run_mqtt(config: AppConfig, transform: PayloadTransform) -> None:
    """Subscribe to the configured input topic and publish transformed payloads."""
    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id=config.mqtt.client_id,
    )
    if config.mqtt.username is not None and config.mqtt.password is not None:
        client.username_pw_set(config.mqtt.username, config.mqtt.password)

    def on_connect(
        client: mqtt.Client,
        userdata: object,
        flags: mqtt.ConnectFlags,
        reason_code: mqtt.ReasonCode,
        properties: mqtt.Properties | None,
    ) -> None:
        if reason_code.is_failure:
            logger.error("MQTT connection failed: %s", reason_code)
            return
        result, message_id = client.subscribe(config.topics.input, qos=1)
        if result != mqtt.MQTT_ERR_SUCCESS:
            logger.error("Could not subscribe to topic %s (code %s)", config.topics.input, result)
            return
        logger.info("Subscribed to %s (message id %s)", config.topics.input, message_id)

    def on_message(
        client: mqtt.Client,
        userdata: object,
        message: mqtt.MQTTMessage,
    ) -> None:
        try:
            output_payload = transform(message.payload)
            if not isinstance(output_payload, bytes):
                raise TypeError("The payload transform must return bytes.")
            info = client.publish(config.topics.output, output_payload, qos=1)
            if info.rc != mqtt.MQTT_ERR_SUCCESS:
                raise RuntimeError(f"MQTT publish failed with code {info.rc}.")
        except Exception:
            logger.exception("Failed to process MQTT message from %s", message.topic)

    client.on_connect = on_connect
    client.on_message = on_message
    
    logger.info(
        "Connecting to MQTT broker %s:%s",
        config.mqtt.host,
        config.mqtt.port,
    )
    client.connect(
        config.mqtt.host,
        config.mqtt.port,
        config.mqtt.keepalive_seconds,
    )
    logger.info(
        "Connected to MQTT broker %s:%s",
        config.mqtt.host,
        config.mqtt.port,
    )
    client.loop_forever()
