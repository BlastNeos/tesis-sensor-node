from datetime import datetime, timezone
from typing import Any
from .models import SensorReading

def format_utc_timestamp(value: datetime) -> str:
    if value.tzinfo is None:
        raise ValueError("El timestamp debe incluir zona horaria.")
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

def build_measurement_payload(
    *,
    node_id: str,
    sensor_uid: str,
    schema_version: str,
    measured_at: datetime,
    reading: SensorReading,
) -> dict[str, Any]:
    return {
        "node_id": node_id,
        "timestamp": format_utc_timestamp(measured_at),
        "source": "local_sensor",
        "producer": "mock_bme280",
        "schema_version": schema_version,
        "metrics": {
            "temperature_c": reading.temperature_c,
            "humidity_pct": reading.humidity_pct,
            "pressure_hpa": reading.pressure_hpa,
            "sensor_uid": sensor_uid,
        },
    }

def build_status_payload(*, node_id: str, status: str) -> dict[str, Any]:
    return {
        "node_id": node_id,
        "source": "mock_bme280",
        "status": status,
    }