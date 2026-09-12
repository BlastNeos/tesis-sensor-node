from datetime import datetime

from src.payload_builder import build_measurement_payload, build_status_payload
from src.models import OmixomReading


def test_measurement_payload_uses_correct_source_producer_semantics() -> None:
    reading = OmixomReading(
        measured_at=datetime(2026, 8, 20, 12, 0),
        temperature_c=18.5,
        humidity_pct=62.0,
        pressure_hpa=1013.2,
        precipitation_mm=0.0,
        wind_speed_kmh=11.0,
        wind_direction_deg=270,
    )
    payload = build_measurement_payload(node_id="lit-cordoba-01", schema_version="1.0", reading=reading)

    assert payload["source"] == "api_omixom"
    assert payload["producer"] == "api"
    assert payload["metrics"]["temperature_c"] == 18.5
    assert payload["metrics"]["cloud_cover_pct"] is None
    assert payload["timestamp"] == "2026-08-20T12:00:00Z"


def test_status_payload_shape() -> None:
    payload = build_status_payload(node_id="lit-cordoba-01", status="online")
    assert payload == {"node_id": "lit-cordoba-01", "source": "api_omixom", "status": "online"}
