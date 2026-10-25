import os

import paho.mqtt.client as mqtt

from .db import MeteoDB
from .processor import MessageProcessor


TOPIC_SENSOR = "meteo/sensor/+"
TOPIC_EXTERNAL = "meteo/external/+"


def main() -> None:
    mqtt_host = os.environ.get("MQTT_HOST", "localhost")
    mqtt_port = int(os.environ.get("MQTT_PORT", "1883"))
    mqtt_username = os.environ.get("MQTT_USERNAME", "")
    mqtt_password = os.environ.get("MQTT_PASSWORD", "")
    mqtt_qos = int(os.environ.get("MQTT_QOS", "1"))
    client_id = os.environ.get("MQTT_CLIENT_ID", "meteo-consumer")

    db = MeteoDB.from_env()
    processor = MessageProcessor(db)

    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id=client_id,
        clean_session=False,
        protocol=mqtt.MQTTv311,
        manual_ack=True,
    )

    if mqtt_username:
        client.username_pw_set(mqtt_username, mqtt_password)

    client.reconnect_delay_set(min_delay=1, max_delay=60)

    def on_connect(client, userdata, connect_flags, reason_code, properties):
        del userdata, connect_flags, properties

        if reason_code != 0:
            print(f"[MQTT] Conexión rechazada: {reason_code}")
            return

        print(f"[MQTT] Conectado a {mqtt_host}:{mqtt_port}")

        client.subscribe(
            [
                (TOPIC_SENSOR, mqtt_qos),
                (TOPIC_EXTERNAL, mqtt_qos),
            ]
        )

        print(f"[MQTT] Suscripto a {TOPIC_SENSOR}")
        print(f"[MQTT] Suscripto a {TOPIC_EXTERNAL}")

    def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
        del client, userdata, disconnect_flags, properties

        if reason_code != 0:
            print(f"[MQTT] Conexión perdida: {reason_code}")
        else:
            print("[MQTT] Desconectado correctamente.")

    def on_message(client, userdata, message):
        del userdata

        should_ack = processor.process(message.payload)

        if should_ack:
            client.ack(message.mid, message.qos)
        else:
            print(
                "[MQTT] Mensaje no ACKeado por falla de persistencia; "
                "podrá ser reentregado por QoS 1."
            )

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    print("=== Meteo Consumer ===")
    print(f"[CONFIG] Broker: {mqtt_host}:{mqtt_port}")
    print(f"[CONFIG] QoS: {mqtt_qos}")

    try:
        client.connect(
            mqtt_host,
            mqtt_port,
            keepalive=60,
        )
        client.loop_forever()
    finally:
        db.dispose()


if __name__ == "__main__":
    main()
