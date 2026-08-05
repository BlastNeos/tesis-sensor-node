#pragma once

#include <Adafruit_BME280.h>
#include "SensorReading.h"

class Bme280Sensor {
 public:
  bool begin();
  SensorReading read();

 private:
  Adafruit_BME280 bme_;
  uint8_t activeAddress_ = 0;
};
