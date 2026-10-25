from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import DateTime, Engine, Float, Integer, String, create_engine
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


class Base(DeclarativeBase):
    pass


class EnvMetric(Base):
    """Mapeo ORM de la hypertable `env_metrics`.

    La tabla es creada por infrastructure/meteo-db/init_meteo_data.sql.
    SQLAlchemy solamente la mapea para persistir datos; no crea el esquema.
    """

    __tablename__ = "env_metrics"

    time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        primary_key=True,
    )
    node_id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
    )
    source: Mapped[str] = mapped_column(
        String(16),
        primary_key=True,
    )
    producer: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
    )

    temperature_c: Mapped[Optional[float]] = mapped_column(Float)
    humidity_pct: Mapped[Optional[float]] = mapped_column(Float)
    pressure_hpa: Mapped[Optional[float]] = mapped_column(Float)
    precipitation_mm: Mapped[Optional[float]] = mapped_column(Float)
    wind_speed_kmh: Mapped[Optional[float]] = mapped_column(Float)
    wind_direction_deg: Mapped[Optional[int]] = mapped_column(Integer)
    cloud_cover_pct: Mapped[Optional[float]] = mapped_column(Float)

    sensor_id: Mapped[Optional[int]] = mapped_column(Integer)
    schema_version: Mapped[str] = mapped_column(String(16))


class MeteoDB:
    """Gateway de persistencia de mediciones meteorológicas."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    @classmethod
    def from_env(cls) -> "MeteoDB":
        host = os.environ.get("METEO_DB_HOST", "localhost")
        port = os.environ.get("METEO_DB_PORT", "5432")
        name = os.environ.get("METEO_DB_NAME", "meteo_data")
        user = os.environ.get("METEO_DB_USER", "meteo_app")
        password = os.environ.get("METEO_DB_PASSWORD", "")

        dsn = (
            f"postgresql+psycopg2://"
            f"{user}:{password}@{host}:{port}/{name}"
        )

        return cls(
            create_engine(
                dsn,
                pool_pre_ping=True,
            )
        )

    def insert(self, row: dict[str, Any]) -> None:
        """Inserta una medición en env_metrics.

        MQTT QoS 1 puede reentregar un mismo mensaje. La PK
        (time, node_id, source, producer) permite reconocerlo y
        ON CONFLICT DO NOTHING evita duplicar la medición.
        """

        stmt = (
            pg_insert(EnvMetric)
            .values(**row)
            .on_conflict_do_nothing(
                index_elements=[
                    "time",
                    "node_id",
                    "source",
                    "producer",
                ]
            )
        )

        with Session(self._engine) as session:
            session.execute(stmt)
            session.commit()

    def dispose(self) -> None:
        self._engine.dispose()
