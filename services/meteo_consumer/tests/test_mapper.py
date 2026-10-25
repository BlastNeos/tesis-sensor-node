from datetime import timezone

from src.mapper import meteo_row
from src.models import EnvPayloadIn


def test_maps_bme280_payload_to_env_metrics_row() -> None:
    payload = EnvPayloadIn.model_validate(
        {
            "node_id": "lit-cordoba-01",
            "timestamp": "2026-10-25T03:00:00-03:00",
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

    row = meteo_row(payload)

    assert row["node_id"] == "lit-cordoba-01"
    assert row["source"] == "real"
    assert row["producer"] == "bme280"

    assert row["temperature_c"] == 22.4
    assert row["humidity_pct"] == 54.2
    assert row["pressure_hpa"] == 971.3

    assert row["precipitation_mm"] is None
    assert row["wind_speed_kmh"] is None
    assert row["wind_direction_deg"] is None
    assert row["cloud_cover_pct"] is None

    assert row["sensor_id"] is None
    assert row["schema_version"] == "1.0"

    assert row["time"].tzinfo == timezone.utc
    assert row["time"].isoformat() == "2026-10-25T06:00:00+00:00"

    # sensor_uid pertenece al payload, pero todavía no es una columna de
    # env_metrics.
    assert "sensor_uid" not in row


def test_maps_ohmc_payload_to_env_metrics_row() -> None:
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

    row = meteo_row(payload)

    assert row["producer"] == "ohmc"
    assert row["precipitation_mm"] == 0.0
    assert row["wind_speed_kmh"] == 11.0
    assert row["wind_direction_deg"] == 270
    assert row["cloud_cover_pct"] is None


def test_mapper_returns_exact_env_metrics_columns() -> None:
    payload = EnvPayloadIn.model_validate(
        {
            "node_id": "lit-cordoba-01",
            "timestamp": "2026-10-25T06:00:00Z",
            "source": "mock",
            "producer": "open_meteo",
            "schema_version": "1.0",
            "metrics": {},
        }
    )

    row = meteo_row(payload)

    assert set(row) == {
        "time",
        "node_id",
        "source",
        "producer",
        "temperature_c",
        "humidity_pct",
        "pressure_hpa",
        "precipitation_mm",
        "wind_speed_kmh",
        "wind_direction_deg",
        "cloud_cover_pct",
        "sensor_id",
        "schema_version",
    }
