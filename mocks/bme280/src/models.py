from dataclasses import dataclass

@dataclass(frozen=True)
class SensorReading:
    temperature_c: float
    humidity_pct: float
    pressure_hpa: float
