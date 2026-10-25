from datetime import timezone

import pytest
from pydantic import ValidationError

from src.models import EnvPayloadIn


def test_accepts_real_bme280_payload() -> None:
    payload = EnvPayloadIn.model_validate(
        {
            "node_id": "lit-cordoba-01",
            "timestamp": "2026-10-25T06:00:00Z",
            "source": "real",
            "producer": "bme280",
            "schema_version": "1.0",
            "metrics": {
                "temperature_c": 22.4,
                "humidity_pct": 54.2,
                "pressure_hpa": 971.3,
                "sensor_uid": "bme280-01",
            },
        }
    )

    assert payload.source == "real"
    assert payload.producer == "bme280"
    assert payload.metrics.sensor_uid == "bme280-01"
    assert payload.timestamp.tzinfo == timezone.utc


def test_accepts_mock_open_meteo_payload() -> None:
    payload = EnvPayloadIn.model_validate(
        {
            "node_id": "lit-cordoba-01",
            "timestamp": "2026-10-25T06:00:00Z",
            "source": "mock",
            "producer": "open_meteo",
            "schema_version": "1.0",
            "metrics": {
                "temperature_c": 21.8,
                "humidity_pct": 58.1,
                "pressure_hpa": 973.0,
                "precipitation_mm": 0.0,
                "wind_speed_kmh": 12.5,
                "wind_direction_deg": 225,
                "cloud_cover_pct": 40.0,
            },
        }
    )

    assert payload.source == "mock"
    assert payload.producer == "open_meteo"
    assert payload.metrics.wind_direction_deg == 225


def test_accepts_real_ohmc_payload() -> None:
    payload = EnvPayloadIn.model_validate(
        {
            "node_id": "lit-cordoba-01",
            "timestamp": "2026-10-25T06:00:00Z",
            "source": "real",
            "producer": "ohmc",
            "schema_version": "1.0",
            "metrics": {
                "temperature_c": 18.5,
                "humidity_pct": 62.0,
                "pressure_hpa": 1013.2,
                "precipitation_mm": 0.0,
                "wind_speed_kmh": 11.0,
                "wind_direction_deg": 270,
                "cloud_cover_pct": None,
            },
        }
    )

    assert payload.source == "real"
    assert payload.producer == "ohmc"


def test_rejects_old_source_semantics() -> None:
    with pytest.raises(ValidationError):
        EnvPayloadIn.model_validate(
            {
                "node_id": "lit-cordoba-01",
                "timestamp": "2026-10-25T06:00:00Z",
                "source": "api_omixom",
                "producer": "api",
                "schema_version": "1.0",
                "metrics": {},
            }
        )


def test_rejects_wind_direction_out_of_range() -> None:
    with pytest.raises(ValidationError):
        EnvPayloadIn.model_validate(
            {
                "node_id": "lit-cordoba-01",
                "timestamp": "2026-10-25T06:00:00Z",
                "source": "real",
                "producer": "ohmc",
                "schema_version": "1.0",
                "metrics": {
                    "wind_direction_deg": 360,
                },
            }
        )


def test_rejects_naive_timestamp() -> None:
    with pytest.raises(ValidationError):
        EnvPayloadIn.model_validate(
            {
                "node_id": "lit-cordoba-01",
                "timestamp": "2026-10-25T06:00:00",
                "source": "real",
                "producer": "bme280",
                "schema_version": "1.0",
                "metrics": {
                    "temperature_c": 22.4,
                },
            }
        )


def test_normalizes_timestamp_to_utc() -> None:
    payload = EnvPayloadIn.model_validate(
        {
            "node_id": "lit-cordoba-01",
            "timestamp": "2026-10-25T03:00:00-03:00",
            "source": "real",
            "producer": "ohmc",
            "schema_version": "1.0",
            "metrics": {
                "temperature_c": 18.5,
            },
        }
    )

    assert payload.timestamp.isoformat() == "2026-10-25T06:00:00+00:00"
