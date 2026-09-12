import json
import time
from threading import Event
from typing import Any

import paho.mqtt.client as mqtt

from .config import Settings
from .payload_builder import build_status_payload


class MqttPublisher:
    """Mismo patrón que services/api_smn/src/mqtt_publisher.py -- ver el
    comentario ahí sobre por qué está duplicado en vez de compartido."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._connected = Event()
        self._client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=f"api-omixom-{settings.node_id}",
            protocol=mqtt.MQTTv311,
        )

        if settings.mqtt_username:
            self._client.username_pw_set(settings.mqtt_username, settings.mqtt_password)

        offline_payload = json.dumps(
            build_status_payload(node_id=settings.node_id, status="offline"),
            separators=(",", ":"),
        )
        self._client.will_set(
            settings.status_topic,
            payload=offline_payload,
            qos=settings.mqtt_qos,
            retain=True,
        )
        self._client.reconnect_delay_set(min_delay=1, max_delay=30)
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect

    def _on_connect(self, client, userdata, connect_flags, reason_code, properties) -> None:
        del client, userdata, connect_flags, properties
        if reason_code.is_failure:
            print(f"[MQTT] Conexión rechazada: {reason_code}")
            self._connected.clear()
            return
        print("[MQTT] Conectado al broker.")
        self._connected.set()

    def _on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties) -> None:
        del client, userdata, disconnect_flags, properties
        self._connected.clear()
        if reason_code.is_failure:
            print(f"[MQTT] Conexión perdida; se reintentará: {reason_code}")
        else:
            print("[MQTT] Desconectado correctamente.")

    def connect(self) -> None:
        print(f"[MQTT] Conectando a {self._settings.mqtt_host}:{self._settings.mqtt_port}...")
        self._client.connect(
            self._settings.mqtt_host,
            self._settings.mqtt_port,
            keepalive=self._settings.mqtt_keepalive_seconds,
        )
        self._client.loop_start()
        if not self._connected.wait(self._settings.mqtt_connect_timeout_seconds):
            self._client.loop_stop()
            raise TimeoutError("No se pudo conectar al broker MQTT.")
        self.publish_status("online")

    def publish_status(self, status: str) -> None:
        payload = build_status_payload(node_id=self._settings.node_id, status=status)
        self._publish_json(self._settings.status_topic, payload, retain=True)

    def publish_measurement(self, payload: dict[str, Any]) -> None:
        self._publish_json(self._settings.measurement_topic, payload, retain=False)

    def _publish_json(self, topic: str, payload: dict[str, Any], *, retain: bool) -> None:
        if not self._connected.is_set():
            deadline = time.monotonic() + self._settings.mqtt_connect_timeout_seconds
            while not self._connected.is_set() and time.monotonic() < deadline:
                time.sleep(0.1)
        if not self._connected.is_set():
            raise ConnectionError("El cliente MQTT no está conectado.")

        serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        result = self._client.publish(
            topic,
            payload=serialized,
            qos=self._settings.mqtt_qos,
            retain=retain,
        )
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            raise RuntimeError(f"Error MQTT {result.rc} al publicar en {topic}.")
        result.wait_for_publish(timeout=10.0)

    def disconnect(self) -> None:
        if self._connected.is_set():
            try:
                self.publish_status("offline")
            except Exception as error:
                print(f"[MQTT] No se pudo publicar offline: {error}")
        self._client.disconnect()
        self._client.loop_stop()
