import math
import random
from datetime import datetime
from .models import SensorReading

def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(value, maximum))

class Bme280Generator:
    def __init__(
        self,
        seed: int,
        base_temperature_c: float,
        base_humidity_pct: float,
        base_pressure_hpa: float,
    ) -> None:
        self._random = random.Random(seed)
        self._base_temperature_c = base_temperature_c
        self._base_humidity_pct = base_humidity_pct
        self._base_pressure_hpa = base_pressure_hpa
        self._pressure_drift = 0.0

    def generate(self, simulated_at: datetime) -> SensorReading:
        seconds = simulated_at.hour * 3600 + simulated_at.minute * 60 + simulated_at.second
        phase = 2.0 * math.pi * seconds / 86400.0

        temperature = (
            self._base_temperature_c
            + 4.0 * math.sin(phase - math.pi / 2.0)
            + self._random.gauss(0.0, 0.15)
        )
        humidity = _clamp(
            self._base_humidity_pct
            - 10.0 * math.sin(phase - math.pi / 2.0)
            + self._random.gauss(0.0, 0.5),
            0.0,
            100.0,
        )
        self._pressure_drift = _clamp(
            self._pressure_drift + self._random.gauss(0.0, 0.03),
            -3.0,
            3.0,
        )
        pressure = (
            self._base_pressure_hpa
            + 1.2 * math.sin(phase / 2.0)
            + self._pressure_drift
        )

        return SensorReading(
            temperature_c=round(temperature, 2),
            humidity_pct=round(humidity, 2),
            pressure_hpa=round(pressure, 2),
        )
