"""Entrypoint alternativo -- Camino B (reportes .xlsx, `python -m src.main_reports`).

Fallback/histórico desde que se confirmó el Camino A (API real del OHMC, ver
`main.py`) el 12/9/2026. Se mantiene por si algún día hace falta backfillear
un rango de fechas que la API no tenga (`/mediciones/ultimas` solo da el
último valor, no historia -- para eso la API sí tiene `/mediciones` y
`/mediciones/agregaciones`, sin cliente propio todavía porque no hizo falta).
"""

import signal
import sys
from threading import Event

from .config import load_settings
from .mqtt_publisher import MqttPublisher
from .payload_builder import build_measurement_payload
from .report_ingestor import ReportParseError, find_pending_reports, move_report, parse_report

stop_event = Event()


def _request_stop(signum: int, frame: object) -> None:
    del frame
    print(f"\n[APP] Señal {signum} recibida. Finalizando...")
    stop_event.set()


def _process_one_report(path, settings, publisher) -> None:
    try:
        readings = parse_report(path)
    except ReportParseError as error:
        print(f"[ERROR] {error} -- se mueve a failed/ para no reintentarlo en loop.", file=sys.stderr)
        move_report(path, settings.failed_dir)
        return

    published = 0
    for reading in readings:
        payload = build_measurement_payload(
            node_id=settings.node_id,
            schema_version=settings.schema_version,
            reading=reading,
        )
        try:
            publisher.publish_measurement(payload)
            published += 1
        except (ConnectionError, TimeoutError, RuntimeError) as error:
            # No mover el archivo a processed/ si falló la publicación -- se
            # reintenta el archivo completo en el próximo scan, mejor duplicar
            # que perder mediciones.
            print(f"[ERROR] Falló publicar una lectura de {path.name}: {error}", file=sys.stderr)
            return

    print(f"[OMIXOM] {path.name}: {published}/{len(readings)} lecturas publicadas.")
    move_report(path, settings.processed_dir)


def run() -> int:
    settings = load_settings()
    print("=== Integrador de clima externo — Omixom (Camino B, reportes .xlsx) ===")
    print(f"[CONFIG] Broker: {settings.mqtt_host}:{settings.mqtt_port}")
    print(f"[CONFIG] Tópico: {settings.measurement_topic}")
    print(f"[CONFIG] Carpeta observada: {settings.watch_dir}")
    print(f"[CONFIG] Intervalo de escaneo: {settings.scan_interval_seconds}s")

    publisher = MqttPublisher(settings)
    publisher.connect()

    try:
        while not stop_event.is_set():
            for path in find_pending_reports(settings.watch_dir):
                _process_one_report(path, settings, publisher)
            stop_event.wait(settings.scan_interval_seconds)
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
