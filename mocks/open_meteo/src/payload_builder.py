from datetime import datetime, timezone
from typing import Any

from .models import ExternalWeatherReading


def format_utc_timestamp(value: datetime) -> str:
    if value.tzinfo is None:
        raise ValueError("El timestamp debe incluir zona horaria.")
    return (
        value.astimezone(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def build_measurement_payload(
    *,
    node_id: str,
    schema_version: str,
    measured_at: datetime,
    reading: ExternalWeatherReading,
) -> dict[str, Any]:
    return {
        "node_id": node_id,
        "timestamp": format_utc_timestamp(measured_at),
        "source": "mock",
        "producer": "open_meteo",
        "schema_version": schema_version,
        "metrics": {
            "temperature_c": reading.temperature_c,
            "humidity_pct": reading.humidity_pct,
            "pressure_hpa": reading.pressure_hpa,
            "precipitation_mm": reading.precipitation_mm,
            "wind_speed_kmh": reading.wind_speed_kmh,
            "wind_direction_deg": reading.wind_direction_deg,
            "cloud_cover_pct": reading.cloud_cover_pct,
        },
    }
