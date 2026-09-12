"""Entrypoint principal -- Camino A (API real del OHMC, `python -m src.main`).

Para el flujo viejo de reportes .xlsx (Camino B, fallback), ver
`src/main_reports.py` -- queda aparte para no mezclar los 2 loops en un mismo
proceso; son 2 formas de alimentar el mismo tópico, no 2 mitades de una cosa.
"""

import signal
import sys
from threading import Event

from .config import load_settings
from .mqtt_publisher import MqttPublisher
from .ohmc_client import OhmcClient, OhmcClientError
from .payload_builder import build_measurement_payload

stop_event = Event()


def _request_stop(signum: int, frame: object) -> None:
    del frame
    print(f"\n[APP] Señal {signum} recibida. Finalizando...")
    stop_event.set()


def run() -> int:
    settings = load_settings()
    if not settings.ohmc_email or not settings.ohmc_password:
        print(
            "[ERROR] Faltan OHMC_EMAIL/OHMC_PASSWORD en el .env -- ver README.md, "
            "sección 'Cómo conseguir las credenciales'.",
            file=sys.stderr,
        )
        return 1

    print("=== Integrador de clima externo — OHMC (API real, Camino A) ===")
    print(f"[CONFIG] Broker: {settings.mqtt_host}:{settings.mqtt_port}")
    print(f"[CONFIG] Tópico: {settings.measurement_topic}")
    print(f"[CONFIG] Estación OHMC: station_id={settings.ohmc_station_id} (Lab. Hidráulica-UNC)")
    print(f"[CONFIG] Intervalo de poll: {settings.poll_interval_seconds}s (RF-11: 900s=15min por defecto)")

    client = OhmcClient(settings)
    publisher = MqttPublisher(settings)
    publisher.connect()

    try:
        while not stop_event.is_set():
            try:
                reading = client.fetch_latest_reading()
                payload = build_measurement_payload(
                    node_id=settings.node_id,
                    schema_version=settings.schema_version,
                    reading=reading,
                )
                publisher.publish_measurement(payload)
                print(f"[OHMC] Publicado ({reading.measured_at.isoformat()}) → {settings.measurement_topic}")
            except OhmcClientError as error:
                # Nunca tumbar el contenedor por una falla del OHMC (login
                # vencido, timeout, mantenimiento) -- se salta este ciclo.
                print(f"[ERROR] Falló la consulta al OHMC, se salta este ciclo: {error}", file=sys.stderr)
            except (ConnectionError, TimeoutError, RuntimeError) as error:
                print(f"[ERROR] Falló la publicación MQTT, se salta este ciclo: {error}", file=sys.stderr)

            stop_event.wait(settings.poll_interval_seconds)
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
