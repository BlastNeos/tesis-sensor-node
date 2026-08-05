#include <Arduino.h>

#include "AppConfig.h"
#include "Bme280Sensor.h"
#include "MqttService.h"
#include "PayloadBuilder.h"
#include "TimeService.h"
#include "WifiService.h"

Bme280Sensor sensor;
WifiService wifiService;
TimeService timeService;
MqttService mqttService;

bool sensorReady = false;
uint32_t lastSampleAtMs = 0;

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("\n=== Nodo ambiental ESP32 + BME280 ===");

  randomSeed(esp_random());

  sensorReady = sensor.begin();
  wifiService.begin();

  // El LWT se registra al conectarse. Su timestamp queda en null porque el ESP32
  // no puede saber por anticipado el instante exacto de una caída abrupta.
  const String lastWill = PayloadBuilder::buildStatus("offline", "");
  mqttService.begin(lastWill);

  // Permite intentar la primera medición inmediatamente.
  lastSampleAtMs = millis() - AppConfig::SAMPLE_INTERVAL_MS;
}

void loop() {
  wifiService.loop();
  timeService.loop(wifiService.connected());
  mqttService.loop(wifiService.connected(), timeService.nowIso8601());

  if (millis() - lastSampleAtMs >= AppConfig::SAMPLE_INTERVAL_MS) {
    lastSampleAtMs = millis();

    if (!sensorReady) {
      Serial.println("[APP] Sensor no inicializado; se omite la medición.");
    } else if (!timeService.synchronized()) {
      Serial.println("[APP] Hora UTC todavía no sincronizada; se omite la publicación.");
    } else {
      const SensorReading reading = sensor.read();

      if (!reading.valid) {
        Serial.println("[APP] Lectura BME280 inválida o NaN; no se publica.");
      } else {
        const String timestamp = timeService.nowIso8601();
        const String payload =
            PayloadBuilder::buildMeasurement(reading, timestamp);
        mqttService.publishMeasurement(payload);
      }
    }
  }

  // No bloquea el programa durante segundos; sólo cede brevemente CPU.
  delay(5);
}
