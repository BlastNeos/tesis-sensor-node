from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EnvMetrics(BaseModel):
    """Métricas admitidas por el dominio meteorológico."""

    model_config = ConfigDict(extra="forbid")

    temperature_c: float | None = Field(default=None, gt=-50, lt=80)
    humidity_pct: float | None = Field(default=None, ge=0, le=100)
    pressure_hpa: float | None = Field(default=None, gt=800, lt=1100)

    precipitation_mm: float | None = Field(default=None, ge=0)
    wind_speed_kmh: float | None = Field(default=None, ge=0)
    wind_direction_deg: int | None = Field(default=None, ge=0, lt=360)
    cloud_cover_pct: float | None = Field(default=None, ge=0, le=100)

    # BME280 real/mock identifica el sensor físico/lógico con este campo.
    # La resolución sensor_uid -> sensor_id para la DB se hará posteriormente.
    sensor_uid: str | None = Field(default=None, min_length=1, max_length=64)


class EnvPayloadIn(BaseModel):
    """Envelope común de entrada para mediciones meteorológicas MQTT."""

    model_config = ConfigDict(extra="forbid")

    node_id: str = Field(min_length=1, max_length=64)
    timestamp: datetime

    source: Literal["real", "mock"]
    producer: str = Field(min_length=1, max_length=64)

    schema_version: str = Field(min_length=1, max_length=16)
    metrics: EnvMetrics

    @field_validator("timestamp")
    @classmethod
    def timestamp_must_include_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp debe incluir zona horaria")

        return value.astimezone(timezone.utc)
