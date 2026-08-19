from datetime import datetime, timezone
import pytest
from src.models import SensorReading
from src.payload_builder import (
    build_measurement_payload,
    build_status_payload,
    format_utc_timestamp,
)

def test_payload_uses_envelope_and_nested_metrics() -> None:
    payload = build_measurement_payload(
        node_id="lit-cordoba-01",
        sensor_uid="bme280-mock-01",
        schema_version="1.0",
        measured_at=datetime(2026, 8, 5, 15, 0, tzinfo=timezone.utc),
        reading=SensorReading(22.5, 60.0, 1012.0),
    )
    assert payload["node_id"] == "lit-cordoba-01"
    assert payload["producer"] == "mock_bme280"
    assert payload["timestamp"] == "2026-08-05T15:00:00Z"
    assert payload["metrics"]["temperature_c"] == 22.5
    assert payload["metrics"]["sensor_uid"] == "bme280-mock-01"

def test_timestamp_must_include_timezone() -> None:
    with pytest.raises(ValueError):
        format_utc_timestamp(datetime(2026, 8, 5, 15, 0))

def test_status_payload_uses_documented_source() -> None:
    payload = build_status_payload(
        node_id="lit-cordoba-01",
        status="online",
    )

    assert payload == {
        "node_id": "lit-cordoba-01",
        "source": "mock_bme280",
        "status": "online",
    }