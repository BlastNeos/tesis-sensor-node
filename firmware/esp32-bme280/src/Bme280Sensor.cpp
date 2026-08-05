#include "Bme280Sensor.h"

#include <Arduino.h>
#include <Wire.h>
#include <cmath>

#include "AppConfig.h"

bool Bme280Sensor::begin() {
  Wire.begin(AppConfig::I2C_SDA_PIN, AppConfig::I2C_SCL_PIN);

  if (bme_.begin(AppConfig::BME280_ADDRESS_PRIMARY, &Wire)) {
    activeAddress_ = AppConfig::BME280_ADDRESS_PRIMARY;
  } else if (bme_.begin(AppConfig::BME280_ADDRESS_SECONDARY, &Wire)) {
    activeAddress_ = AppConfig::BME280_ADDRESS_SECONDARY;
  } else {
    Serial.println("[BME280] No se encontró el sensor en 0x76 ni 0x77.");
    return false;
  }

  Serial.printf("[BME280] Sensor detectado en 0x%02X.\n", activeAddress_);
  return true;
}

SensorReading Bme280Sensor::read() {
  SensorReading reading;
  reading.temperatureC = bme_.readTemperature();
  reading.humidityPct = bme_.readHumidity();
  reading.pressureHpa = bme_.readPressure() / 100.0F;  // Pa -> hPa

  // NaN significa "Not a Number": la biblioteca no obtuvo un número válido.
  const bool hasNaN = std::isnan(reading.temperatureC) ||
                      std::isnan(reading.humidityPct) ||
                      std::isnan(reading.pressureHpa);

  const bool humidityValid =
      reading.humidityPct >= 0.0F && reading.humidityPct <= 100.0F;
  const bool pressureValid = reading.pressureHpa > 0.0F;

  reading.valid = !hasNaN && humidityValid && pressureValid;
  return reading;
}
