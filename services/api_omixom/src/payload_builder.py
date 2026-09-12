from datetime import datetime, timezone
from typing import Any

from .models import OmixomReading


def format_utc_timestamp(value: datetime) -> str:
    if value.tzinfo is None:
        # Los reportes de Omixom no traen zona horaria -- se asume hora local
        # Argentina (UTC-3) salvo que se confirme lo contrario con un reporte real.
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def build_measurement_payload(
    *,
    node_id: str,
    schema_version: str,
    reading: OmixomReading,
) -> dict[str, Any]:
    # source = identidad puntual, producer = categoría -- misma semántica que
    # services/api_smn (ver docs/PROGRESS.md de starlink-measurement-station).
    return {
        "node_id": node_id,
        "timestamp": format_utc_timestamp(reading.measured_at),
        "source": "api_omixom",
        "producer": "api",
        "schema_version": schema_version,
        "metrics": {
            "temperature_c": reading.temperature_c,
            "humidity_pct": reading.humidity_pct,
            "pressure_hpa": reading.pressure_hpa,
            "precipitation_mm": reading.precipitation_mm,
            "wind_speed_kmh": reading.wind_speed_kmh,
            "wind_direction_deg": reading.wind_direction_deg,
            "cloud_cover_pct": None,  # Omixom no suele reportar nubosidad
        },
    }


def build_status_payload(*, node_id: str, status: str) -> dict[str, Any]:
    return {
        "node_id": node_id,
        "source": "api_omixom",
        "status": status,
    }
