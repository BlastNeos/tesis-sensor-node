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
uint32_t lastSensorRetryAtMs = 0;

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("\n=== Nodo ambiental ESP32 + BME280 ===");

  randomSeed(esp_random());

  sensorReady = sensor.begin();
  lastSensorRetryAtMs = millis();
  wifiService.begin();

  // El LWT permite que el broker marque el nodo ambiental como offline
  // si el ESP32 desaparece sin desconectarse correctamente.
  const String lastWill = PayloadBuilder::buildStatus("offline");
  mqttService.begin(lastWill);

  // Permite intentar la primera medición inmediatamente.
  lastSampleAtMs = millis() - AppConfig::SAMPLE_INTERVAL_MS;
}

void loop() {
  wifiService.loop();
  timeService.loop(wifiService.connected());
  mqttService.loop(wifiService.connected());

  // Si el sensor no está disponible, se intenta reinicializar cada 10 segundos
  // sin bloquear el resto del programa.
  if (!sensorReady &&
      millis() - lastSensorRetryAtMs >= AppConfig::SENSOR_RETRY_INTERVAL_MS) {
    lastSensorRetryAtMs = millis();

    Serial.println("[APP] Reintentando inicialización del BME280...");
    sensorReady = sensor.begin();

    if (sensorReady) {
      Serial.println("[APP] BME280 recuperado.");

      // Permite tomar una medición inmediatamente después de recuperarlo.
      lastSampleAtMs = millis() - AppConfig::SAMPLE_INTERVAL_MS;
    }
  }

  if (millis() - lastSampleAtMs >= AppConfig::SAMPLE_INTERVAL_MS) {
    lastSampleAtMs = millis();

    if (!sensorReady) {
      Serial.println("[APP] Sensor no inicializado; se omite la medición.");
    } else if (!timeService.synchronized()) {
      Serial.println("[APP] Hora UTC todavía no sincronizada; se omite la publicación.");
    } else {
      const SensorReading reading = sensor.read();

      if (!reading.valid) {
        Serial.println(
            "[APP] Lectura BME280 inválida o NaN; se intentará reinicializar.");

        sensorReady = false;
        lastSensorRetryAtMs = millis();
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
