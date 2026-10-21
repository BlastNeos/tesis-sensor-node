from datetime import datetime, timezone

import pytest

from src.models import ExternalWeatherReading
from src.payload_builder import build_measurement_payload, format_utc_timestamp


def _reading() -> ExternalWeatherReading:
    return ExternalWeatherReading(
        temperature_c=20.5,
        humidity_pct=65.0,
        pressure_hpa=1011.2,
        precipitation_mm=0.4,
        wind_speed_kmh=15.2,
        wind_direction_deg=225,
        cloud_cover_pct=78.0,
    )


def test_payload_uses_external_topic_contract_metadata() -> None:
    payload = build_measurement_payload(
        node_id="lit-cordoba-01",
        schema_version="1.0",
        measured_at=datetime(2026, 8, 5, 15, 0, tzinfo=timezone.utc),
        reading=_reading(),
    )

    assert payload["node_id"] == "lit-cordoba-01"
    assert payload["source"] == "mock"
    assert payload["producer"] == "open_meteo"
    assert payload["timestamp"] == "2026-08-05T15:00:00Z"

    assert payload["metrics"]["precipitation_mm"] == 0.4
    assert payload["metrics"]["wind_speed_kmh"] == 15.2
    assert payload["metrics"]["wind_direction_deg"] == 225
    assert payload["metrics"]["cloud_cover_pct"] == 78.0


def test_payload_preserves_null_fields() -> None:
    reading = ExternalWeatherReading(
        temperature_c=None,
        humidity_pct=65.0,
        pressure_hpa=None,
        precipitation_mm=0.0,
        wind_speed_kmh=10.0,
        wind_direction_deg=None,
        cloud_cover_pct=None,
    )

    payload = build_measurement_payload(
        node_id="lit-cordoba-01",
        schema_version="1.0",
        measured_at=datetime(2026, 8, 5, 15, 0, tzinfo=timezone.utc),
        reading=reading,
    )

    assert payload["metrics"]["temperature_c"] is None
    assert payload["metrics"]["pressure_hpa"] is None
    assert payload["metrics"]["wind_direction_deg"] is None
    assert payload["metrics"]["cloud_cover_pct"] is None


def test_timestamp_must_include_timezone() -> None:
    with pytest.raises(ValueError):
        format_utc_timestamp(datetime(2026, 8, 5, 15, 0))
