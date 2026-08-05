#include "MqttService.h"

#include <cstring>

#include "AppConfig.h"
#include "PayloadBuilder.h"
#include "Secrets.h"

void MqttService::begin(const String& lastWillPayload) {
  sensorTopic_ = String(AppConfig::SENSOR_TOPIC_PREFIX) + AppConfig::NODE_ID;
  statusTopic_ = String(AppConfig::STATUS_TOPIC_PREFIX) + AppConfig::NODE_ID;

  mqttClient_.begin(AppConfig::MQTT_HOST, AppConfig::MQTT_PORT, networkClient_);
  mqttClient_.setOptions(30, false, 2'000);  // keepalive, sesión persistente, timeout

  // El broker publicará este mensaje si el ESP32 desaparece sin desconectarse bien.
  mqttClient_.setWill(statusTopic_.c_str(), lastWillPayload.c_str(), true, 1);

  resetBackoff();
}

void MqttService::loop(bool networkAvailable,
                       const String& timestampIso8601) {
  mqttClient_.loop();

  if (!networkAvailable) {
    return;
  }

  if (!mqttClient_.connected()) {
    if (millis() >= nextAttemptAtMs_) {
      attemptConnection(timestampIso8601);
    }
    return;
  }

  resetBackoff();

  if (millis() - lastHeartbeatAtMs_ >= AppConfig::HEARTBEAT_INTERVAL_MS) {
    publishStatus("online", timestampIso8601);
    lastHeartbeatAtMs_ = millis();
  }
}

bool MqttService::connected() const {
  return mqttClient_.connected();
}

bool MqttService::publishMeasurement(const String& payload) {
  if (!connected()) {
    Serial.println("[MQTT] No se publicó: el cliente no está conectado.");
    return false;
  }

  // retained=false: una medición histórica no debe quedar como estado permanente.
  // qos=1: el broker confirma la recepción al publicador.
  const bool published =
      mqttClient_.publish(sensorTopic_, payload, false, 1);

  if (published) {
    Serial.printf("[MQTT] Publicado en %s: %s\n", sensorTopic_.c_str(),
                  payload.c_str());
  } else {
    Serial.printf("[MQTT] Falló la publicación. Error=%d\n",
                  static_cast<int>(mqttClient_.lastError()));
  }

  return published;
}

void MqttService::attemptConnection(const String& timestampIso8601) {
  Serial.printf("[MQTT] Conectando a %s:%u...\n", AppConfig::MQTT_HOST,
                AppConfig::MQTT_PORT);

  bool connectedNow = false;
  if (std::strlen(Secrets::MQTT_USERNAME) == 0) {
    connectedNow = mqttClient_.connect(AppConfig::MQTT_CLIENT_ID);
  } else {
    connectedNow = mqttClient_.connect(AppConfig::MQTT_CLIENT_ID,
                                       Secrets::MQTT_USERNAME,
                                       Secrets::MQTT_PASSWORD);
  }

  if (connectedNow) {
    Serial.println("[MQTT] Conectado al broker Mosquitto.");
    resetBackoff();
    publishStatus("online", timestampIso8601);
    lastHeartbeatAtMs_ = millis();
  } else {
    Serial.printf("[MQTT] Conexión fallida. Error=%d, retorno=%d\n",
                  static_cast<int>(mqttClient_.lastError()),
                  static_cast<int>(mqttClient_.returnCode()));
    scheduleNextAttempt();
  }
}

void MqttService::publishStatus(const char* status,
                                const String& timestampIso8601) {
  const String payload = PayloadBuilder::buildStatus(status, timestampIso8601);

  // retained=true: un nuevo suscriptor puede conocer inmediatamente el último estado.
  mqttClient_.publish(statusTopic_, payload, true, 1);
}

void MqttService::scheduleNextAttempt() {
  const uint32_t jitterMs = static_cast<uint32_t>(random(0, 500));
  nextAttemptAtMs_ = millis() + backoffMs_ + jitterMs;
  backoffMs_ = min(backoffMs_ * 2, AppConfig::BACKOFF_MAX_MS);
}

void MqttService::resetBackoff() {
  backoffMs_ = AppConfig::BACKOFF_INITIAL_MS;
  nextAttemptAtMs_ = millis();
}
