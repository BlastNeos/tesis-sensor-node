from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class OmixomReading:
    """Forma común que producen tanto ohmc_client (Camino A, API real) como
    report_ingestor (Camino B, reportes .xlsx) -- payload_builder no necesita
    saber de cuál de los 2 vino."""

    measured_at: datetime
    temperature_c: float | None
    humidity_pct: float | None
    pressure_hpa: float | None
    precipitation_mm: float | None
    wind_speed_kmh: float | None
    wind_direction_deg: int | None
