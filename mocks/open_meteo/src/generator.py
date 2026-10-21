import math
import random
from datetime import datetime
from typing import TypeVar

from .models import ExternalWeatherReading

T = TypeVar("T")


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(value, maximum))


class OpenMeteoGenerator:
    def __init__(self, seed: int, missing_field_probability: float = 0.05) -> None:
        self._random = random.Random(seed)
        self._missing_field_probability = missing_field_probability

    def _maybe_missing(self, value: T) -> T | None:
        if self._random.random() < self._missing_field_probability:
            return None
        return value

    def generate(self, simulated_at: datetime) -> ExternalWeatherReading:
        seconds = simulated_at.hour * 3600 + simulated_at.minute * 60 + simulated_at.second
        phase = 2.0 * math.pi * seconds / 86400.0

        temperature = 21.0 + 5.0 * math.sin(phase - math.pi / 2.0)
        temperature += self._random.gauss(0.0, 0.4)

        humidity = _clamp(
            62.0 - 12.0 * math.sin(phase - math.pi / 2.0)
            + self._random.gauss(0.0, 1.0),
            0.0,
            100.0,
        )
        pressure = 1012.0 + self._random.gauss(0.0, 1.5)
        wind = _clamp(12.0 + self._random.gauss(0.0, 5.0), 0.0, 80.0)
        wind_direction = int((220.0 + 60.0 * math.sin(phase) + self._random.gauss(0.0, 15.0)) % 360)
        cloud = _clamp(45.0 + self._random.gauss(0.0, 25.0), 0.0, 100.0)

        if self._random.random() < 0.18:
            precipitation = round(max(0.1, self._random.expovariate(0.7)), 2)
            cloud = max(cloud, 70.0)
        else:
            precipitation = 0.0

        return ExternalWeatherReading(
            temperature_c=self._maybe_missing(round(temperature, 2)),
            humidity_pct=self._maybe_missing(round(humidity, 2)),
            pressure_hpa=self._maybe_missing(round(pressure, 2)),
            precipitation_mm=self._maybe_missing(precipitation),
            wind_speed_kmh=self._maybe_missing(round(wind, 2)),
            wind_direction_deg=self._maybe_missing(wind_direction),
            cloud_cover_pct=self._maybe_missing(round(cloud, 2)),
        )
