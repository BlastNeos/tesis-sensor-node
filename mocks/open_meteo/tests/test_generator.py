from datetime import datetime, timezone

from src.generator import OpenMeteoGenerator


def test_generated_values_are_in_expected_ranges() -> None:
    generator = OpenMeteoGenerator(seed=84, missing_field_probability=0.0)
    reading = generator.generate(datetime(2026, 8, 5, 12, 0, tzinfo=timezone.utc))

    assert reading.temperature_c is not None
    assert reading.humidity_pct is not None
    assert reading.pressure_hpa is not None
    assert reading.precipitation_mm is not None
    assert reading.wind_speed_kmh is not None
    assert reading.wind_direction_deg is not None
    assert reading.cloud_cover_pct is not None

    assert -50.0 < reading.temperature_c < 80.0
    assert 0.0 <= reading.humidity_pct <= 100.0
    assert 800.0 < reading.pressure_hpa < 1100.0
    assert reading.precipitation_mm >= 0.0
    assert reading.wind_speed_kmh >= 0.0
    assert 0 <= reading.wind_direction_deg <= 359
    assert 0.0 <= reading.cloud_cover_pct <= 100.0


def test_missing_fields_can_be_simulated_as_null() -> None:
    generator = OpenMeteoGenerator(seed=84, missing_field_probability=1.0)
    reading = generator.generate(datetime(2026, 8, 5, 12, 0, tzinfo=timezone.utc))

    assert reading.temperature_c is None
    assert reading.humidity_pct is None
    assert reading.pressure_hpa is None
    assert reading.precipitation_mm is None
    assert reading.wind_speed_kmh is None
    assert reading.wind_direction_deg is None
    assert reading.cloud_cover_pct is None
