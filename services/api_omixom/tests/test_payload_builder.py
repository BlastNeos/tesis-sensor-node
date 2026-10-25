from datetime import datetime, timezone

from src.models import OmixomReading
from src.payload_builder import build_measurement_payload, build_status_payload


def _reading(measured_at: datetime) -> OmixomReading:
    return OmixomReading(
        measured_at=measured_at,
        temperature_c=18.5,
        humidity_pct=62.0,
        pressure_hpa=1013.2,
        precipitation_mm=0.0,
        wind_speed_kmh=11.0,
        wind_direction_deg=270,
    )


def test_measurement_payload_uses_current_source_producer_contract() -> None:
    reading = _reading(
        datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)
    )

    payload = build_measurement_payload(
        node_id="lit-cordoba-01",
        schema_version="1.0",
        reading=reading,
    )

    assert payload["source"] == "real"
    assert payload["producer"] == "ohmc"
    assert payload["metrics"]["temperature_c"] == 18.5
    assert payload["metrics"]["cloud_cover_pct"] is None
    assert payload["timestamp"] == "2026-08-20T12:00:00Z"


def test_naive_report_timestamp_is_interpreted_as_argentina_time() -> None:
    reading = _reading(datetime(2026, 8, 20, 12, 0))

    payload = build_measurement_payload(
        node_id="lit-cordoba-01",
        schema_version="1.0",
        reading=reading,
    )

    assert payload["timestamp"] == "2026-08-20T15:00:00Z"


def test_status_payload_shape() -> None:
    payload = build_status_payload(
        node_id="lit-cordoba-01",
        status="online",
    )

    assert payload == {
        "node_id": "lit-cordoba-01",
        "source": "real",
        "producer": "ohmc",
        "status": "online",
    }
