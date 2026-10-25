from typing import Any

from .models import EnvPayloadIn


def meteo_row(payload: EnvPayloadIn) -> dict[str, Any]:
    """Convierte un payload meteorológico validado en una fila de env_metrics."""

    metrics = payload.metrics

    return {
        "time": payload.timestamp,
        "node_id": payload.node_id,
        "source": payload.source,
        "producer": payload.producer,
        "temperature_c": metrics.temperature_c,
        "humidity_pct": metrics.humidity_pct,
        "pressure_hpa": metrics.pressure_hpa,
        "precipitation_mm": metrics.precipitation_mm,
        "wind_speed_kmh": metrics.wind_speed_kmh,
        "wind_direction_deg": metrics.wind_direction_deg,
        "cloud_cover_pct": metrics.cloud_cover_pct,

        # Pendiente: resolver sensor_uid -> sensor_id mediante el catálogo
        # compartido. Hasta entonces env_metrics admite sensor_id NULL.
        "sensor_id": None,

        "schema_version": payload.schema_version,
    }
