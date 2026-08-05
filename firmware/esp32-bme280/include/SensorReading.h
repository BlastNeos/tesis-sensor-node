#pragma once

struct SensorReading {
  float temperatureC = 0.0F;
  float humidityPct = 0.0F;
  float pressureHpa = 0.0F;
  bool valid = false;
};
