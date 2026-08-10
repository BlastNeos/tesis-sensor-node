from datetime import datetime, timezone
from src.generator import Bme280Generator

def _generator(seed: int = 42) -> Bme280Generator:
    return Bme280Generator(seed, 22.0, 60.0, 1012.0)

def test_generated_values_are_in_physical_ranges() -> None:
    reading = _generator().generate(datetime(2026, 8, 5, 12, 0, tzinfo=timezone.utc))
    assert -40.0 <= reading.temperature_c <= 85.0
    assert 0.0 <= reading.humidity_pct <= 100.0
    assert 800.0 <= reading.pressure_hpa <= 1200.0

def test_same_seed_produces_same_first_reading() -> None:
    timestamp = datetime(2026, 8, 5, 12, 0, tzinfo=timezone.utc)
    assert _generator(7).generate(timestamp) == _generator(7).generate(timestamp)
