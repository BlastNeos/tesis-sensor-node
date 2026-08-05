#include "PayloadBuilder.h"

#include <ArduinoJson.h>

#include "AppConfig.h"

namespace PayloadBuilder {

String buildMeasurement(const SensorReading& reading,
                        const String& timestampIso8601) {
  JsonDocument doc;

  // Este contrato es provisional hasta que el equipo congele ADR-01.
  // Al estar aislado en este archivo, cambiarlo no afecta al sensor ni a MQTT.
  doc["node_id"] = AppConfig::NODE_ID;
  doc["timestamp"] = timestampIso8601;
  doc["source"] = "local_sensor";
  doc["producer"] = "esp32_bme280";
  doc["schema_version"] = "1.0";

  JsonObject metrics = doc["metrics"].to<JsonObject>();
  metrics["temperature_c"] = reading.temperatureC;
  metrics["humidity_pct"] = reading.humidityPct;
  metrics["pressure_hpa"] = reading.pressureHpa;
  metrics["sensor_uid"] = AppConfig::SENSOR_UID;

  String payload;
  serializeJson(doc, payload);
  return payload;
}

String buildStatus(const char* status, const String& timestampIso8601) {
  JsonDocument doc;
  doc["node_id"] = AppConfig::NODE_ID;
  doc["component"] = "sensor_gateway";
  doc["status"] = status;
  doc["schema_version"] = "1.0";

  if (timestampIso8601.isEmpty()) {
    doc["timestamp"] = nullptr;
  } else {
    doc["timestamp"] = timestampIso8601;
  }

  String payload;
  serializeJson(doc, payload);
  return payload;
}

}  // namespace PayloadBuilder
