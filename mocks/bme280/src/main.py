import json
import random
import signal
import sys
from datetime import datetime, timedelta, timezone
from threading import Event
from .config import load_settings
from .generator import Bme280Generator
from .mqtt_publisher import MqttPublisher
from .payload_builder import build_measurement_payload

stop_event = Event()

def _request_stop(signum: int, frame: object) -> None:
    del frame
    print(f"\n[APP] Señal {signum} recibida. Finalizando...")
    stop_event.set()

def run() -> int:
    settings = load_settings()
    print("=== Mock BME280 ===")
    print(f"[CONFIG] Broker: {settings.mqtt_host}:{settings.mqtt_port}")
    print(f"[CONFIG] Tópico: {settings.measurement_topic}")
    print(f"[CONFIG] Intervalo simulado: {settings.publish_interval_seconds}s")
    print(f"[CONFIG] TIME_WARP_FACTOR: {settings.time_warp_factor}")
    print(f"[CONFIG] Espera real: {settings.real_wait_seconds:.3f}s")

    generator = Bme280Generator(
        settings.random_seed,
        settings.base_temperature_c,
        settings.base_humidity_pct,
        settings.base_pressure_hpa,
    )
    chaos_random = random.Random(settings.random_seed + 1)
    publisher = MqttPublisher(settings)
    simulated_at = datetime.now(timezone.utc)
    publisher.connect()

    try:
        while not stop_event.is_set():
            drop = (
                settings.chaos_enabled
                and chaos_random.random() < settings.drop_probability
            )
            if drop:
                print(f"[CHAOS] Medición omitida en {simulated_at.isoformat()}.")
            else:
                reading = generator.generate(simulated_at)
                payload = build_measurement_payload(
                    node_id=settings.node_id,
                    sensor_uid=settings.sensor_uid,
                    schema_version=settings.schema_version,
                    measured_at=simulated_at,
                    reading=reading,
                )
                publisher.publish_measurement(payload)
                print(
                    f"[MQTT] Publicado en {settings.measurement_topic}: "
                    f"{json.dumps(payload, ensure_ascii=False)}"
                )

            simulated_at += timedelta(seconds=settings.publish_interval_seconds)
            stop_event.wait(settings.real_wait_seconds)
    finally:
        publisher.disconnect()

    return 0

def main() -> None:
    signal.signal(signal.SIGINT, _request_stop)
    signal.signal(signal.SIGTERM, _request_stop)
    try:
        code = run()
    except (ValueError, OSError, ConnectionError, TimeoutError) as error:
        print(f"[ERROR] {error}", file=sys.stderr)
        code = 1
    raise SystemExit(code)

if __name__ == "__main__":
    main()
